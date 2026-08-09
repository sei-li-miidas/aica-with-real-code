package main

import (
	"flag"
	"io"
	"os"
	"testing"
)

func withTestFlags(t *testing.T, args []string) {
	t.Helper()

	origArgs := os.Args
	origCommandLine := flag.CommandLine

	fs := flag.NewFlagSet(args[0], flag.ContinueOnError)
	fs.SetOutput(io.Discard)
	flag.CommandLine = fs
	os.Args = args

	t.Cleanup(func() {
		os.Args = origArgs
		flag.CommandLine = origCommandLine
	})
}

func TestParseFlags_Defaults(t *testing.T) {
	t.Run("デフォルト引数でフラグの初期値が設定されること", func(t *testing.T) {
		withTestFlags(t, []string{"cmd"})

		cfg := parseFlags()

		if cfg.showRoute {
			t.Fatalf("showRoute: got %v, want %v", cfg.showRoute, false)
		}
		if cfg.category != logCategory {
			t.Fatalf("category: got %q, want %q", cfg.category, logCategory)
		}
		if cfg.debugMode {
			t.Fatalf("debugMode: got %v, want %v", cfg.debugMode, false)
		}
		if cfg.port != 0 {
			t.Fatalf("port: got %d, want %d", cfg.port, 0)
		}
	})
}

func TestParseFlags_WithValues(t *testing.T) {
	t.Run("引数を指定した場合にフラグ値が正しく反映されること", func(t *testing.T) {
		withTestFlags(t, []string{
			"cmd",
			"-show-routes",
			"-category", "custom-category",
			"-debug",
		})

		cfg := parseFlags()

		if !cfg.showRoute {
			t.Fatalf("showRoute: got %v, want %v", cfg.showRoute, true)
		}
		if cfg.category != "custom-category" {
			t.Fatalf("category: got %q, want %q", cfg.category, "custom-category")
		}
		if !cfg.debugMode {
			t.Fatalf("debugMode: got %v, want %v", cfg.debugMode, true)
		}
	})
}

func TestParseFlags_IsolatedBetweenRuns(t *testing.T) {
	t.Run("複数回実行しても前回のフラグ状態が次回に影響しないこと", func(t *testing.T) {
		withTestFlags(t, []string{"cmd", "-category", "first"})
		first := parseFlags()
		if first.category != "first" {
			t.Fatalf("first.category: got %q, want %q", first.category, "first")
		}

		withTestFlags(t, []string{"cmd"})
		second := parseFlags()
		if second.category != logCategory {
			t.Fatalf("second.category: got %q, want %q", second.category, logCategory)
		}
	})
}
