// Package output handles terminal output formatting and colors.
package output

import (
	"fmt"
	"os"
)

var (
	// NoColor disables colored output
	NoColor = false
)

// Color codes
const (
	reset   = "\033[0m"
	red     = "\033[31m"
	green   = "\033[32m"
	yellow  = "\033[33m"
	blue    = "\033[34m"
	magenta = "\033[35m"
	cyan    = "\033[36m"
	gray    = "\033[90m"
	bold    = "\033[1m"
)

// EnableColor enables or disables colored output based on environment
func EnableColor(enabled bool) {
	NoColor = !enabled
}

// colorize wraps text with color codes if colors are enabled
func colorize(text, color string) string {
	if NoColor || os.Getenv("NO_COLOR") != "" {
		return text
	}
	return color + text + reset
}

// Success returns a success-colored string
func Success(text string) string {
	return colorize(text, green)
}

// Error returns an error-colored string
func Error(text string) string {
	return colorize(text, red)
}

// Warning returns a warning-colored string
func Warning(text string) string {
	return colorize(text, yellow)
}

// Info returns an info-colored string
func Info(text string) string {
	return colorize(text, blue)
}

// Bold returns bold text
func Bold(text string) string {
	return colorize(text, bold)
}

// Gray returns gray text
func Gray(text string) string {
	return colorize(text, gray)
}

// Successf returns a formatted success string
func Successf(format string, args ...interface{}) string {
	return Success(fmt.Sprintf(format, args...))
}

// Errorf returns a formatted error string
func Errorf(format string, args ...interface{}) string {
	return Error(fmt.Sprintf(format, args...))
}

// Warningf returns a formatted warning string
func Warningf(format string, args ...interface{}) string {
	return Warning(fmt.Sprintf(format, args...))
}

// Infof returns a formatted info string
func Infof(format string, args ...interface{}) string {
	return Info(fmt.Sprintf(format, args...))
}
