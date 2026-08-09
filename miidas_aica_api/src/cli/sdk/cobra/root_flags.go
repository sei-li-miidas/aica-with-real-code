package cobra

import (
	"runtime"

	"github.com/spf13/cobra"
)

// SetupConcurrency は並列実行数を設定する。
func SetupConcurrency(cmd *cobra.Command, concurrency *int) {
	cmd.PersistentFlags().IntVarP(concurrency, "concurrency", "C", runtime.NumCPU(), "並行実行数。デフォルトはCPU数。")
}

// SetupCpuProf はcpu profileの取得を設定する
func SetupCpuProf(cmd *cobra.Command, prof *bool, path *string) {
	cmd.PersistentFlags().BoolVar(prof, "cpuprof", false, "cpuプロファイルの取得")
	cmd.PersistentFlags().StringVar(path, "cpuout", "", "cpuプロファイルの出力ファイルパス。")
}

// SetupIntervalCpuProf は5分毎のcpu profileの取得を設定する（ワーカー用）
func SetupIntervalCpuProf(cmd *cobra.Command, prof *bool) {
	cmd.PersistentFlags().BoolVar(prof, "interval-cpuprof", false, "5分毎のcpuプロファイルの取得")
}

// SetupIntervalMemProf は5分毎のmem profileの取得を設定する（ワーカー用）
func SetupIntervalMemProf(cmd *cobra.Command, prof *bool) {
	cmd.PersistentFlags().BoolVar(prof, "interval-memprof", false, "5分毎のmemプロファイルの取得")
}

// SetupDisableSignalHandle はデバッグ用のシグナルハンドラを無効化を設定する。
func SetupDisableSignalHandle(cmd *cobra.Command, disableHandle *bool) {
	cmd.PersistentFlags().BoolVar(disableHandle, "local-debug-signal-insensitive", false, "（debug用）localでシグナルハンドラを無効化")
}
