package mineru

import (
	"archive/zip"
	"bytes"
	"encoding/json"
	"io"
	"path"
	"strings"
)

// parseZip extracts content from a MinerU result zip into an ExtractResult.
func parseZip(zipBytes []byte, taskID, filename string) (*ExtractResult, error) {
	zr, err := zip.NewReader(bytes.NewReader(zipBytes), int64(len(zipBytes)))
	if err != nil {
		return nil, err
	}

	r := &ExtractResult{
		TaskID:   taskID,
		State:    "done",
		Filename: filename,
		zipBytes: zipBytes,
	}

	for _, f := range zr.File {
		if f.FileInfo().IsDir() {
			continue
		}
		name := path.Base(f.Name)
		ext := strings.ToLower(path.Ext(name))

		data, err := readZipFile(f)
		if err != nil {
			return nil, err
		}

		switch {
		case ext == ".md":
			r.Markdown = string(data)

		case strings.HasSuffix(name, "_content_list.json") || name == "content_list.json":
			var cl []map[string]any
			if json.Unmarshal(data, &cl) == nil {
				r.ContentList = cl
			}

		case ext == ".json" && r.ContentList == nil:
			var cl []map[string]any
			if json.Unmarshal(data, &cl) == nil {
				r.ContentList = cl
			}

		case isImageExt(ext):
			r.Images = append(r.Images, Image{Name: name, Data: data, Path: f.Name})

		case ext == ".docx":
			r.Docx = data

		case ext == ".html" || ext == ".htm":
			r.HTML = string(data)

		case ext == ".tex":
			r.LaTeX = string(data)
		}
	}
	return r, nil
}

func readZipFile(f *zip.File) ([]byte, error) {
	rc, err := f.Open()
	if err != nil {
		return nil, err
	}
	defer rc.Close()
	return io.ReadAll(rc)
}

func isImageExt(ext string) bool {
	switch ext {
	case ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp":
		return true
	}
	return false
}
