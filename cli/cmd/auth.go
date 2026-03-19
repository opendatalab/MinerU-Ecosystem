package cmd

import (
	"bufio"
	"fmt"
	"os"
	"strings"

	"github.com/opendatalab/MinerU-Ecosystem/cli/internal/config"
	"github.com/opendatalab/MinerU-Ecosystem/cli/internal/output"
	mineru "github.com/opendatalab/MinerU-Ecosystem/sdk/go"
	"github.com/spf13/cobra"
)

var (
	authVerify bool
	authShow   bool
)

var authCmd = &cobra.Command{
	Use:   "auth",
	Short: "Configure API token for Full Feature extraction",
	Long: `Authenticate with your MinerU API token. 
This is required to access Full Feature extraction (large files, multi-format, rich assets).
Get your free token at https://mineru.net`,
	Example: `  mineru-open-api auth              # Interactive token setup
  mineru-open-api auth --verify     # Verify current token
  mineru-open-api auth --show       # Show token source

  # For automation, set MINERU_TOKEN environment variable.`,
	RunE: runAuth,
}

func init() {
	rootCmd.AddCommand(authCmd)

	authCmd.Flags().BoolVar(&authVerify, "verify", false, "Verify the current token")
	authCmd.Flags().BoolVar(&authShow, "show", false, "Show current token source")
}

func runAuth(cmd *cobra.Command, args []string) error {
	if authShow {
		return runAuthShow()
	}
	if authVerify {
		return runAuthVerify()
	}
	return runAuthSetup()
}

func runAuthShow() error {
	tokenSrc, err := config.ResolveToken(nil)
	if err != nil {
		return fmt.Errorf("failed to load config: %w", err)
	}
	if tokenSrc.Token == "" {
		fmt.Println("No token configured.")
		fmt.Println("Run 'mineru-open-api auth' to set up your API token.")
		return nil
	}

	masked := maskToken(tokenSrc.Token)
	fmt.Printf("Token source: %s\n", tokenSrc.Source)
	fmt.Printf("Token: %s\n", masked)

	cfg, err := config.Load()
	if err == nil && cfg.BaseURL != "" {
		fmt.Printf("Base URL: %s\n", cfg.BaseURL)
	}
	return nil
}

func runAuthVerify() error {
	tokenSrc, err := config.ResolveToken(nil)
	if err != nil {
		return fmt.Errorf("failed to load config: %w", err)
	}
	if tokenSrc.Token == "" {
		return fmt.Errorf("no token found. Run 'mineru-open-api auth' to configure your token")
	}

	_, err = mineru.New(tokenSrc.Token)
	if err != nil {
		return fmt.Errorf("invalid token: %w", err)
	}

	fmt.Println("Token format is valid")
	fmt.Printf("  Source: %s\n", tokenSrc.Source)
	fmt.Println("  Note: full verification requires an API call.")
	return nil
}

func runAuthSetup() error {
	output.Status("MinerU API Token Setup")
	output.Status("Get your token from: https://mineru.net")
	fmt.Println()

	reader := bufio.NewReader(os.Stdin)

	existing, _ := config.ResolveToken(nil)
	if existing.Token != "" {
		fmt.Printf("Current token source: %s\n", existing.Source)
		fmt.Print("Enter new token (or press Enter to keep current): ")
	} else {
		fmt.Print("Enter your API token: ")
	}

	token, err := reader.ReadString('\n')
	if err != nil {
		return fmt.Errorf("failed to read input: %w", err)
	}
	token = strings.TrimSpace(token)

	if token == "" {
		if existing.Token != "" {
			fmt.Println("Keeping existing token.")
			return nil
		}
		return fmt.Errorf("token is required")
	}

	_, err = mineru.New(token)
	if err != nil {
		return fmt.Errorf("invalid token: %w", err)
	}

	if err := config.SetToken(token); err != nil {
		return fmt.Errorf("failed to save token: %w", err)
	}

	output.Status("Token saved successfully")
	return nil
}

func maskToken(token string) string {
	if len(token) <= 8 {
		return "***"
	}
	return token[:4] + "..." + token[len(token)-4:]
}
