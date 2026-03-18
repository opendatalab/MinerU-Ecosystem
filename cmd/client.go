package cmd

import (
	"github.com/OpenDataLab/mineru-open-cli/internal/config"
	mineru "github.com/opendatalab/MinerU-Ecosystem/sdk/go"
	"github.com/spf13/cobra"
)

// newClient is a helper to initialize the SDK client with global flags applied.
func newClient(cmd *cobra.Command, token string) (*mineru.Client, error) {
	cfg, _ := config.Load()
	var clientOpts []mineru.ClientOption
	if baseURL := config.GetBaseURL(cmd, cfg); baseURL != "" {
		clientOpts = append(clientOpts, mineru.WithBaseURL(baseURL))
	}
	if verboseFlag {
		clientOpts = append(clientOpts, mineru.WithHTTPClient(newVerboseHTTPClient()))
	}

	return mineru.New(token, clientOpts...)
}

// newFlashClient is a helper to initialize the SDK flash client with global flags applied.
func newFlashClient(cmd *cobra.Command) *mineru.Client {
	cfg, _ := config.Load()
	var clientOpts []mineru.ClientOption
	if baseURL := config.GetBaseURL(cmd, cfg); baseURL != "" {
		clientOpts = append(clientOpts, mineru.WithBaseURL(baseURL))
	}
	if verboseFlag {
		clientOpts = append(clientOpts, mineru.WithHTTPClient(newVerboseHTTPClient()))
	}

	client := mineru.NewFlash(clientOpts...)
	client.SetSource(config.ResolveSource())
	return client
}
