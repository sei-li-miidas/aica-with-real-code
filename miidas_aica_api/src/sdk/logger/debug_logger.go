package logger

import (
	"github.com/rs/zerolog"
)

type DebugLogger interface {
	Log(msg string, keyvals ...any)
}

func newDebugLogger(cfg Config) zerolog.Logger {
	zerolog.TimeFieldFormat = "2006-01-02 15:04:05.000"
	l := zerolog.New(cfg.Writer).With().Logger()
	if cfg.NeedCaller {
		l = l.Level(zerolog.DebugLevel)
	} else {
		l = l.Level(zerolog.Disabled)
	}

	if cfg.Category != "" {
		l = l.With().Str("category", cfg.Category).Logger()
	}

	return l.With().CallerWithSkipFrameCount(cfg.CallerWithSkipFrameCount).Logger()
}

type debugLogger struct {
	logger zerolog.Logger
}

func (l debugLogger) Log(msg string, keyvals ...any) {
	print(l.logger.Debug, msg, keyvals...)
}
