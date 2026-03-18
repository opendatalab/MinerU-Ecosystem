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
	flashOutput   string
	flashLanguage string
	flashPages    string
	flashTimeout  int
)

var flashExtractCmd = &cobra.Command{
	Use:   "flash-extract <file-or-url>",
	Short: "Extract documents to Markdown using flash mode (no auth required)",
	// TODO(docs): 补充 flash 模式 vs 标准模式的差异说明（多端统一文案待定）
	Long: `Parse PDFs, images, or other documents using the lightweight flash API. No API token required.`,
	Example: `  mineru-open-api flash-extract report.pdf                     # markdown to stdout
  mineru-open-api flash-extract report.pdf -o ./out/           # save to file
  mineru-open-api flash-extract https://cdn-mineru.openxlab.org.cn/demo/example.pdf    # URL mode
  mineru-open-api flash-extract report.pdf --language en       # specify language
  mineru-open-api flash-extract report.pdf --pages 1-10        # page range`,
	Args: cobra.ExactArgs(1),
	RunE: runFlashExtract,
}

func init() {
	rootCmd.AddCommand(flashExtractCmd)

	flashExtractCmd.Flags().StringVarP(&flashOutput, "output", "o", "", "Output path (file or dir); omit for stdout")
	flashExtractCmd.Flags().StringVar(&flashLanguage, "language", "ch", "Document language")
	flashExtractCmd.Flags().StringVar(&flashPages, "pages", "", "Page range, e.g. '1-10'")
	flashExtractCmd.Flags().IntVar(&flashTimeout, "timeout", 0, "Timeout in seconds (default 300)")
}

func runFlashExtract(cmd *cobra.Command, args []string) error {
	source := args[0]

	var clientOpts []mineru.ClientOption
	cfg, _ := config.Load()
	if baseURL := config.GetBaseURL(cmd, cfg); baseURL != "" {
		clientOpts = append(clientOpts, mineru.WithBaseURL(baseURL))
	}

	client := mineru.NewFlash(clientOpts...)
	client.SetSource(config.ResolveSource())

	var opts []mineru.FlashExtractOption
	if flashLanguage != "ch" {
		opts = append(opts, mineru.WithFlashLanguage(flashLanguage))
	}
	if flashPages != "" {
		opts = append(opts, mineru.WithFlashPages(flashPages))
	}

	timeout := 5 * time.Minute
	if flashTimeout > 0 {
		timeout = time.Duration(flashTimeout) * time.Second
		opts = append(opts, mineru.WithFlashTimeout(timeout))
	}

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	output.Status("Thinking... %s (flash)", filepath.Base(source))

	result, err := client.FlashExtract(ctx, source, opts...)
	if err != nil {
		return handleSDKError(err)
	}

	if err := result.Err(); err != nil {
		return handleSDKError(err)
	}

	return flashOutputResult(result, source)
}

func flashOutputResult(result *mineru.ExtractResult, source string) error {
	if flashOutput == "" {
		fmt.Print(result.Markdown)
		output.Status("Done")
		return nil
	}

	dir := flashOutput
	base := baseNameNoExt(source)

	info, err := os.Stat(dir)
	if err == nil && !info.IsDir() {
		dir = filepath.Dir(flashOutput)
		base = baseNameNoExt(flashOutput)
	}

	if err := os.MkdirAll(dir, 0o755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	p := filepath.Join(dir, base+".md")
	if err := result.SaveMarkdown(p, false); err != nil {
		return fmt.Errorf("failed to save markdown: %w", err)
	}

	output.Status("Done: %s (%s)", p, humanSize(len(result.Markdown)))
	return nil
}
