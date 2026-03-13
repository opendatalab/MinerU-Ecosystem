package cmd

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/OpenDataLab/mineru-open-cli/internal/config"
	"github.com/OpenDataLab/mineru-open-cli/internal/output"
	mineru "github.com/OpenDataLab/mineru-open-sdk"
	"github.com/spf13/cobra"
)

var (
	batchOutput      string
	batchFormat      string
	batchModel       string
	batchOCR         bool
	batchNoFormula   bool
	batchNoTable     bool
	batchLanguage    string
	batchPages       string
	batchTimeout     int
	batchListFile    string
	batchStdinList   bool
	batchConcurrency int
)

// batchCmd represents the batch command
var batchCmd = &cobra.Command{
	Use:   "batch <file1> [file2] ...",
	Short: "Batch extract multiple documents",
	Long:  `Extract multiple documents in parallel.`,
	Example: `  mineru batch *.pdf -o ./results/
  mineru batch --list urls.txt -f md,docx
  ls *.pdf | mineru batch --stdin-list -o ./out/`,
	RunE: runBatch,
}

func init() {
	rootCmd.AddCommand(batchCmd)

	batchCmd.Flags().StringVarP(&batchOutput, "output", "o", "", "Output directory (required)")
	batchCmd.Flags().StringVarP(&batchFormat, "format", "f", "md", "Output formats: md,docx,html,latex (comma-separated)")
	batchCmd.Flags().StringVar(&batchModel, "model", "", "Model: vlm, pipeline, html (default: auto)")
	batchCmd.Flags().BoolVar(&batchOCR, "ocr", false, "Enable OCR for scanned documents")
	batchCmd.Flags().BoolVar(&batchNoFormula, "no-formula", false, "Disable formula recognition")
	batchCmd.Flags().BoolVar(&batchNoTable, "no-table", false, "Disable table recognition")
	batchCmd.Flags().StringVar(&batchLanguage, "language", "ch", "Document language (default: ch)")
	batchCmd.Flags().StringVar(&batchPages, "pages", "", "Page range, e.g. '1-10,15' (applies to all)")
	batchCmd.Flags().IntVar(&batchTimeout, "timeout", 300, "Timeout per file in seconds")
	batchCmd.Flags().StringVar(&batchListFile, "list", "", "Read input list from file (one per line)")
	batchCmd.Flags().BoolVar(&batchStdinList, "stdin-list", false, "Read input list from stdin")
	batchCmd.Flags().IntVar(&batchConcurrency, "concurrency", 0, "Max concurrent uploads (0 = unlimited)")

	_ = batchCmd.MarkFlagRequired("output")
}

