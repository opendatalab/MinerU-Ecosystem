package cmd

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/OpenDataLab/mineru-open-cli/internal/config"
	"github.com/OpenDataLab/mineru-open-cli/internal/output"
	mineru "github.com/OpenDataLab/mineru-open-sdk"
	"github.com/spf13/cobra"
)

var (
	crawlOutput      string
	crawlFormat      string
	crawlTimeout     int
	crawlListFile    string
	crawlStdinList   bool
	crawlConcurrency int
)

var crawlCmd = &cobra.Command{
	Use:   "crawl <url> [...]",
	Short: "Crawl web pages and convert to Markdown",
	Long:  `Fetch web pages and convert their content to Markdown (or other text formats).`,
	Example: `  mineru crawl https://example.com/article              # markdown to stdout
  mineru crawl https://example.com/article -f html       # html to stdout
  mineru crawl https://example.com/article -o ./out/      # save to file
  mineru crawl url1 url2 -o ./pages/                      # batch
  mineru crawl --list urls.txt -o ./pages/                # batch from file list`,
	RunE: runCrawl,
}

func init() {
	rootCmd.AddCommand(crawlCmd)

	crawlCmd.Flags().StringVarP(&crawlOutput, "output", "o", "", "Output path; omit to output to stdout")
	crawlCmd.Flags().StringVarP(&crawlFormat, "format", "f", "md", "Output format(s): md,json,html (comma-separated)")
	crawlCmd.Flags().IntVar(&crawlTimeout, "timeout", 0, "Timeout in seconds (default: 300 single, 1800 batch)")
	crawlCmd.Flags().StringVar(&crawlListFile, "list", "", "Read URL list from file (one per line)")
	crawlCmd.Flags().BoolVar(&crawlStdinList, "stdin-list", false, "Read URL list from stdin")
	crawlCmd.Flags().IntVar(&crawlConcurrency, "concurrency", 0, "Batch concurrency (0 = server default)")
}

func runCrawl(cmd *cobra.Command, args []string) error {
	sources, err := collectSources(args, crawlListFile, crawlStdinList)
	if err != nil {
		return err
	}
	if len(sources) == 0 {
		return fmt.Errorf("no URLs specified. Provide URLs as arguments or use --list")
	}

	formats := parseFormats(crawlFormat)

	if err := validateOutputMode(crawlOutput, formats, sources, false); err != nil {
		return err
	}

	tokenSrc, err := config.ResolveToken(cmd)
	if err != nil {
		return err
	}
	if tokenSrc.Token == "" {
		return fmt.Errorf("no API token found. Run 'mineru auth' to configure your token")
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

	crawlOpts := []mineru.ExtractOption{mineru.WithModel("html")}

	if len(sources) == 1 {
		return runSingleCrawl(client, sources[0], formats, crawlOpts)
	}
	return runBatchCrawl(client, sources, formats, crawlOpts)
}

func runSingleCrawl(client *mineru.Client, url string, formats []string, opts []mineru.ExtractOption) error {
	timeout := time.Duration(crawlTimeout) * time.Second
	if crawlTimeout == 0 {
		timeout = 5 * time.Minute
	}

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	output.Status("Crawling %s", url)

	batchID, err := client.Submit(ctx, url, opts...)
	if err != nil {
		return handleSDKError(err)
	}

	result, err := pollBatch(ctx, client, batchID)
	if err != nil {
		return handleSDKError(err)
	}

	if result.State == "failed" {
		return fmt.Errorf("crawl failed: %s", result.Error)
	}

	return outputCrawlResult(result, url, formats)
}

func runBatchCrawl(client *mineru.Client, urls, formats []string, opts []mineru.ExtractOption) error {
	timeout := time.Duration(crawlTimeout) * time.Second
	if crawlTimeout == 0 {
		timeout = 30 * time.Minute
	}

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	if err := os.MkdirAll(crawlOutput, 0o755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	output.Status("Batch: %d URLs", len(urls))

	batchID, err := client.SubmitBatch(ctx, urls, opts...)
	if err != nil {
		return handleSDKError(err)
	}

	total := len(urls)
	downloaded := make(map[int]bool)
	succeeded := 0
	failed := 0
	start := time.Now()
	interval := 2 * time.Second

	for {
		results, err := client.GetBatch(ctx, batchID)
		if err != nil {
			if ctx.Err() != nil {
				output.Status("Timeout: batch exceeded %ds limit", crawlTimeout)
				break
			}
			return handleSDKError(err)
		}

		for i, r := range results {
			if downloaded[i] {
				continue
			}
			if r.State != "done" && r.State != "failed" {
				continue
			}
			downloaded[i] = true

			name := urlToFilename(urls[i])

			if r.State == "done" {
				outPath := filepath.Join(crawlOutput, name+".md")
				if err := r.SaveMarkdown(outPath, true); err != nil {
					output.Status("[%d/%d] Error: %s - failed to save: %v", i+1, total, urls[i], err)
					failed++
				} else {
					output.Status("[%d/%d] Done: %s -> %s (%.1fs)", i+1, total,
						urls[i], outPath, time.Since(start).Seconds())
					succeeded++
				}
			} else {
				output.Status("[%d/%d] Error: %s - %s", i+1, total, urls[i], r.Error)
				failed++
			}
		}

		if len(downloaded) >= total {
			break
		}

		select {
		case <-ctx.Done():
			output.Status("Timeout: batch exceeded %ds limit", crawlTimeout)
			goto summary
		case <-time.After(interval):
		}
		if interval < 30*time.Second {
			interval = interval * 3 / 2
		}
	}

summary:
	elapsed := time.Since(start).Seconds()
	timedOut := total - succeeded - failed
	if timedOut > 0 {
		output.Status("Result: %d/%d succeeded, %d failed, %d timed out (%.1fs)", succeeded, total, failed, timedOut, elapsed)
	} else {
		output.Status("Result: %d/%d succeeded, %d failed (%.1fs)", succeeded, total, failed, elapsed)
	}

	if succeeded < total {
		return fmt.Errorf("batch completed with errors: %d/%d failed", total-succeeded, total)
	}
	return nil
}

func outputCrawlResult(result *mineru.ExtractResult, url string, formats []string) error {
	if crawlOutput == "" {
		f := formats[0]
		switch f {
		case "md":
			fmt.Print(result.Markdown)
		case "html":
			fmt.Print(result.HTML)
		case "json":
			if result.ContentList != nil {
				fmt.Print(contentListToJSON(result.ContentList))
			}
		}
		output.Status("Done: crawl complete")
		return nil
	}

	base := urlToFilename(url)
	dir := crawlOutput

	if err := os.MkdirAll(dir, 0o755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	var saved []string
	for _, f := range formats {
		switch f {
		case "md":
			p := filepath.Join(dir, base+".md")
			if err := result.SaveMarkdown(p, true); err != nil {
				return fmt.Errorf("failed to save markdown: %w", err)
			}
			saved = append(saved, p)
		case "html":
			p := filepath.Join(dir, base+".html")
			if err := result.SaveHTML(p); err != nil {
				return fmt.Errorf("failed to save html: %w", err)
			}
			saved = append(saved, p)
		}
	}

	output.Status("Done: %s", strings.Join(saved, ", "))
	return nil
}

func urlToFilename(url string) string {
	name := url
	name = strings.TrimPrefix(name, "https://")
	name = strings.TrimPrefix(name, "http://")
	replacer := strings.NewReplacer("/", "_", ":", "_", "?", "_", "&", "_", "=", "_")
	name = replacer.Replace(name)
	if len(name) > 100 {
		name = name[:100]
	}
	return name
}
