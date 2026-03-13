package main

import (
	"os"

	"github.com/OpenDataLab/mineru-open-cli/cmd"
)

func main() {
	if err := cmd.Execute(); err != nil {
		os.Exit(1)
	}
}
