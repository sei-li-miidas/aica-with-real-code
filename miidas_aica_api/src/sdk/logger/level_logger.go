package logger

import (
	"io"

	"github.com/rs/zerolog"
)

// LevelLogger はレベル付きロガー
// Info("メッセージ", "user_id", userID, "position_id", positionID) で
// {"level": "info", ..中略.. "message":"メッセージ", "user_id": 1, "position_id": 2} がロギングされる
type LevelLogger interface {
	// Info Infoレベルのログを出力します。...any は key, val のペアで指定
	Info(string, ...any)

	// Warn Warnレベルのログを出力します。...any は key, val のペアで指定
	Warn(string, ...any)

	// Error Errorレベルのログを出力します。...any は key, val のペアで指定
	Error(string, ...any)

	// Fatal Fatalレベルのログを出力し、os.Exitします。...any は key, val のペアで指定
	Fatal(string, ...any)
}

type Config struct {
	NeedCaller               bool
	OutputLevel              zerolog.Level
	Category                 string
	Writer                   io.Writer
	CallerWithSkipFrameCount int
}

type Configure func(*Config)

// newZeroLogger ロガーの実体の作成
func newZeroLogger(cfg Config) zerolog.Logger {
	zerolog.TimeFieldFormat = "2006-01-02 15:04:05.000"
	l := zerolog.New(cfg.Writer).With().Logger()
	l = l.Level(cfg.OutputLevel)
	if cfg.NeedCaller {
		l = l.With().CallerWithSkipFrameCount(cfg.CallerWithSkipFrameCount).Logger()
	}
	if cfg.Category != "" {
		l = l.With().Str("category", cfg.Category).Logger()
	}
	return l
}

type levelLogger struct {
	logger zerolog.Logger
}

func (l levelLogger) Info(msg string, keyvals ...any) {
	print(l.logger.Info, msg, keyvals...)
}

func (l levelLogger) Warn(msg string, keyvals ...any) {
	print(l.logger.Warn, msg, keyvals...)
}

func (l levelLogger) Error(msg string, keyvals ...any) {
	print(l.logger.Error, msg, keyvals...)
}

func (l levelLogger) Fatal(msg string, keyvals ...any) {
	fatal := func() *zerolog.Event {
		return l.logger.WithLevel(zerolog.FatalLevel)
	}
	print(fatal, msg, keyvals...)
}
