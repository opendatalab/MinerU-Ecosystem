package cmd

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/OpenDataLab/mineru-open-cli/internal/config"
	"github.com/OpenDataLab/mineru-open-cli/internal/exitcode"
	"github.com/OpenDataLab/mineru-open-cli/internal/output"
	mineru "github.com/OpenDataLab/mineru-open-sdk"
	"github.com/spf13/cobra"
)

var (
	extractOutput      string
	extractFormat      string
	extractModel       string
	extractOCR         bool
	extractNoFormula   bool
	extractNoTable     bool
	extractLanguage    string
	extractPages       string
	extractTimeout     int
	extractListFile    string
	extractStdinList   bool
	extractStdin       bool
	extractStdinName   string
	extractConcurrency int
)

var extractCmd = &cobra.Command{
	Use:   "extract <file-or-url> [...]",
	Short: "Extract documents to Markdown",
	Long:  `Parse PDFs, images, or other documents and convert to Markdown (or other formats).`,
	Example: `  mineru-open-api extract report.pdf                         # markdown to stdout
  mineru-open-api extract report.pdf -f html                  # html to stdout
  mineru-open-api extract report.pdf -o ./out/                # save to file
  mineru-open-api extract report.pdf -o ./out/ -f md,docx     # save multiple formats
  mineru-open-api extract *.pdf -o ./results/                  # batch
  mineru-open-api extract --list files.txt -o ./results/       # batch from file list`,
	RunE: runExtract,
}

func init() {
	rootCmd.AddCommand(extractCmd)

	extractCmd.Flags().StringVarP(&extractOutput, "output", "o", "", "Output path (file or dir); omit to output to stdout")
	extractCmd.Flags().StringVarP(&extractFormat, "format", "f", "md", "Output format(s): md,json,html,latex,docx (comma-separated)")
	extractCmd.Flags().StringVar(&extractModel, "model", "", "Model: vlm, pipeline, html (default: auto)")
	extractCmd.Flags().BoolVar(&extractOCR, "ocr", false, "Enable OCR for scanned documents")
	extractCmd.Flags().BoolVar(&extractNoFormula, "no-formula", false, "Disable formula recognition")
	extractCmd.Flags().BoolVar(&extractNoTable, "no-table", false, "Disable table recognition")
	extractCmd.Flags().StringVar(&extractLanguage, "language", "ch", "Document language")
	extractCmd.Flags().StringVar(&extractPages, "pages", "", "Page range, e.g. '1-10,15'")
	extractCmd.Flags().IntVar(&extractTimeout, "timeout", 0, "Timeout in seconds (default: 300 single, 1800 batch)")
	extractCmd.Flags().StringVar(&extractListFile, "list", "", "Read input list from file (one per line)")
	extractCmd.Flags().BoolVar(&extractStdinList, "stdin-list", false, "Read input list from stdin")
	extractCmd.Flags().BoolVar(&extractStdin, "stdin", false, "Read file content from stdin")
	extractCmd.Flags().StringVar(&extractStdinName, "stdin-name", "stdin.pdf", "Filename for stdin mode")
	extractCmd.Flags().IntVar(&extractConcurrency, "concurrency", 0, "Batch concurrency (0 = server default)")
}

func runExtract(cmd *cobra.Command, args []string) error {
	sources, err := collectSources(args, extractListFile, extractStdinList)
	if err != nil {
		return err
	}

	if len(sources) == 0 && !extractStdin {
		return fmt.Errorf("no input files specified. Provide files as arguments, use --list, or --stdin")
	}

	formats := parseFormats(extractFormat)

	if err := validateOutputMode(extractOutput, formats, sources, extractStdin); err != nil {
		return err
	}

	tokenSrc, err := config.ResolveToken(cmd)
	if err != nil {
		return err
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

	opts := buildExtractOpts()

	if extractStdin {
		return runStdinExtract(client, opts)
	}
	if len(sources) == 1 {
		return runSingleExtract(client, sources[0], formats, opts)
	}
	return runBatchExtract(client, sources, formats, opts)
}

// ── single file ──

func runSingleExtract(client *mineru.Client, source string, formats []string, opts []mineru.ExtractOption) error {
	timeout := time.Duration(extractTimeout) * time.Second
	if extractTimeout == 0 {
		timeout = 5 * time.Minute
	}

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	output.Status("Uploading %s", filepath.Base(source))

	batchID, err := client.Submit(ctx, source, opts...)
	if err != nil {
		return handleSDKError(err)
	}

	result, err := pollBatch(ctx, client, batchID)
	if err != nil {
		return handleSDKError(err)
	}

	if err := result.Err(); err != nil {
		return handleSDKError(err)
	}

	return outputResult(result, source, formats)
}

// ── stdin ──

func runStdinExtract(client *mineru.Client, opts []mineru.ExtractOption) error {
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		return fmt.Errorf("failed to read stdin: %w", err)
	}
	if len(data) == 0 {
		return fmt.Errorf("no data received from stdin")
	}

	tmpFile, err := os.CreateTemp("", "mineru-stdin-*"+filepath.Ext(extractStdinName))
	if err != nil {
		return fmt.Errorf("failed to create temp file: %w", err)
	}
	defer os.Remove(tmpFile.Name())

	if _, err := tmpFile.Write(data); err != nil {
		tmpFile.Close()
		return fmt.Errorf("failed to write temp file: %w", err)
	}
	tmpFile.Close()

	formats := parseFormats(extractFormat)
	return runSingleExtract(client, tmpFile.Name(), formats, opts)
}

