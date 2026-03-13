package cmd

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/OpenDataLab/mineru-open-cli/internal/config"
	"github.com/OpenDataLab/mineru-open-cli/internal/output"
	mineru "github.com/OpenDataLab/mineru-open-sdk"
	"github.com/spf13/cobra"
)

var (
	crawlOutput  string
	crawlFormat  string
	crawlTimeout int
	crawlStdout  bool
)

// crawlCmd represents the crawl command
var crawlCmd = &cobra.Command{
	Use:   "crawl <url>",
	Short: "Crawl a web page and convert to Markdown",
	Long:  `Fetch a web page and extract its content as Markdown. Equivalent to 'extract' with model="html".`,
	Example: `  mineru crawl https://example.com/article
  mineru crawl https://example.com/article -o output.md
  mineru crawl https://example.com/article --stdout`,
	Args: cobra.ExactArgs(1),
	RunE: runCrawl,
}

func init() {
	rootCmd.AddCommand(crawlCmd)

	crawlCmd.Flags().StringVarP(&crawlOutput, "output", "o", "", "Output path (file or directory)")
	crawlCmd.Flags().StringVarP(&crawlFormat, "format", "f", "md", "Output formats: md,html (comma-separated)")
	crawlCmd.Flags().IntVar(&crawlTimeout, "timeout", 300, "Timeout in seconds")
	crawlCmd.Flags().BoolVar(&crawlStdout, "stdout", false, "Output markdown to stdout")
}

func runCrawl(cmd *cobra.Command, args []string) error {
	url := args[0]

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

	// Build options - crawl uses html model by default
	opts := buildCrawlOptions()

	// Determine output path
	outputPath := resolveCrawlOutputPath(url)

	// Show progress if not quiet
	if !quietFlag && !crawlStdout {
		fmt.Fprintf(os.Stderr, "%s %s...\n", output.Info("Crawling"), url)
	}

	// Crawl
	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(crawlTimeout)*time.Second)
	defer cancel()

	start := time.Now()
	result, err := client.Crawl(ctx, url, opts...)
	if err != nil {
		return handleError(err)
	}

	// Save or output results
	if crawlStdout {
		fmt.Print(result.Markdown)
	} else {
		// Save markdown
		withImages := true
		if err := result.SaveMarkdown(outputPath, withImages); err != nil {
			return fmt.Errorf("failed to save output: %w", err)
		}

		// Save extra formats
		if err := saveCrawlExtraFormats(result, outputPath); err != nil {
			return err
		}

		// Output result
		elapsed := time.Since(start).Seconds()
		if jsonFlag {
			fmt.Printf(`{"status":"done","url":"%s","output":"%s","elapsed_seconds":%.1f}`+"\n",
				url, outputPath, elapsed)
		} else if !quietFlag {
			fmt.Fprintf(os.Stderr, "%s %s (%s, %.1fs)\n", output.Success("Done:"), outputPath, humanBytes(len(result.Markdown)), elapsed)
		} else {
			fmt.Println(outputPath)
		}
	}

	return nil
}

func buildCrawlOptions() []mineru.ExtractOption {
	var opts []mineru.ExtractOption
	// Crawl uses html model by default (SDK handles this)

	// Parse formats
	formats := parseFormats(crawlFormat)
	if len(formats) > 0 {
		opts = append(opts, mineru.WithExtraFormats(formats...))
	}

	return opts
}

func resolveCrawlOutputPath(url string) string {
	// If explicit output is provided
	if crawlOutput != "" {
		// Check if it's a directory
		info, err := os.Stat(crawlOutput)
		if err == nil && info.IsDir() {
			// Generate filename from URL
			name := sanitizeFilename(url)
			return filepath.Join(crawlOutput, name+".md")
		}
		return crawlOutput
	}

	// Default: generate filename from URL
	name := sanitizeFilename(url)
	return name + ".md"
}

func sanitizeFilename(url string) string {
	// Simple sanitization - remove protocol and special chars
	name := url
	if len(name) > 7 && name[:7] == "http://" {
		name = name[7:]
	}
	if len(name) > 8 && name[:8] == "https://" {
		name = name[8:]
	}
	// Replace special chars with underscore
	result := ""
	for _, c := range name {
		if (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '-' || c == '_' {
			result += string(c)
		} else {
			result += "_"
		}
	}
	// Limit length
	if len(result) > 50 {
		result = result[:50]
	}
	if result == "" {
		result = "crawl_output"
	}
	return result
}

func saveCrawlExtraFormats(result *mineru.ExtractResult, mdPath string) error {
	base := mdPath[:len(mdPath)-len(filepath.Ext(mdPath))]
	dir := filepath.Dir(mdPath)

	formats := parseFormats(crawlFormat)
	for _, f := range formats {
		switch f {
		case "html":
			path := filepath.Join(dir, filepath.Base(base)+".html")
			if err := result.SaveHTML(path); err != nil {
				return fmt.Errorf("failed to save html: %w", err)
			}
		}
	}
	return nil
}
