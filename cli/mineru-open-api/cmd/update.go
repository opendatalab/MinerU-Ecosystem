package cmd

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"strings"

	"github.com/opendatalab/MinerU-Ecosystem/cli/mineru-open-api/internal/output"
	"github.com/spf13/cobra"
)

const cdnBaseURL = "https://cdn-mineru.openxlab.org.cn/open-api-cli"

var updateCheck bool

var updateCmd = &cobra.Command{
	Use:   "update",
	Short: "Update the CLI to the latest version",
	Long:  `Check for a new version and update the binary in-place.`,
	Example: `  mineru-open-api update          # Update to latest
  mineru-open-api update --check  # Only check, don't update`,
	RunE: runUpdate,
}

func init() {
	rootCmd.AddCommand(updateCmd)
	updateCmd.Flags().BoolVar(&updateCheck, "check", false, "Only check for updates, don't install")
}

func runUpdate(cmd *cobra.Command, args []string) error {
	current := version

	// Fetch latest version
	output.Status("Checking for updates...")
	latest, err := fetchLatestVersion()
	if err != nil {
		return fmt.Errorf("failed to check for updates: %w", err)
	}

	if latest == current {
		output.Status("Already up to date (%s)", current)
		return nil
	}

	output.Status("New version available: %s → %s", current, latest)

	if updateCheck {
		return nil
	}

	// Determine binary name for this platform
	binary := fmt.Sprintf("mineru-open-api-cli-%s-%s", runtime.GOOS, runtime.GOARCH)
	if runtime.GOOS == "windows" {
		binary += ".exe"
	}

	downloadURL := fmt.Sprintf("%s/latest/%s", cdnBaseURL, binary)

	// Download to temp file
	output.Status("Downloading %s...", downloadURL)
	tmpFile, err := downloadToTemp(downloadURL)
	if err != nil {
		return fmt.Errorf("download failed: %w", err)
	}
	defer os.Remove(tmpFile)

	// Get current executable path
	execPath, err := os.Executable()
	if err != nil {
		return fmt.Errorf("cannot determine executable path: %w", err)
	}
	execPath, err = filepath.EvalSymlinks(execPath)
	if err != nil {
		return fmt.Errorf("cannot resolve executable path: %w", err)
	}

	// Replace the binary
	if err := replaceBinary(execPath, tmpFile); err != nil {
		return fmt.Errorf("failed to replace binary: %w", err)
	}

	output.Status("Updated successfully to %s", latest)
	return nil
}

func fetchLatestVersion() (string, error) {
	resp, err := http.Get(cdnBaseURL + "/VERSION")
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return "", fmt.Errorf("HTTP %d", resp.StatusCode)
	}
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(body)), nil
}

func downloadToTemp(url string) (string, error) {
	resp, err := http.Get(url)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return "", fmt.Errorf("HTTP %d", resp.StatusCode)
	}

	tmp, err := os.CreateTemp("", "mineru-update-*")
	if err != nil {
		return "", err
	}
	defer tmp.Close()

	if _, err := io.Copy(tmp, resp.Body); err != nil {
		os.Remove(tmp.Name())
		return "", err
	}
	return tmp.Name(), nil
}

// replaceBinary replaces the current binary with the downloaded one.
// On Windows, the running exe cannot be overwritten directly, so we
// rename it first, then move the new file in.
func replaceBinary(execPath, tmpPath string) error {
	if runtime.GOOS == "windows" {
		oldPath := execPath + ".old"
		os.Remove(oldPath) // clean up from previous update
		if err := os.Rename(execPath, oldPath); err != nil {
			return fmt.Errorf("rename current binary: %w", err)
		}
		if err := copyFile(tmpPath, execPath); err != nil {
			// Rollback
			os.Rename(oldPath, execPath)
			return fmt.Errorf("copy new binary: %w", err)
		}
		os.Remove(oldPath)
		return nil
	}

	// Unix: write new file, set executable, rename over old
	if err := os.Chmod(tmpPath, 0755); err != nil {
		return err
	}
	return os.Rename(tmpPath, execPath)
}

func copyFile(src, dst string) error {
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()

	out, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer out.Close()

	if _, err := io.Copy(out, in); err != nil {
		return err
	}
	return out.Close()
}
