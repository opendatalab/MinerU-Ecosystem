// Package output provides progress indicators and terminal output utilities.
package output

import (
	"fmt"
	"os"
	"sync"
	"time"
)

// Spinner provides a simple terminal spinner for indicating progress
type Spinner struct {
	frames   []string
	interval time.Duration
	prefix   string
	suffix   string

	mu      sync.Mutex
	running bool
	stop    chan struct{}
	index   int
}

// NewSpinner creates a new spinner with default settings
func NewSpinner() *Spinner {
	return &Spinner{
		frames:   []string{"⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"},
		interval: 100 * time.Millisecond,
		stop:     make(chan struct{}),
	}
}

// SetPrefix sets the text shown before the spinner
func (s *Spinner) SetPrefix(prefix string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.prefix = prefix
}

// SetSuffix sets the text shown after the spinner
func (s *Spinner) SetSuffix(suffix string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.suffix = suffix
}

// Start begins the spinner animation
func (s *Spinner) Start() {
	s.mu.Lock()
	if s.running {
		s.mu.Unlock()
		return
	}
	s.running = true
	s.mu.Unlock()

	go s.run()
}

// Stop halts the spinner animation
func (s *Spinner) Stop() {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.running {
		s.running = false
		close(s.stop)
	}
}

// StopWithMessage stops the spinner and prints a message
func (s *Spinner) StopWithMessage(msg string) {
	s.Stop()
	fmt.Fprintln(os.Stderr, msg)
}

// StopWithSuccess stops the spinner and prints a success message
func (s *Spinner) StopWithSuccess(format string, args ...interface{}) {
	s.Stop()
	msg := fmt.Sprintf(format, args...)
	fmt.Fprintln(os.Stderr, Success(msg))
}

// StopWithError stops the spinner and prints an error message
func (s *Spinner) StopWithError(format string, args ...interface{}) {
	s.Stop()
	msg := fmt.Sprintf(format, args...)
	fmt.Fprintln(os.Stderr, Error(msg))
}

func (s *Spinner) run() {
	ticker := time.NewTicker(s.interval)
	defer ticker.Stop()

	for {
		select {
		case <-s.stop:
			return
		case <-ticker.C:
			s.mu.Lock()
			if !s.running {
				s.mu.Unlock()
				return
			}
			frame := s.frames[s.index%len(s.frames)]
			prefix := s.prefix
			suffix := s.suffix
			s.index++
			s.mu.Unlock()

			if NoColor || os.Getenv("NO_COLOR") != "" {
				fmt.Fprintf(os.Stderr, "\r%s%s %s", prefix, frame, suffix)
			} else {
				fmt.Fprintf(os.Stderr, "\r\033[K%s%s %s", prefix, Bold(frame), suffix)
			}
		}
	}
}

// ProgressBar provides a simple progress bar
type ProgressBar struct {
	total     int
	current   int
	width     int
	prefix    string
	suffix    string
	completed bool
}

// NewProgressBar creates a new progress bar
func NewProgressBar(total int) *ProgressBar {
	return &ProgressBar{
		total: total,
		width: 30,
	}
}

// SetPrefix sets the prefix text
func (p *ProgressBar) SetPrefix(prefix string) {
	p.prefix = prefix
}

// SetSuffix sets the suffix text
func (p *ProgressBar) SetSuffix(suffix string) {
	p.suffix = suffix
}

// Update updates the progress bar with current value
func (p *ProgressBar) Update(current int) {
	p.current = current
	p.render()
}

// Increment increments the progress bar by 1
func (p *ProgressBar) Increment() {
	p.current++
	p.render()
}

// Finish marks the progress as complete
func (p *ProgressBar) Finish() {
	p.completed = true
	p.render()
	fmt.Fprintln(os.Stderr)
}

func (p *ProgressBar) render() {
	percent := float64(p.current) / float64(p.total)
	filled := int(percent * float64(p.width))
	empty := p.width - filled

	bar := ""
	if !NoColor && os.Getenv("NO_COLOR") == "" {
		bar += "\r\033[K" // Clear line
	} else {
		bar += "\r"
	}

	if p.prefix != "" {
		bar += p.prefix + " "
	}

	bar += "["
	if !NoColor && os.Getenv("NO_COLOR") == "" {
		for i := 0; i < filled; i++ {
			bar += Bold("=")
		}
		bar += ">"
		for i := 0; i < empty-1; i++ {
			bar += " "
		}
	} else {
		for i := 0; i < filled; i++ {
			bar += "="
		}
		bar += ">"
		for i := 0; i < empty-1; i++ {
			bar += " "
		}
	}
	bar += "]"

	if p.completed {
		bar += Success(" Done")
	} else {
		bar += fmt.Sprintf(" %d/%d (%.0f%%)", p.current, p.total, percent*100)
	}

	if p.suffix != "" {
		bar += " " + p.suffix
	}

	fmt.Fprint(os.Stderr, bar)
}

// SimpleProgress shows a simple text-based progress
func SimpleProgress(current, total int, prefix string) {
	if prefix != "" {
		fmt.Fprintf(os.Stderr, "%s %d/%d\n", prefix, current, total)
	} else {
		fmt.Fprintf(os.Stderr, "Progress: %d/%d\n", current, total)
	}
}
