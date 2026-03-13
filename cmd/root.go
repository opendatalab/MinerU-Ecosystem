// Package cmd implements the CLI commands using cobra.
package cmd

import (
	"os"

	"github.com/OpenDataLab/mineru-open-cli/internal/output"
	"github.com/spf13/cobra"
)

// Global flags
var (
	tokenFlag   string
	baseURLFlag string
	jsonFlag    bool
	quietFlag   bool
	verboseFlag bool
	noColorFlag bool
)

// noColorSet tracks if --no-color was explicitly set
var noColorSet = false

// rootCmd represents the base command when called without any subcommands.
var rootCmd = &cobra.Command{
	Use:   "mineru",
	Short: "MinerU CLI — turn documents into Markdown",
	Long: `MinerU CLI is a command-line tool for extracting content from documents.

Extract PDFs, images, and web pages to Markdown with a single command:

  mineru extract report.pdf
  mineru extract https://example.com/paper.pdf -o output.md

Authenticate with your API token:

  mineru auth

For more information, visit https://mineru.net`,
	SilenceUsage:  true,
	SilenceErrors: true,
}

// Execute adds all child commands to the root command and sets flags appropriately.
func Execute() error {
	return rootCmd.Execute()
}

func init() {
	// Global flags
	rootCmd.PersistentFlags().StringVar(&tokenFlag, "token", "", "API Token (overrides env and config)")
	rootCmd.PersistentFlags().StringVar(&baseURLFlag, "base-url", "", "API base URL (for private deployments)")
	rootCmd.PersistentFlags().BoolVar(&jsonFlag, "json", false, "Output structured JSON")
	rootCmd.PersistentFlags().BoolVarP(&quietFlag, "quiet", "q", false, "Quiet mode, only output result path")
	rootCmd.PersistentFlags().BoolVarP(&verboseFlag, "verbose", "v", false, "Verbose mode, print HTTP details")
	rootCmd.PersistentFlags().BoolVar(&noColorFlag, "no-color", false, "Disable colored output")

	// Hook to handle --no-color before commands run
	rootCmd.PersistentPreRun = func(cmd *cobra.Command, args []string) {
		if noColorFlag || os.Getenv("NO_COLOR") != "" {
			output.EnableColor(false)
		}
	}
}

// getOutputFile returns the appropriate output file based on flags.
// If quiet mode, returns os.Discard; otherwise returns stderr for progress.
func getOutputFile() *os.File {
	if quietFlag {
		return os.Stderr // Still need stderr but we'll suppress output
	}
	return os.Stderr
}
