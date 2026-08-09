package logger

import (
	"io"
	"os"
	"strings"
	"unicode/utf8"

	"github.com/rs/zerolog"
)

const (
	defaultBytesLimit = 9_999_900
	jsonSep           = ",\""
	jsonStart         = "{"
	jsonEnd           = "}"
	newLine           = "\n"
	dots              = "..."
	comma             = ","
	cutMessage        = "This log is cut by BytesLimitWriter."
	cutJson           = `"cut":"` + cutMessage + `"`
)

// DefaultWriter は通常利用のio.Writerを返します。os.Stdoutです。
func DefaultWriter() io.Writer {
	return newBytesLimitWriter(zerolog.SyncWriter(os.Stdout), defaultBytesLimit)
}

// bytesLimitWriter 出力内容をバイト数で制限する
type bytesLimitWriter struct {
	bytesLimit int
	w          io.Writer
}

// newBytesLimitWriter コンストラクタ
func newBytesLimitWriter(w io.Writer, bytesLimit int) bytesLimitWriter {
	return bytesLimitWriter{
		bytesLimit: bytesLimit,
		w:          w,
	}
}

// Write io.Writerの実装。出力するログを制限して、渡されたロガーで実際のログを出力。
func (w bytesLimitWriter) Write(b []byte) (n int, err error) {
	b = cut(b, w.bytesLimit)
	return w.w.Write(b)
}

// cut ログ出力をバイト数で制限する。json形式の場合は、綺麗に整形できるようにする。
func cut(b []byte, bytesLimit int) []byte {
	if len(b) > bytesLimit {
		// 改行有無判定。LevelLoggerを用いている場合はロガー側で必ず付与されるが念の為。
		var needNewLine bool
		if string(b[len(b)-1:]) == newLine {
			needNewLine = true
		}

		s := string(b)[:bytesLimit]

		if strings.HasPrefix(s, jsonStart) {
			// {始まりはjson扱いとする
			// jsonのkey-valueの切り替わりで区切る
			idx := strings.LastIndex(s, jsonSep)
			if idx == -1 {
				// 最初のkey-valueで切れてしまった場合
				s = jsonStart + cutJson + jsonEnd
			} else {
				// 切り出された旨のメッセージを付与してjsonの形に再整形
				s = s[:idx] + comma + cutJson + jsonEnd
			}
		} else {
			// jsonでない場合は、指定位置で切り出して出力
			s = cutToValidRune(s) + dots + cutMessage
		}

		if needNewLine {
			s = s + newLine
		}
		b = []byte(s)
	}
	return b
}

// cutToValidRune 全角文字などで、有効な文字で切り出せなかった場合は、切り出し位置を１バイト前にする。
func cutToValidRune(s string) string {
	if utf8.ValidString(s) {
		// 普通に切れたらそのまま渡す
		return s
	} else {
		// だめだったら1バイト削って再チャレンジ
		s = s[:len(s)-1]
		return cutToValidRune(s)
	}
}
