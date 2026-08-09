package mysql

import (
	"fmt"
	"strconv"
	"time"

	"github.com/go-sql-driver/mysql"
)

// Standard config options
const (
	// StandardCharset 標準で設定するキャラクターセット
	StandardCharset = "utf8mb4"
)

type (
	// ConfigParam 接続時のパラメータ設定関数
	ConfigParam func(map[string]string)
)

// NewConfig mysql接続のコンフィギュレーションを作成する
func NewConfig(user, password, host string, port int, opts ...ConfigParam) *mysql.Config {
	c := mysql.NewConfig()
	c.User = user
	c.Passwd = password
	c.Addr = fmt.Sprintf("%s:%d", host, port)
	c.Net = "tcp"
	c.MaxAllowedPacket = 0 // apply server side setting
	c.AllowNativePasswords = true
	c.ParseTime = true
	c.Loc = time.Local
	c.Params = params(opts...)
	return c
}

// StdConfigParams 標準のパラメータ
func StdConfigParams() []ConfigParam {
	return []ConfigParam{
		Charset(StandardCharset),
	}
}

// Charset charsetパラメータの設定
func Charset(charset string) ConfigParam {
	return func(params map[string]string) {
		params["charset"] = charset
	}
}

// MaxExecuteTime max_execute_timeパラメータの設定
// dはミリセカンド単位です。
func MaxExecuteTime(d time.Duration) ConfigParam {
	return func(params map[string]string) {
		params["max_execution_time"] = strconv.FormatInt(d.Milliseconds(), 10)
	}
}

func params(params ...ConfigParam) map[string]string {
	ret := make(map[string]string, len(params))
	for _, param := range params {
		param(ret)
	}
	return ret
}
