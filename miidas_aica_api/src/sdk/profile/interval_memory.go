package profile

import (
	"os"
	"path/filepath"
	"runtime/pprof"
	"time"
)

const StandardMemoryProfileFileName = "mem.pprof"

type (
	IntervalMemoryProfiler interface {
		Start()
		Stop()
	}

	intervalMemoryProfiler struct {
		cfg     *IntervalMemoryProfileConfig
		stopper chan bool
	}

	IntervalMemoryProfileConfig struct {
		apiName  string
		interval time.Duration // 取得する間隔
		fileName string
	}

	IntervalMemoryProfileConfigure func(config *IntervalMemoryProfileConfig)
)

// NewIntervalMemoryProfiler は定期的にメモリプロファイルを取得します。
// default値：インターバルが5分、ファイル名はmem.pprofのYYYYMMDD_hhmmssを付与。
func NewIntervalMemoryProfiler(apiName string, configure ...IntervalMemoryProfileConfigure) IntervalMemoryProfiler {
	cfg := IntervalMemoryProfileConfig{
		apiName:  apiName,
		interval: time.Minute * 5,
		fileName: StandardMemoryProfileFileName,
	}
	for _, c := range configure {
		c(&cfg)
	}
	if cfg.interval < time.Minute { // 最短を一分間隔に調整
		cfg.interval = time.Minute
	}
	return &intervalMemoryProfiler{
		cfg:     &cfg,
		stopper: make(chan bool),
	}
}

// Start は定期的なプロファイル取得を開始します。
func (p intervalMemoryProfiler) Start() {
	tk := time.NewTicker(p.cfg.interval)
	go func() {
		for {
			select {
			case t := <-tk.C:
				_ = p.write(t, hashValue) // しくじることもあるが無視
			case <-p.stopper:
				return
			}
		}
	}()
}

// write はプロファイル結果をファイルに書き込みます
func (p intervalMemoryProfiler) write(t time.Time, hashValue string) error {
	f := genFileName(p.cfg.apiName, p.cfg.fileName, t, hashValue)
	fullPath := filepath.Join(createAndGetOutputDir(getRootDir(), genChildDir(t)), f)
	w, err := os.OpenFile(fullPath, os.O_RDWR|os.O_CREATE, 0666)
	if err != nil {
		return err
	}
	defer func() {
		_ = w.Close()
	}()
	if err := pprof.WriteHeapProfile(w); err != nil {
		return err
	}
	return nil
}

// Stop は定期的なプロファイル取得をやめます。
//
// NOTE:一応停止を作りましたが、プロセスを止めることが多いと思うので使わなくても大丈夫のはず。
func (p intervalMemoryProfiler) Stop() {
	p.stopper <- true
}
