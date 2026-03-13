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

// statusCmd represents the status command
var statusCmd = &cobra.Command{
	Use:   "status <task-id>",
	Short: "Query the status of an async task",
	Long:  `Check the status of a previously submitted extraction task.`,
	Example: `  mineru status abc-123-def
  mineru status abc-123-def --wait
  mineru status abc-123-def --wait -o ./`,
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

	// Resolve token
	tokenSrc, err := config.ResolveToken(cmd)
	if err != nil {
		return fmt.Errorf("failed to load config: %w", err)
	}
	if tokenSrc.Token == "" {
		return fmt.Errorf("no API token found. Run 'mineru auth' to configure your token")
	}

	// Load config for base URL
	cfg, _ := config.Load()

	// Build client options
	var clientOpts []mineru.ClientOption
	if baseURL := config.GetBaseURL(cmd, cfg); baseURL != "" {
		clientOpts = append(clientOpts, mineru.WithBaseURL(baseURL))
	}

	// Create client
	client, err := mineru.New(tokenSrc.Token, clientOpts...)
	if err != nil {
		return handleError(err)
	}

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
		return handleError(err)
	}

	if jsonFlag {
		fmt.Printf(`{"task_id":"%s","state":"%s"`, taskID, result.State)
		if result.Progress != nil {
			fmt.Printf(",\"progress\":{\"extracted_pages\":%d,\"total_pages\":%d,\"percent\":%.0f}",
				result.Progress.ExtractedPages, result.Progress.TotalPages, result.Progress.Percent())
		}
		if result.Error != "" {
			fmt.Printf(",\"error\":%q", result.Error)
		}
		fmt.Println("}")
	} else {
		fmt.Printf("Task: %s\n", taskID)
		fmt.Printf("State: %s\n", result.State)
		if result.Progress != nil {
			fmt.Printf("Progress: %s\n", result.Progress.String())
		}
		if result.Error != "" {
			fmt.Printf("Error: %s\n", result.Error)
		}
	}

	// Download results if requested and task is done
	if statusOutput != "" && result.State == "done" {
		return downloadResult(result, statusOutput)
	}

	return nil
}

func waitForTask(ctx context.Context, client *mineru.Client, taskID string) error {
	if !quietFlag && !jsonFlag {
		fmt.Fprintf(os.Stderr, "%s task %s...\n", output.Info("Waiting for"), taskID)
	}

	start := time.Now()
	for {
		result, err := client.GetTask(ctx, taskID)
		if err != nil {
			return handleError(err)
		}

		// Show progress
		if !quietFlag && !jsonFlag && result.Progress != nil {
			fmt.Fprintf(os.Stderr, "\rProgress: %s", result.Progress.String())
		}

		// Check if done
		if result.State == "done" || result.State == "failed" {
			if !quietFlag && !jsonFlag {
				fmt.Fprintln(os.Stderr)
			}

			elapsed := time.Since(start).Seconds()

			if jsonFlag {
				status := "done"
				errMsg := ""
				if result.State == "failed" {
					status = "error"
					errMsg = result.Error
				}
				fmt.Printf(`{"task_id":"%s","status":"%s","error":"%s","elapsed_seconds":%.1f}`+"\n",
					taskID, status, errMsg, elapsed)
			} else {
				if result.State == "done" {
					fmt.Printf("%s %s (%.1fs)\n", output.Success("Done:"), taskID, elapsed)
				} else {
					fmt.Printf("%s %s - %s\n", output.Error("Failed:"), taskID, result.Error)
				}
			}

			// Download results if requested
			if result.State == "done" && statusOutput != "" {
				return downloadResult(result, statusOutput)
			}
			return nil
		}

		// Wait before next poll
		select {
		case <-ctx.Done():
			if !quietFlag && !jsonFlag {
				fmt.Fprintln(os.Stderr)
			}
			return fmt.Errorf("timeout waiting for task %s", taskID)
		case <-time.After(2 * time.Second):
			// Continue polling
		}
	}
}

func downloadResult(result *mineru.ExtractResult, outputDir string) error {
	if err := os.MkdirAll(outputDir, 0755); err != nil {
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

	if !quietFlag && !jsonFlag {
		fmt.Printf("Saved to: %s\n", outputPath)
	}
	return nil
}
