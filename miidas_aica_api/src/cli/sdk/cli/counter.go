package cli

import (
	"runtime"
	"sync/atomic"
	"time"
)

var (
	aim    uint64 // 処理対象件数
	done   uint64 // 処理実施件数
	memory uint64 // 利用メモリの最大値
)

func SetAim(n uint64) {
	atomic.StoreUint64(&aim, n)
}

func Aim() uint64 {
	return atomic.LoadUint64(&aim)
}

func AddAim(d uint64) uint64 {
	return atomic.AddUint64(&aim, d)
}

func IncAim() uint64 {
	return AddAim(1)
}

func SetDone(n uint64) {
	atomic.StoreUint64(&done, n)
}

func Done() uint64 {
	return atomic.LoadUint64(&done)
}

func AddDone(d uint64) uint64 {
	return atomic.AddUint64(&done, d)
}

func IncDone() uint64 {
	return AddDone(1)
}

func Memory() uint64 {
	return atomic.LoadUint64(&memory)
}

// MemoryMB は利用メモリをMiB(2^20)単位にして返します。
func MemoryMB() uint64 {
	m := Memory()
	return m / (1024 * 1024)
}

// StartRecordingMemoryUsage はメモリ使用量を計測します。
//
// return値は計測を停止する関数です。終了時に実行してください。defer推奨。
func StartRecordingMemoryUsage(sec int64) func() {
	ticker := time.NewTicker(time.Duration(sec) * time.Second)
	go func() {
		var stats runtime.MemStats
		for {
			<-ticker.C
			runtime.ReadMemStats(&stats)
			use := stats.Sys
			if use > memory {
				atomic.StoreUint64(&memory, use)
			}
		}
	}()
	return ticker.Stop
}
