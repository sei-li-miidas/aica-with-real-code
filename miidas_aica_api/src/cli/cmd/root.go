package cmd

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"

	"aica/api/cli/internal"
	mcobra "aica/api/cli/sdk/cobra"
	"aica/api/sdk/aica"
)

var (
	// 並行実行数
	concurrency int

	// cpuプロファイルの取得
	cpuProf bool

	// cpuプロファイルの出力先
	cpuProfOut string

	// 5分毎のcpuプロファイルの取得（ワーカー用）
	intervalCpuProf bool

	// 5分毎のmemプロファイルの取得（ワーカー用）
	intervalMemProf bool

	// ローカル環境用のsignalhandleを無効化するか
	disableSignalHandle bool

	// デバッグログ出力
	debugMode bool
)

var (
	serviceDef  = aica.MCPToolBatch
	logCategory = serviceDef.LogCategory
	serviceName = serviceDef.DBEnv
)

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
	Use:           "Prepare for semantic search",
	Short:         "意味検索のためのバッチ処理",
	SilenceErrors: true,
	SilenceUsage:  true,
}

// Execute adds all child commands to the root command and sets flags appropriately.
// This is called by main.main(). It only needs to happen once to the rootCmd.
func Execute() {
	rootCmd.SetOut(os.Stdout)
	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

func init() {
	cobra.OnInitialize()
	mcobra.SetupConcurrency(rootCmd, &concurrency)
	mcobra.SetupCpuProf(rootCmd, &cpuProf, &cpuProfOut)
	mcobra.SetupIntervalCpuProf(rootCmd, &intervalCpuProf)
	mcobra.SetupIntervalMemProf(rootCmd, &intervalMemProf)
	mcobra.SetupDisableSignalHandle(rootCmd, &disableSignalHandle)
	rootCmd.PersistentFlags().BoolVar(&debugMode, "debug-log", false, "デバッグモード。デバッグログが出力され、全てのログに出力箇所が追加されます。")

	cfg := mcobra.CPUProf{
		NeedVal:    &cpuProf,
		OutPathVal: &cpuProfOut,
	}
	intervalCfg := mcobra.CPUProf{
		NeedVal: &intervalCpuProf,
	}
	intervalMemCfg := mcobra.MemProf{
		NeedVal: &intervalMemProf,
	}

	pre := append(mcobra.SetupStandardPreHooks(disableSignalHandle), setupDBConn())
	cpuPre, cpuPost := mcobra.SetupCPUProfileHooks(cfg)
	intervalCpuPre := mcobra.SetupIntervalCPUProfileHooks(intervalCfg)
	intervalMemPre := mcobra.SetupIntervalMemProfileHooks(intervalMemCfg)

	rootCmd.PersistentPreRunE = mcobra.MultiHook(append(pre, cpuPre, intervalCpuPre, intervalMemPre)...)
	rootCmd.PersistentPostRunE = mcobra.MultiHook(cpuPost, mcobra.Sleep)
}

func setupDBConn() func(*cobra.Command, []string) error {
	return func(cmd *cobra.Command, args []string) error {
		if err := internal.SetupRDB(serviceName, logCategory, debugMode); err != nil {
			fmt.Println(err)
			panic(err)
		}

		return nil
	}
}
