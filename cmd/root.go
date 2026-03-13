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
	Use:   "mineru",
	Short: "MinerU CLI — turn documents into Markdown",
	Long: `MinerU CLI is a command-line tool for extracting content from documents.

  mineru extract report.pdf                  # markdown to stdout
  mineru extract report.pdf -o ./out/        # save to file
  mineru crawl https://example.com/article   # web page to stdout

Authenticate first:

  mineru auth

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
