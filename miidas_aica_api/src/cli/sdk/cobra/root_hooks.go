/*
Setup-：Runnerを返す。
*/
package cobra

import (
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/rs/zerolog"
	"github.com/spf13/cobra"

	"aica/api/cli/sdk/cli"
	"aica/api/sdk/debug"
	"aica/api/sdk/initialize"
	"aica/api/sdk/logger"
	"aica/api/sdk/profile"
)

type (
	hook func(*cobra.Command, []string) error
)

// SetupLogger ログをセットアップするhookを返す
func SetupLogger() func(_ *cobra.Command, _ []string) error {
	return func(cmd *cobra.Command, args []string) error {
		var configure func(*logger.Config)
		var needDebug bool
		switch initialize.GetApp() {
		case "test", "local":
			configure = func(c *logger.Config) {
				c.NeedCaller = true
				c.OutputLevel = zerolog.InfoLevel
				c.Category = cmd.Use
			}
			needDebug = true
		default:
			configure = func(c *logger.Config) {
				c.NeedCaller = false
				c.OutputLevel = zerolog.InfoLevel
				c.Category = cmd.Use
			}
			needDebug = false
		}

		jobID := CreateJobID()

		// 通常のログ
		cli.SetupBatchLogger(jobID, configure)
		// デバッグログ
		debug.SetupLogger(needDebug, cmd.Use)
		return nil
	}
}

// SetupCPUProfileHook cpuプロファイルを取得するhookを返す
func SetupCPUProfileHook(need *bool, out *string) (pre, post func(*cobra.Command, []string) error) {
	safeTrue := func(n *bool) bool {
		if n == nil {
			return false
		}
		return *n
	}

	var p *profile.CPUProfiler

	pre = func(command *cobra.Command, _ []string) error {
		if !safeTrue(need) {
			return nil
		}

		batchName := command.Name()
		defaultPath := profile.DefaultPath(batchName, time.Now())

		var o string
		if out == nil || *out == "" {
			o = defaultPath
		} else {
			o = *out
		}

		debug.Log("cpu profiling start. filePath: " + o)
		p = profile.NewCPUProfiler(o).Start()
		return nil
	}
	post = func(*cobra.Command, []string) error {
		if !safeTrue(need) {
			return nil
		}
		debug.Log("cpu profiling end")
		p.Stop()
		return nil
	}

	return
}

// SetupIntervalCPUProfileHook 5分毎にcpuプロファイルを取得するhookを返す
func SetupIntervalCPUProfileHook(need *bool) (pre func(*cobra.Command, []string) error) {
	safeTrue := func(n *bool) bool {
		if n == nil {
			return false
		}
		return *n
	}

	pre = func(command *cobra.Command, _ []string) error {
		if !safeTrue(need) {
			return nil
		}

		batchName := command.Name()

		debug.Log("cpu profiling start.")
		profile.NewIntervalCPUProfiler(batchName).Start()
		return nil
	}

	return
}

// SetupIntervalMemProfileHook 5分毎にmemプロファイルを取得するhookを返す
func SetupIntervalMemProfileHook(need *bool) (pre func(*cobra.Command, []string) error) {
	safeTrue := func(n *bool) bool {
		if n == nil {
			return false
		}
		return *n
	}

	pre = func(command *cobra.Command, _ []string) error {
		if !safeTrue(need) {
			return nil
		}

		batchName := command.Name()

		debug.Log("mem profiling start.")
		profile.NewIntervalMemoryProfiler(batchName).Start()
		return nil
	}

	return
}

func SetupSignalHandler() hook {
	sigs := []os.Signal{syscall.SIGHUP, syscall.SIGINT, syscall.SIGTERM, syscall.SIGQUIT}

	return func(cmd *cobra.Command, args []string) error {
		sigChan := make(chan os.Signal, 1)
		signal.Notify(sigChan, sigs...)
		go func() {
			s := <-sigChan
			if v, ok := s.(syscall.Signal); ok {
				fmt.Println(v.String())
				os.Exit(int(v))
			} else {
				fmt.Println("signal unknown")
				os.Exit(255)
			}
		}()
		return nil
	}
}
