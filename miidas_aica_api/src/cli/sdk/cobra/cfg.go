package cobra

import (
	"time"

	"github.com/spf13/cobra"

	"aica/api/sdk/initialize"
)

type (
	PersistentRunnerConfig struct {
		CPUProf
		DisableSignalHandler bool
	}

	CPUProf struct {
		NeedVal    *bool
		OutPathVal *string
	}

	MemProf struct {
		NeedVal    *bool
		OutPathVal *string
	}
)

// SetupStandardPreHooks 標準的なPreHookを用意します。
func SetupStandardPreHooks(disableSignalHandler bool) []func(*cobra.Command, []string) error {
	pres := []func(*cobra.Command, []string) error{
		SetupLogger(),
	}

	if initialize.GetApp() == "local" {
		if !disableSignalHandler {
			pres = append(pres, SetupSignalHandler())
		}
	}
	return pres
}

// SetupCPUProfileHooks cpu profileを取得するpre/post hookを用意します
func SetupCPUProfileHooks(cfg CPUProf) (pre, post func(*cobra.Command, []string) error) {
	return SetupCPUProfileHook(cfg.NeedVal, cfg.OutPathVal)
}

// SetupIntervalCPUProfileHooks 5分毎にcpu profileを取得するpre hookを用意します
func SetupIntervalCPUProfileHooks(cfg CPUProf) (pre func(*cobra.Command, []string) error) {
	return SetupIntervalCPUProfileHook(cfg.NeedVal)
}

// SetupIntervalMemProfileHooks 5分毎にmem profileを取得するpre hookを用意します
func SetupIntervalMemProfileHooks(cfg MemProf) (pre func(*cobra.Command, []string) error) {
	return SetupIntervalMemProfileHook(cfg.NeedVal)
}

// 終了ログを出力してすぐコンテナが落ちてしまうと、
// fluentdがログを転送仕切れないことがあるので、Hookで10sスリープする
func Sleep(_ *cobra.Command, _ []string) error {
	time.Sleep(10 * time.Second)
	return nil
}
