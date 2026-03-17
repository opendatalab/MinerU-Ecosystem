package cmd

import (
	"context"
	"fmt"
	"os"
	"time"

	"github.com/OpenDataLab/mineru-open-cli/internal/config"
	"github.com/OpenDataLab/mineru-open-cli/internal/output"
	mineru "github.com/OpenDataLab/mineru-open-sdk"
	"github.com/spf13/cobra"
)

var (
	statusWait    bool
	statusOutput  string
	statusTimeout int
)

var statusCmd = &cobra.Command{
	Use:   "status <task-id>",
	Short: "Query the status of an async task",
	Long:  `Check the status of a previously submitted extraction task.`,
	Example: `  mineru-open-api status abc-123-def
  mineru-open-api status abc-123-def --wait
  mineru-open-api status abc-123-def --wait -o ./`,
	Args: cobra.ExactArgs(1),
	RunE: runStatus,
}

func init() {
	rootCmd.AddCommand(statusCmd)

	statusCmd.Flags().BoolVar(&statusWait, "wait", false, "Wait for task completion")
	statusCmd.Flags().StringVarP(&statusOutput, "output", "o", "", "Download results to this directory when done")
	statusCmd.Flags().IntVar(&statusTimeout, "timeout", 300, "Max wait time in seconds")
}

func runStatus(cmd *cobra.Command, args []string) error {
	taskID := args[0]

	tokenSrc, err := config.ResolveToken(cmd)
	if err != nil {
		return fmt.Errorf("failed to load config: %w", err)
	}
	if tokenSrc.Token == "" {
		return fmt.Errorf("no API token found. Run 'mineru-open-api auth' to configure your token")
	}

	cfg, _ := config.Load()
	var clientOpts []mineru.ClientOption
	if baseURL := config.GetBaseURL(cmd, cfg); baseURL != "" {
		clientOpts = append(clientOpts, mineru.WithBaseURL(baseURL))
	}

	client, err := mineru.New(tokenSrc.Token, clientOpts...)
	if err != nil {
		return handleSDKError(err)
	}
	client.SetSource(config.ResolveSource())

	ctx := context.Background()
	if statusWait {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(ctx, time.Duration(statusTimeout)*time.Second)
		defer cancel()
	}

	if statusWait {
		return waitForTask(ctx, client, taskID)
	}
	return checkTaskOnce(ctx, client, taskID)
}

func checkTaskOnce(ctx context.Context, client *mineru.Client, taskID string) error {
	result, err := client.GetTask(ctx, taskID)
	if err != nil {
		return handleSDKError(err)
	}

	fmt.Printf("Task: %s\n", taskID)
	fmt.Printf("State: %s\n", result.State)
	if result.Progress != nil {
		fmt.Printf("Progress: %s\n", result.Progress.String())
	}
	if result.Error != "" {
		fmt.Printf("Error: %s\n", result.Error)
	}

	if statusOutput != "" && result.State == "done" {
		return downloadStatusResult(result, statusOutput)
	}
	return nil
}

func waitForTask(ctx context.Context, client *mineru.Client, taskID string) error {
	output.Status("Waiting for task %s...", taskID)

	start := time.Now()
	interval := 2 * time.Second

	for {
		result, err := client.GetTask(ctx, taskID)
		if err != nil {
			return handleSDKError(err)
		}

		if result.Progress != nil {
			output.Status("Progress: %s", result.Progress.String())
		}

		if result.State == "done" || result.State == "failed" {
			elapsed := time.Since(start).Seconds()

			if result.State == "done" {
				output.Status("Done: %s (%.1fs)", taskID, elapsed)
			} else {
				output.Status("Failed: %s - %s", taskID, result.Error)
			}

			if result.State == "done" && statusOutput != "" {
				return downloadStatusResult(result, statusOutput)
			}
			return nil
		}

		select {
		case <-ctx.Done():
			return fmt.Errorf("timeout waiting for task %s", taskID)
		case <-time.After(interval):
		}
		if interval < 30*time.Second {
			interval = interval * 3 / 2
		}
	}
}

func downloadStatusResult(result *mineru.ExtractResult, outputDir string) error {
	if err := os.MkdirAll(outputDir, 0o755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	outputPath := outputDir
	if result.Filename != "" {
		outputPath = outputDir + "/" + result.Filename + ".md"
	} else {
		outputPath = outputDir + "/result.md"
	}

	if err := result.SaveMarkdown(outputPath, true); err != nil {
		return fmt.Errorf("failed to save result: %w", err)
	}

	output.Status("Saved to: %s", outputPath)
	return nil
}
