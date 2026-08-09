package profile

import (
	"os"
	"os/signal"
	"path/filepath"
	"runtime/pprof"
	"sync"
	"time"
)

const (
	CPUProfilePath = "/var/log/go/cpu.pprof"
)

func init() {
	hashValue = genHash()
}

type CPUProfiler struct {
	path      string
	startOnce sync.Once
	closeOnce sync.Once
	closer    func()
}

func NewCPUProfiler(filePath string) *CPUProfiler {
	return &CPUProfiler{
		path:      filePath,
		startOnce: sync.Once{},
		closeOnce: sync.Once{},
	}
}

func (p *CPUProfiler) Start() *CPUProfiler {
	p.startOnce.Do(func() {
		w, err := os.OpenFile(p.path, os.O_RDWR|os.O_CREATE, 0666)
		if err != nil {
			panic(err)
		}
		_ = pprof.StartCPUProfile(w)
		p.closer = func() {
			pprof.StopCPUProfile()
			_ = w.Close()
		}

		go func() {
			c := make(chan os.Signal, 1)
			signal.Notify(c, os.Interrupt)
			<-c
			p.closer()
			os.Exit(1)
		}()
	})

	return p
}

func (p *CPUProfiler) Stop() {
	if p == nil {
		return
	}
	p.closeOnce.Do(func() {
		p.closer()
	})
}

// DefaultPath はfargateコンテナにマウントされたnfsに出力先ディレクトリを作成し、パスを返却する
func DefaultPath(batchName string, t time.Time) string {
	f := genFileName(batchName, StandardCPUProfileFileName, time.Now(), hashValue)
	return filepath.Join(createAndGetOutputDir(getRootDir(), genChildDir(t)), f)
}
