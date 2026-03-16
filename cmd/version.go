package cmd

import (
	"fmt"
	"runtime"

	"github.com/spf13/cobra"
)

// Version info - set at build time via ldflags
var (
	version = "dev"
	commit  = "none"
	date    = "unknown"
)

// versionCmd represents the version command
var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Show version information",
	Long:  `Display the version, commit hash, and build date of the MinerU Open API CLI.`,
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Printf("mineru-open-api version %s\n", version)
		fmt.Printf("  commit: %s\n", commit)
		fmt.Printf("  built:  %s\n", date)
		fmt.Printf("  go:     %s\n", runtime.Version())
		fmt.Printf("  os:     %s/%s\n", runtime.GOOS, runtime.GOARCH)
	},
}

func init() {
	rootCmd.AddCommand(versionCmd)
}

// GetVersion returns the current version string.
func GetVersion() string {
	return version
}
