package cmd

import (
	"context"
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
	extractOutput    string
	extractFormat    string
	extractModel     string
	extractOCR       bool
	extractNoFormula bool
	extractNoTable   bool
	extractLanguage  string
	extractPages     string
	extractTimeout   int
	extractStdin     bool
	extractStdinName string
	extractStdout    bool
)

// extractCmd represents the extract command
var extractCmd = &cobra.Command{
	Use:   "extract <file-or-url>",
	Short: "Extract a document to Markdown",
	Long:  `Parse a PDF, image, or webpage and convert it to Markdown.`,
	Example: `  mineru extract report.pdf
  mineru extract report.pdf -o ./output/ -f md,docx
  mineru extract https://example.com/paper.pdf --model vlm --pages 1-10
  mineru extract scan.pdf --ocr --language en
  cat report.pdf | mineru extract --stdin -o result.md`,
	Args: func(cmd *cobra.Command, args []string) error {
		if extractStdin {
			return nil // stdin mode doesn't require args
		}
		if len(args) < 1 {
			return fmt.Errorf("requires file or URL argument, or use --stdin")
		}
		return nil
	},
	RunE: runExtract,
}

func init() {
	rootCmd.AddCommand(extractCmd)

	extractCmd.Flags().StringVarP(&extractOutput, "output", "o", "", "Output path (file or directory)")
	extractCmd.Flags().StringVarP(&extractFormat, "format", "f", "md", "Output formats: md,docx,html,latex (comma-separated)")
	extractCmd.Flags().StringVar(&extractModel, "model", "", "Model: vlm, pipeline, html (default: auto)")
	extractCmd.Flags().BoolVar(&extractOCR, "ocr", false, "Enable OCR for scanned documents")
	extractCmd.Flags().BoolVar(&extractNoFormula, "no-formula", false, "Disable formula recognition")
	extractCmd.Flags().BoolVar(&extractNoTable, "no-table", false, "Disable table recognition")
	extractCmd.Flags().StringVar(&extractLanguage, "language", "ch", "Document language (default: ch)")
	extractCmd.Flags().StringVar(&extractPages, "pages", "", "Page range, e.g. '1-10,15' or '2--2'")
	extractCmd.Flags().IntVar(&extractTimeout, "timeout", 300, "Timeout in seconds")
	extractCmd.Flags().BoolVar(&extractStdin, "stdin", false, "Read file content from stdin")
	extractCmd.Flags().StringVar(&extractStdinName, "stdin-name", "stdin.pdf", "Filename for stdin mode")
	extractCmd.Flags().BoolVar(&extractStdout, "stdout", false, "Output markdown to stdout")
}

func runExtract(cmd *cobra.Command, args []string) error {
	var source string
	var stdinData []byte

	if extractStdin {
		// Read from stdin
		if !quietFlag {
			fmt.Fprintln(os.Stderr, "Reading from stdin...")
		}
		var err error
		stdinData, err = io.ReadAll(os.Stdin)
		if err != nil {
			return fmt.Errorf("failed to read from stdin: %w", err)
		}
		if len(stdinData) == 0 {
			return fmt.Errorf("no data received from stdin")
		}
		if !quietFlag {
			fmt.Fprintf(os.Stderr, "Received %s from stdin\n", humanBytes(len(stdinData)))
		}
		source = extractStdinName
	} else {
		if len(args) < 1 {
			return fmt.Errorf("missing file or URL argument")
		}
		source = args[0]
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

	// Handle stdin data - write to temp file
	if stdinData != nil {
		tempFile, err := os.CreateTemp("", "mineru-stdin-*"+filepath.Ext(extractStdinName))
		if err != nil {
			return fmt.Errorf("failed to create temp file: %w", err)
		}
		defer os.Remove(tempFile.Name())

		if _, err := tempFile.Write(stdinData); err != nil {
			tempFile.Close()
			return fmt.Errorf("failed to write temp file: %w", err)
		}
		tempFile.Close()
		source = tempFile.Name()
	}

	// Build extract options
	opts := buildExtractOptions()

	// Determine output path
	displaySource := extractStdinName
	if !extractStdin {
		displaySource = source
	}
	outputPath := resolveOutputPath(displaySource)

	// Show progress if not quiet
	if !quietFlag && !extractStdout {
		fmt.Fprintf(os.Stderr, "%s %s...\n", output.Info("Extracting"), displaySource)
	}

	// Extract
	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(extractTimeout)*time.Second)
	defer cancel()

	start := time.Now()
	result, err := client.Extract(ctx, source, opts...)
	if err != nil {
		return handleError(err)
	}

	// Save or output results
	if extractStdout {
		fmt.Print(result.Markdown)
	} else {
		// Save markdown
		withImages := true
		if err := result.SaveMarkdown(outputPath, withImages); err != nil {
			return fmt.Errorf("failed to save output: %w", err)
		}

		// Save extra formats
		if err := saveExtraFormats(result, outputPath); err != nil {
			return err
		}

		// Output result
		elapsed := time.Since(start).Seconds()
		if jsonFlag {
			fmt.Printf(`{"status":"done","file":"%s","output":"%s","pages":%d,"elapsed_seconds":%.1f}`+"\n",
				filepath.Base(source), outputPath, getPageCount(result), elapsed)
		} else if !quietFlag {
			fmt.Fprintf(os.Stderr, "%s %s (%s, %.1fs)\n", output.Success("Done:"), outputPath, humanBytes(len(result.Markdown)), elapsed)
		} else {
			fmt.Println(outputPath)
		}
	}

	return nil
}

