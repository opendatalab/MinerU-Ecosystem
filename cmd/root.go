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
	Long: `MinerU Open API CLI is a completely free command-line tool for extracting content from documents.

  # Flash Extract (Fast, No Auth, Markdown-only)
  mineru-open-api flash-extract report.pdf            # print markdown to stdout

  # Full Feature (Auth Required)
  mineru-open-api extract report.pdf                  # print markdown to stdout
  mineru-open-api extract report.pdf -o ./out/        # save all assets to directory
  mineru-open-api crawl https://mineru.net   # web page to stdout

Authenticate for Full Feature:

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
