// Package cmd implements the CLI commands using cobra.
package cmd

import (
	"github.com/spf13/cobra"
)

var (
	tokenFlag   string
	baseURLFlag string
	verboseFlag bool
)

var rootCmd = &cobra.Command{
	Use:     "mineru-open-api",
	Short:   "MinerU Open API CLI — turn documents into Markdown",
	Version: version,
	Long: `MinerU Open API CLI is a command-line tool for extracting content from documents.

  mineru-open-api extract report.pdf                  # markdown to stdout
  mineru-open-api extract report.pdf -o ./out/        # save to file
  mineru-open-api crawl https://example.com/article   # web page to stdout

Authenticate first:

  mineru-open-api auth

For more information, visit https://mineru.net`,
	SilenceUsage:  true,
	SilenceErrors: true,
}

func Execute() error {
	return rootCmd.Execute()
}

func init() {
	rootCmd.PersistentFlags().StringVar(&tokenFlag, "token", "", "API Token (overrides env and config)")
	rootCmd.PersistentFlags().StringVar(&baseURLFlag, "base-url", "", "API base URL (for private deployments)")
	rootCmd.PersistentFlags().BoolVarP(&verboseFlag, "verbose", "v", false, "Verbose mode, print HTTP details")
}
