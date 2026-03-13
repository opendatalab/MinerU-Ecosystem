// Package config handles token resolution and configuration file management.
package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/spf13/cobra"
	"gopkg.in/yaml.v3"
)

const configDirName = ".mineru"
const configFileName = "config.yaml"

// Config represents the configuration file structure.
type Config struct {
	Token   string `yaml:"token,omitempty"`
	BaseURL string `yaml:"base_url,omitempty"`
}

// configPath returns the path to the config file.
func configPath() (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("cannot get home directory: %w", err)
	}
	return filepath.Join(home, configDirName, configFileName), nil
}

// Load reads the configuration file.
func Load() (*Config, error) {
	path, err := configPath()
	if err != nil {
		return nil, err
	}

	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return &Config{}, nil
		}
		return nil, fmt.Errorf("read config: %w", err)
	}

	var cfg Config
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, fmt.Errorf("parse config: %w", err)
	}
	return &cfg, nil
}

// Save writes the configuration file.
func Save(cfg *Config) error {
	path, err := configPath()
	if err != nil {
		return err
	}

	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("create config dir: %w", err)
	}

	data, err := yaml.Marshal(cfg)
	if err != nil {
		return fmt.Errorf("marshal config: %w", err)
	}

	if err := os.WriteFile(path, data, 0600); err != nil {
		return fmt.Errorf("write config: %w", err)
	}
	return nil
}

// TokenSource describes where a token came from.
type TokenSource struct {
	Token  string
	Source string // "flag", "env", "config", ""
}

// ResolveToken resolves the API token from multiple sources in priority order:
// 1. --token flag
// 2. MINERU_TOKEN env var
// 3. ~/.mineru/config.yaml
func ResolveToken(cmd *cobra.Command) (*TokenSource, error) {
	// 1. Check --token flag
	if cmd != nil {
		tokenFlag, err := cmd.Flags().GetString("token")
		if err == nil && strings.TrimSpace(tokenFlag) != "" {
			return &TokenSource{Token: tokenFlag, Source: "flag"}, nil
		}
	}

	// 2. Check MINERU_TOKEN env var
	if tokenEnv := os.Getenv("MINERU_TOKEN"); strings.TrimSpace(tokenEnv) != "" {
		return &TokenSource{Token: tokenEnv, Source: "env"}, nil
	}

	// 3. Check config file
	cfg, err := Load()
	if err != nil {
		return nil, err
	}
	if strings.TrimSpace(cfg.Token) != "" {
		return &TokenSource{Token: cfg.Token, Source: "config"}, nil
	}

	return &TokenSource{Token: "", Source: ""}, nil
}

// GetBaseURL returns the base URL from flag, config, or default.
func GetBaseURL(cmd *cobra.Command, cfg *Config) string {
	// Check --base-url flag
	if cmd != nil {
		baseURL, err := cmd.Flags().GetString("base-url")
		if err == nil && strings.TrimSpace(baseURL) != "" {
			return baseURL
		}
	}

	// Check config
	if cfg != nil && strings.TrimSpace(cfg.BaseURL) != "" {
		return cfg.BaseURL
	}

	return ""
}

// SetToken saves the token to the config file.
func SetToken(token string) error {
	cfg, err := Load()
	if err != nil {
		return err
	}
	cfg.Token = token
	return Save(cfg)
}