func runBatch(cmd *cobra.Command, args []string) error {
	// Collect all sources
	sources, err := collectSources(args)
	if err != nil {
		return err
	}

	if len(sources) == 0 {
		return fmt.Errorf("no input files specified")
	}

	// Ensure output directory exists
	if err := os.MkdirAll(batchOutput, 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

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

	// Build extract options
	opts := buildBatchOptions()

	// Run batch processing
	return runBatchProcessing(client, sources, opts)
}

func collectSources(args []string) ([]string, error) {
	var sources []string

	// From command line args
	sources = append(sources, args...)

	// From --list file
	if batchListFile != "" {
		file, err := os.Open(batchListFile)
		if err != nil {
			return nil, fmt.Errorf("failed to open list file: %w", err)
		}
		defer file.Close()

		scanner := bufio.NewScanner(file)
		for scanner.Scan() {
			line := strings.TrimSpace(scanner.Text())
			if line != "" {
				sources = append(sources, line)
			}
		}
		if err := scanner.Err(); err != nil {
			return nil, fmt.Errorf("failed to read list file: %w", err)
		}
	}

	// From --stdin-list
	if batchStdinList {
		scanner := bufio.NewScanner(os.Stdin)
		for scanner.Scan() {
			line := strings.TrimSpace(scanner.Text())
			if line != "" {
				sources = append(sources, line)
			}
		}
		if err := scanner.Err(); err != nil {
			return nil, fmt.Errorf("failed to read stdin: %w", err)
		}
	}

	return sources, nil
}

func buildBatchOptions() []mineru.ExtractOption {
	var opts []mineru.ExtractOption

	if batchModel != "" {
		opts = append(opts, mineru.WithModel(batchModel))
	}
	if batchOCR {
		opts = append(opts, mineru.WithOCR(true))
	}
	if batchNoFormula {
		opts = append(opts, mineru.WithFormula(false))
	}
	if batchNoTable {
		opts = append(opts, mineru.WithTable(false))
	}
	if batchLanguage != "ch" {
		opts = append(opts, mineru.WithLanguage(batchLanguage))
	}
	if batchPages != "" {
		opts = append(opts, mineru.WithPages(batchPages))
	}

	// Parse formats
	formats := parseFormats(batchFormat)
	if len(formats) > 0 {
		opts = append(opts, mineru.WithExtraFormats(formats...))
	}

	return opts
}

type batchResult struct {
	Index    int
	Source   string
	Output   string
	Success  bool
	Error    error
	Duration time.Duration
}

func runBatchProcessing(client *mineru.Client, sources []string, opts []mineru.ExtractOption) error {
	total := len(sources)
	results := make([]batchResult, total)
	var mu sync.Mutex
	var wg sync.WaitGroup

	// Limit concurrency if specified
	sem := make(chan struct{}, total)
	if batchConcurrency > 0 {
		sem = make(chan struct{}, batchConcurrency)
	}

	start := time.Now()

	// Progress reporting
	if !quietFlag && !jsonFlag {
		fmt.Fprintf(os.Stderr, "%s %d files...\n", output.Info("Batch processing"), total)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	for i, source := range sources {
		wg.Add(1)
		go func(idx int, src string) {
			defer wg.Done()

			sem <- struct{}{}        // Acquire
			defer func() { <-sem }() // Release

			fileStart := time.Now()

			// Progress update
			if !quietFlag && !jsonFlag {
				fmt.Fprintf(os.Stderr, "[%d/%d] %s %s...\n", idx+1, total, output.Info("Processing"), filepath.Base(src))
			}

			fileCtx, fileCancel := context.WithTimeout(ctx, time.Duration(batchTimeout)*time.Second)
			defer fileCancel()

			result, err := client.Extract(fileCtx, src, opts...)

			mu.Lock()
			results[idx] = batchResult{
				Index:    idx,
				Source:   src,
				Duration: time.Since(fileStart),
			}

			if err != nil {
				results[idx].Success = false
				results[idx].Error = err
				if !quietFlag && !jsonFlag {
					fmt.Fprintf(os.Stderr, "[%d/%d] %s %s - %v\n", idx+1, total, output.Error("Error:"), filepath.Base(src), err)
				}
			} else {
				// Save output
				outputPath := filepath.Join(batchOutput, getOutputFilename(src))
				if err := result.SaveMarkdown(outputPath, true); err != nil {
					results[idx].Success = false
					results[idx].Error = err
				} else {
					results[idx].Success = true
					results[idx].Output = outputPath
					if !quietFlag && !jsonFlag {
						fmt.Fprintf(os.Stderr, "[%d/%d] %s %s (%s)\n", idx+1, total, output.Success("Done:"), filepath.Base(src), humanBytes(len(result.Markdown)))
					}
				}
			}
			mu.Unlock()
		}(i, source)
	}

	wg.Wait()
	totalDuration := time.Since(start)

	// Summary
	successCount := 0
	for _, r := range results {
		if r.Success {
			successCount++
		}
	}

	if jsonFlag {
		// JSON output
		fmt.Println("[")
		for i, r := range results {
			status := "done"
			errMsg := ""
			if !r.Success {
				status = "error"
				if r.Error != nil {
					errMsg = r.Error.Error()
				}
			}
			fmt.Printf(`  {"index":%d,"source":"%s","status":"%s","output":"%s","error":"%s","duration_seconds":%.1f}`,
				r.Index, r.Source, status, r.Output, errMsg, r.Duration.Seconds())
			if i < len(results)-1 {
				fmt.Println(",")
			} else {
				fmt.Println()
			}
		}
		fmt.Println("]")
	} else if !quietFlag {
		fmt.Fprintf(os.Stderr, "\n%s %d/%d succeeded (%.1fs total)\n", output.Success("Done:"), successCount, total, totalDuration.Seconds())
		if successCount < total {
			fmt.Fprintf(os.Stderr, "%s %d files\n", output.Error("Failed:"), total-successCount)
		}
	}

	if successCount < total {
		return fmt.Errorf("batch processing completed with errors: %d/%d failed", total-successCount, total)
	}
	return nil
}

func getOutputFilename(source string) string {
	var base string
	if strings.HasPrefix(source, "http://") || strings.HasPrefix(source, "https://") {
		base = sanitizeFilename(source)
	} else {
		base = filepath.Base(source)
		if ext := filepath.Ext(base); ext != "" {
			base = base[:len(base)-len(ext)]
		}
	}
	return base + ".md"
}