// ── batch ──

func runBatchExtract(client *mineru.Client, sources, formats []string, opts []mineru.ExtractOption) error {
	timeout := time.Duration(extractTimeout) * time.Second
	if extractTimeout == 0 {
		timeout = 30 * time.Minute
	}

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	if err := os.MkdirAll(extractOutput, 0o755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	output.Status("Batch: %d files", len(sources))

	batchID, err := client.SubmitBatch(ctx, sources, opts...)
	if err != nil {
		return handleSDKError(err)
	}

	total := len(sources)
	downloaded := make(map[int]bool)
	succeeded := 0
	failed := 0
	start := time.Now()
	interval := 2 * time.Second

	for {
		results, err := client.GetBatch(ctx, batchID)
		if err != nil {
			if ctx.Err() != nil {
				output.Status("Timeout: batch exceeded %ds limit", extractTimeout)
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

			src := sources[i]
			if i < len(sources) {
				src = sources[i]
			}

			if r.State == "done" {
				outPath := filepath.Join(extractOutput, baseNameNoExt(src)+".md")
				if err := r.SaveMarkdown(outPath, true); err != nil {
					output.Status("[%d/%d] Error: %s - failed to save: %v", i+1, total, filepath.Base(src), err)
					failed++
				} else {
					saveExtraFormatsToDir(r, extractOutput, baseNameNoExt(src), formats)
					output.Status("[%d/%d] Done: %s -> %s (%s, %.1fs)", i+1, total,
						filepath.Base(src), outPath, humanSize(len(r.Markdown)), time.Since(start).Seconds())
					succeeded++
				}
			} else {
				if taskErr := r.Err(); taskErr != nil {
					info := exitcode.Wrap(taskErr)
					output.Status("[%d/%d] Error: %s - %s", i+1, total, filepath.Base(src), info.Message)
					if info.Hint != "" {
						output.Status("  Hint: %s", info.Hint)
					}
				} else {
					output.Status("[%d/%d] Error: %s - %s", i+1, total, filepath.Base(src), r.Error)
				}
				failed++
			}
		}

		if len(downloaded) >= total {
			break
		}

		select {
		case <-ctx.Done():
			output.Status("Timeout: batch exceeded %ds limit", extractTimeout)
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

// ── polling ──

func pollBatch(ctx context.Context, client *mineru.Client, batchID string) (*mineru.ExtractResult, error) {
	interval := 2 * time.Second
	for {
		results, err := client.GetBatch(ctx, batchID)
		if err != nil {
			return nil, err
		}
		if len(results) > 0 {
			r := results[0]
			if r.Progress != nil {
				output.Status("Parsing %d/%d pages", r.Progress.ExtractedPages, r.Progress.TotalPages)
			}
			if r.State == "done" || r.State == "failed" {
				return r, nil
			}
		}
		select {
		case <-ctx.Done():
			return nil, fmt.Errorf("timeout waiting for batch %s", batchID)
		case <-time.After(interval):
		}
		if interval < 30*time.Second {
			interval = interval * 3 / 2
		}
	}
}

// ── output ──

func outputResult(result *mineru.ExtractResult, source string, formats []string) error {
	if extractOutput == "" {
		// stdout mode: output the requested format
		f := formats[0]
		switch f {
		case "md":
			fmt.Print(result.Markdown)
		case "html":
			fmt.Print(result.HTML)
		case "latex":
			fmt.Print(result.LaTeX)
		case "json":
			if result.ContentList != nil {
				// ContentList is []map[string]any, serialize manually
				fmt.Print(contentListToJSON(result.ContentList))
			}
		}
		output.Status("Done: %d pages, %.1fs", pageCount(result), 0.0)
		return nil
	}

	// file mode
	base := baseNameNoExt(source)
	dir := extractOutput

	info, err := os.Stat(dir)
	if err == nil && !info.IsDir() {
		// -o points to a file path
		dir = filepath.Dir(extractOutput)
		base = baseNameNoExt(extractOutput)
	}

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
		case "docx":
			p := filepath.Join(dir, base+".docx")
			if err := result.SaveDocx(p); err != nil {
				return fmt.Errorf("failed to save docx: %w", err)
			}
			saved = append(saved, p)
		case "html":
			p := filepath.Join(dir, base+".html")
			if err := result.SaveHTML(p); err != nil {
				return fmt.Errorf("failed to save html: %w", err)
			}
			saved = append(saved, p)
		case "latex":
			p := filepath.Join(dir, base+".tex")
			if err := result.SaveLaTeX(p); err != nil {
				return fmt.Errorf("failed to save latex: %w", err)
			}
			saved = append(saved, p)
		}
	}

	output.Status("Done: %s (%d pages)", strings.Join(saved, ", "), pageCount(result))
	return nil
}

// ── validation ──

func validateOutputMode(outputPath string, formats []string, sources []string, isStdin bool) error {
	if outputPath != "" {
		return nil
	}

	count := len(sources)
	if isStdin {
		count = 1
	}

	if count > 1 {
		return fmt.Errorf("batch mode requires -o to specify output directory")
	}
	if len(formats) > 1 {
		return fmt.Errorf("multiple formats cannot output to stdout, use -o to save to file")
	}
	if len(formats) == 1 && isBinaryFormat(formats[0]) {
		return fmt.Errorf("%s is binary format, cannot output to stdout, use -o to save to file", formats[0])
	}
	return nil
}

func isBinaryFormat(f string) bool {
	return f == "docx"
}

// ── options builders ──

func buildExtractOpts() []mineru.ExtractOption {
	var opts []mineru.ExtractOption
	if extractModel != "" {
		opts = append(opts, mineru.WithModel(extractModel))
	}
	if extractOCR {
		opts = append(opts, mineru.WithOCR(true))
	}
	if extractNoFormula {
		opts = append(opts, mineru.WithFormula(false))
	}
	if extractNoTable {
		opts = append(opts, mineru.WithTable(false))
	}
	if extractLanguage != "ch" {
		opts = append(opts, mineru.WithLanguage(extractLanguage))
	}
	if extractPages != "" {
		opts = append(opts, mineru.WithPages(extractPages))
	}

	extraFormats := extraFormatsForSDK(parseFormats(extractFormat))
	if len(extraFormats) > 0 {
		opts = append(opts, mineru.WithExtraFormats(extraFormats...))
	}
	return opts
}

// extraFormatsForSDK returns formats the SDK needs to request beyond default md.
func extraFormatsForSDK(formats []string) []string {
	var extra []string
	for _, f := range formats {
		if f != "md" && f != "json" {
			extra = append(extra, f)
		}
	}
	return extra
}

// ── shared helpers ──

func collectSources(args []string, listFile string, stdinList bool) ([]string, error) {
	var sources []string
	sources = append(sources, args...)

	if listFile != "" {
		f, err := os.Open(listFile)
		if err != nil {
			return nil, fmt.Errorf("failed to open list file: %w", err)
		}
		defer f.Close()
		scanner := bufio.NewScanner(f)
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

	if stdinList {
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

func parseFormats(raw string) []string {
	if raw == "" {
		return []string{"md"}
	}
	var formats []string
	for _, f := range strings.Split(raw, ",") {
		f = strings.TrimSpace(strings.ToLower(f))
		if f != "" {
			formats = append(formats, f)
		}
	}
	if len(formats) == 0 {
		return []string{"md"}
	}
	return formats
}

func baseNameNoExt(source string) string {
	base := filepath.Base(source)
	ext := filepath.Ext(base)
	if ext != "" {
		return base[:len(base)-len(ext)]
	}
	return base
}

func saveExtraFormatsToDir(result *mineru.ExtractResult, dir, base string, formats []string) {
	for _, f := range formats {
		switch f {
		case "docx":
			_ = result.SaveDocx(filepath.Join(dir, base+".docx"))
		case "html":
			_ = result.SaveHTML(filepath.Join(dir, base+".html"))
		case "latex":
			_ = result.SaveLaTeX(filepath.Join(dir, base+".tex"))
		}
	}
}

func pageCount(r *mineru.ExtractResult) int {
	if r.Progress != nil {
		return r.Progress.TotalPages
	}
	return 0
}

func humanSize(n int) string {
	if n < 1024 {
		return fmt.Sprintf("%d B", n)
	}
	if n < 1024*1024 {
		return fmt.Sprintf("%.1f KB", float64(n)/1024)
	}
	return fmt.Sprintf("%.1f MB", float64(n)/(1024*1024))
}

func contentListToJSON(cl []map[string]any) string {
	data, err := json.Marshal(cl)
	if err != nil {
		return "[]"
	}
	return string(data)
}

func handleSDKError(err error) error {
	info := exitcode.Wrap(err)
	if info == nil {
		return nil
	}
	output.Errorf("%s", info.Message)
	if info.Hint != "" {
		output.Status("Hint: %s", info.Hint)
	}
	os.Exit(info.Code)
	return nil
}