func buildExtractOptions() []mineru.ExtractOption {
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

	// Parse formats
	formats := parseFormats(extractFormat)
	if len(formats) > 0 {
		opts = append(opts, mineru.WithExtraFormats(formats...))
	}

	return opts
}

func parseFormats(format string) []string {
	if format == "" || format == "md" {
		return nil
	}
	var formats []string
	for _, f := range strings.Split(format, ",") {
		f = strings.TrimSpace(strings.ToLower(f))
		if f != "" && f != "md" {
			formats = append(formats, f)
		}
	}
	return formats
}

func resolveOutputPath(source string) string {
	// If explicit output is provided
	if extractOutput != "" {
		// Check if it's a directory
		info, err := os.Stat(extractOutput)
		if err == nil && info.IsDir() {
			base := filepath.Base(source)
			ext := filepath.Ext(base)
			name := base[:len(base)-len(ext)]
			return filepath.Join(extractOutput, name+".md")
		}
		return extractOutput
	}

	// Default: same directory, same name with .md extension
	base := filepath.Base(source)
	ext := filepath.Ext(base)
	name := base[:len(base)-len(ext)]
	return name + ".md"
}

func saveExtraFormats(result *mineru.ExtractResult, mdPath string) error {
	base := mdPath[:len(mdPath)-len(filepath.Ext(mdPath))]
	dir := filepath.Dir(mdPath)

	formats := parseFormats(extractFormat)
	for _, f := range formats {
		switch f {
		case "docx":
			path := filepath.Join(dir, filepath.Base(base)+".docx")
			if err := result.SaveDocx(path); err != nil {
				return fmt.Errorf("failed to save docx: %w", err)
			}
		case "html":
			path := filepath.Join(dir, filepath.Base(base)+".html")
			if err := result.SaveHTML(path); err != nil {
				return fmt.Errorf("failed to save html: %w", err)
			}
		case "latex":
			path := filepath.Join(dir, filepath.Base(base)+".tex")
			if err := result.SaveLaTeX(path); err != nil {
				return fmt.Errorf("failed to save latex: %w", err)
			}
		}
	}
	return nil
}

func handleError(err error) error {
	info := exitcode.Wrap(err)
	if info == nil {
		return nil
	}

	if jsonFlag {
		fmt.Printf(`{"status":"error","error_code":"%d","error_message":"%s"}`+"\n", info.Code, info.Message)
	} else {
		fmt.Fprintf(os.Stderr, "%s %s\n", output.Error("Error:"), info.Message)
		if info.Hint != "" {
			fmt.Fprintf(os.Stderr, "  %s %s\n", output.Info("Hint:"), info.Hint)
		}
	}

	os.Exit(info.Code)
	return nil // never reached
}

func getPageCount(result *mineru.ExtractResult) int {
	if result.Progress != nil {
		return result.Progress.TotalPages
	}
	return 0
}

func humanBytes(n int) string {
	if n < 1024 {
		return fmt.Sprintf("%d B", n)
	}
	if n < 1024*1024 {
		return fmt.Sprintf("%.1f KB", float64(n)/1024)
	}
	return fmt.Sprintf("%.1f MB", float64(n)/(1024*1024))
}
