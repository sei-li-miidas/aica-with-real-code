package profile

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime/pprof"
	"time"

	"github.com/google/uuid"

	"aica/api/conf"
)

const pprofRootDir = "pprof"

const StandardCPUProfileFileName = "cpu.pprof"

var (
	// 起動前に設定されるハッシュ値。これをファイルに付けることでコンテナごとにユニークなファイル名にする。
	hashValue string
)

func init() {
	hashValue = genHash()
}

type (
	IntervalCPUProfiler interface {
		Start()
		Stop()
	}

	intervalCPUProfiler struct {
		cfg     *IntervalCPUProfileConfig
		stopper chan bool
	}

	IntervalCPUProfileConfig struct {
		apiName  string
		interval time.Duration // 取得する間隔
		duration time.Duration // 取得持続する時間
		fileName string
	}

	IntervalCPUProfileConfigure func(*IntervalCPUProfileConfig)
)

// NewIntervalCPUProfiler は定期的にCPUプロファイルを取得します。
// default値：インターバルが5分、取得持続時間が1分、ファイル名はmem.pprofの末尾にYYYYMMDD_hhmmssを付与。
func NewIntervalCPUProfiler(apiName string, configure ...IntervalCPUProfileConfigure) IntervalCPUProfiler {
	cfg := IntervalCPUProfileConfig{
		apiName:  apiName,
		interval: time.Minute * 5,
		duration: time.Minute * 1,
		fileName: StandardCPUProfileFileName,
	}
	for _, c := range configure {
		c(&cfg)
	}
	if cfg.interval < time.Minute { // 最短を一分間隔に調整
		cfg.interval = time.Minute
	}
	if cfg.interval < cfg.duration { // 取得持続する時間がインターバル以内になるように調整
		cfg.duration = cfg.interval
	}
	return &intervalCPUProfiler{
		cfg:     &cfg,
		stopper: make(chan bool),
	}
}

func (p intervalCPUProfiler) Start() {
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
func (p intervalCPUProfiler) write(t time.Time, hashValue string) error {
	f := genFileName(p.cfg.apiName, p.cfg.fileName, t, hashValue)
	fullPath := filepath.Join(createAndGetOutputDir(getRootDir(), genChildDir(t)), f)
	w, err := os.OpenFile(fullPath, os.O_RDWR|os.O_CREATE, 0666)
	if err != nil {
		return err
	}
	defer func() {
		_ = w.Close()
	}()

	_ = pprof.StartCPUProfile(w)
	<-time.After(p.cfg.duration)
	pprof.StopCPUProfile()
	return nil
}

// Stop は定期的なプロファイル取得をやめます。
//
// NOTE:一応停止を作りましたが、プロセスを止めることが多いと思うので使わなくても大丈夫のはず。
func (p intervalCPUProfiler) Stop() {
	p.stopper <- true
}

// genFileName はファイル名（パスを含まない）を生成します。
func genFileName(apiName, baseName string, t time.Time, hashValue string) string {
	return fmt.Sprintf("%s.%s.%s.%s", apiName, baseName, t.Format("20060102_150405"), hashValue)
}

// genHash はファイル名に付加するハッシュを生成します。
func genHash() string {
	uuidObj, _ := uuid.NewUUID() // まれなのでエラーを無視
	data := []byte("EyiStKgF5gZW73rJAdAtYUG5LfRZPsY8")
	return uuid.NewSHA1(uuidObj, data).String()
}

// createAndGetOutputDir は出力先のディレクトリを作成し、そのパスを返します。
func createAndGetOutputDir(baseDir, childDir string) string {
	ret := filepath.Join(baseDir, childDir)
	_ = os.MkdirAll(ret, 0777)
	return ret
}

// genChildDir は年月日/時のディレクトリパスを返します。
func genChildDir(t time.Time) string {
	y, m, d := t.Date()
	h := t.Hour()
	return fmt.Sprintf("%s/%04d%02d%02d/%02d", pprofRootDir, y, m, d, h)
}

// getRootDir は出力先の
func getRootDir() string {
	return conf.GetAppConfig().Nfs
}
