package cmd

import (
	"fmt"

	"github.com/OpenDataLab/mineru-open-cli/internal/config"
	"github.com/OpenDataLab/mineru-open-cli/internal/output"
	"github.com/spf13/cobra"
)

var (
	setSourceShow  bool
	setSourceReset bool
)

var setSourceCmd = &cobra.Command{
	Use:   "set-source [source]",
	Short: "Set the source identifier for API request tracking",
	Long: `Persist a source identifier that is sent with every API request.
This helps track which application or integration is calling the API.

The source is saved to ~/.mineru/config.yaml and used automatically
by all subsequent commands.`,
	Example: `  mineru-open-api set-source cursor-skill-pdf   # Set source
  mineru-open-api set-source --show              # Show current source
  mineru-open-api set-source --reset             # Reset to default`,
	Args: cobra.MaximumNArgs(1),
	RunE: runSetSource,
}

func init() {
	rootCmd.AddCommand(setSourceCmd)

	setSourceCmd.Flags().BoolVar(&setSourceShow, "show", false, "Show current source")
	setSourceCmd.Flags().BoolVar(&setSourceReset, "reset", false, "Reset source to default")
}

func runSetSource(cmd *cobra.Command, args []string) error {
	if setSourceShow {
		source := config.ResolveSource()
		fmt.Printf("Source: %s\n", source)

		cfg, err := config.Load()
		if err == nil && cfg.Source != "" {
			fmt.Printf("  Configured in: ~/.mineru/config.yaml\n")
		} else if src := config.ResolveSource(); src != "open-api-cli" {
			fmt.Printf("  Configured via: MINERU_SOURCE env var\n")
		} else {
			fmt.Printf("  Using default\n")
		}
		return nil
	}

	if setSourceReset {
		if err := config.SetSource(""); err != nil {
			return fmt.Errorf("failed to reset source: %w", err)
		}
		output.Status("Source reset to default (open-api-cli)")
		return nil
	}

	if len(args) == 0 {
		return fmt.Errorf("source value is required. Usage: mineru-open-api set-source <value>")
	}

	source := args[0]
	if err := config.SetSource(source); err != nil {
		return fmt.Errorf("failed to save source: %w", err)
	}
	output.Status("Source set to: %s", source)
	return nil
}
