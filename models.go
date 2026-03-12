package mineru

import (
	"archive/zip"
	"bytes"
	"fmt"
	"io"
	"os"
	"path/filepath"
)

// Image represents an image extracted from the document.
type Image struct {
	Name string // filename, e.g. "img_0.png"
	Data []byte
	Path string // relative path inside the zip
}

// Save writes the image to the given file path, creating parent directories.
func (img *Image) Save(path string) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, img.Data, 0o644)
}

// Progress reports extraction progress for a running task.
type Progress struct {
	ExtractedPages int    `json:"extracted_pages"`
	TotalPages     int    `json:"total_pages"`
	StartTime      string `json:"start_time"`
}

// Percent returns extraction progress as a percentage (0–100).
func (p *Progress) Percent() float64 {
	if p.TotalPages == 0 {
		return 0
	}
	return float64(p.ExtractedPages) / float64(p.TotalPages) * 100
}

func (p *Progress) String() string {
	return fmt.Sprintf("%d/%d (%.0f%%)", p.ExtractedPages, p.TotalPages, p.Percent())
}

// ExtractResult holds the result of a document extraction task.
//
// When State is "done", content fields (Markdown, ContentList, Images, and any
// requested extra formats) are populated. When the task is still in progress,
// only metadata and Progress are set.
type ExtractResult struct {
	TaskID   string
	State    string // "done" | "failed" | "pending" | "running" | "converting"
	Filename string
	Error    string
	ZipURL   string

	Progress *Progress

	Markdown    string
	ContentList []map[string]any
	Images      []Image

	Docx  []byte
	HTML  string
	LaTeX string

	zipBytes []byte
}

// SaveMarkdown writes the markdown file to path. When withImages is true,
// an images/ directory is created alongside the markdown file.
func (r *ExtractResult) SaveMarkdown(path string, withImages bool) error {
	if r.Markdown == "" {
		return fmt.Errorf("no markdown content available (state != done)")
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	if err := os.WriteFile(path, []byte(r.Markdown), 0o644); err != nil {
		return err
	}
	if withImages && len(r.Images) > 0 {
		imgDir := filepath.Join(filepath.Dir(path), "images")
		if err := os.MkdirAll(imgDir, 0o755); err != nil {
			return err
		}
		for i := range r.Images {
			if err := os.WriteFile(filepath.Join(imgDir, r.Images[i].Name), r.Images[i].Data, 0o644); err != nil {
				return err
			}
		}
	}
	return nil
}

// SaveDocx writes the docx bytes to path.
func (r *ExtractResult) SaveDocx(path string) error {
	if r.Docx == nil {
		return fmt.Errorf("no docx content — did you pass WithExtraFormats(\"docx\")?")
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, r.Docx, 0o644)
}

// SaveHTML writes the HTML string to path.
func (r *ExtractResult) SaveHTML(path string) error {
	if r.HTML == "" {
		return fmt.Errorf("no html content — did you pass WithExtraFormats(\"html\")?")
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, []byte(r.HTML), 0o644)
}

// SaveLaTeX writes the LaTeX string to path.
func (r *ExtractResult) SaveLaTeX(path string) error {
	if r.LaTeX == "" {
		return fmt.Errorf("no latex content — did you pass WithExtraFormats(\"latex\")?")
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, []byte(r.LaTeX), 0o644)
}

// SaveAll extracts the full result zip to dir.
func (r *ExtractResult) SaveAll(dir string) error {
	if r.zipBytes == nil {
		return fmt.Errorf("no zip data available (state != done)")
	}
	zr, err := zip.NewReader(bytes.NewReader(r.zipBytes), int64(len(r.zipBytes)))
	if err != nil {
		return fmt.Errorf("open zip: %w", err)
	}
	for _, f := range zr.File {
		fpath := filepath.Join(dir, f.Name)
		if f.FileInfo().IsDir() {
			os.MkdirAll(fpath, 0o755)
			continue
		}
		if err := os.MkdirAll(filepath.Dir(fpath), 0o755); err != nil {
			return err
		}
		rc, err := f.Open()
		if err != nil {
			return err
		}
		data, err := io.ReadAll(rc)
		rc.Close()
		if err != nil {
			return err
		}
		if err := os.WriteFile(fpath, data, 0o644); err != nil {
			return err
		}
	}
	return nil
}
