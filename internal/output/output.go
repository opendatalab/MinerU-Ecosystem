// Package output handles stderr status messages (plain text, no colors, no ANSI).
package output

import (
	"fmt"
	"os"
)

func Status(format string, args ...any) {
	fmt.Fprintf(os.Stderr, format+"\n", args...)
}

func Errorf(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "Error: "+format+"\n", args...)
}
