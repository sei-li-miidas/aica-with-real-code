package gormio

import (
	"context"
	"fmt"
	"io"
	"time"

	"gorm.io/gorm/utils"

	"github.com/rs/zerolog"
	"gorm.io/gorm/logger"
)

// Logger gorm.ioのロガーの実装
type Logger struct {
	LogLevel  logger.LogLevel
	Logger    zerolog.Logger
	traceMode bool
}

// NewLogger ロガーの作成
// ログレベルがWarnなのでInfoログが出力されません。
// trace = trueのとき、実行されるSQLをデバッグレベルで出力します。
func NewLogger(w io.Writer, category string, trace bool) logger.Interface {
	return &Logger{
		LogLevel:  logger.Warn,
		Logger:    newZeroLogger(w, category),
		traceMode: trace,
	}
}

func (l *Logger) LogMode(level logger.LogLevel) logger.Interface {
	newLogger := *l
	newLogger.LogLevel = level
	return &newLogger
}

func (l Logger) Info(_ context.Context, msg string, data ...any) {
	if l.LogLevel >= logger.Info {
		l.print(zerolog.InfoLevel, utils.FileWithLineNum(), msg, data...)
	}
}

func (l Logger) Warn(_ context.Context, msg string, data ...any) {
	if l.LogLevel >= logger.Warn {
		l.print(zerolog.WarnLevel, utils.FileWithLineNum(), msg, data...)
	}
}

func (l Logger) Error(_ context.Context, msg string, data ...any) {
	if l.LogLevel >= logger.Error {
		l.print(zerolog.ErrorLevel, utils.FileWithLineNum(), msg, data...)
	}
}

func (l Logger) print(level zerolog.Level, caller string, msg string, data ...any) {
	l.Logger.WithLevel(level).Timestamp().Str("caller", caller).Msg(fmt.Sprintf(msg, data...))
}

func (l Logger) Trace(_ context.Context, begin time.Time, fc func() (string, int64), err error) {
	if l.traceMode {
		elapsed := time.Since(begin)

		var lg *zerolog.Event
		if err != nil {
			lg = l.Logger.Error().Timestamp().Err(err)
		} else {
			lg = l.Logger.Debug().Timestamp()
		}
		lg = lg.Str("caller", utils.FileWithLineNum())
		sql, rows := fc()
		lg = lg.Str("sql", sql).Float64("exec millisec", float64(elapsed.Nanoseconds())/1e6)
		if rows == -1 {
			lg.Send()
		} else {
			lg.Int64("rows", rows).Send()
		}
	}
}

func newZeroLogger(w io.Writer, category string) zerolog.Logger {
	zerolog.TimeFieldFormat = "2006-01-02 15:04:05.000"
	l := zerolog.New(w).With().Logger()
	l = l.With().Str("category", category).Logger()
	return l
}
