package cli

import (
	"errors"
	"sync"

	mlogger "aica/api/sdk/logger"
)

var (
	// batchLogger はグローバルなロガー
	batchLogger           mlogger.LevelLogger
	batchLoggerConfigures []mlogger.Configure
	setupBatchOnce        sync.Once
)

var (
	ErrLoggerNotInitialize = errors.New("logger not initialized")
)

// SetupBatchLogger はバッチ用のロガーの初期化
func SetupBatchLogger(jobID string, configures ...mlogger.Configure) {
	setupBatchOnce.Do(func() {
		batchLoggerConfigures = configures
		batchLogger = mlogger.NewBatchContext(configures...).NewLogger(jobID)
	})
}

// UpdateJobIDOfBatchLogger は JobID を洗い替えてバッチ用のロガーを再作成する
func UpdateJobIDOfBatchLogger(jobID string) {
	if batchLogger == nil {
		panic(ErrLoggerNotInitialize)
	}
	batchLogger = mlogger.NewBatchContext(batchLoggerConfigures...).NewLogger(jobID)
}

// GetBatchLogger はバッチ用のグローバルなロガーの取得
func GetBatchLogger() mlogger.LevelLogger {
	if batchLogger == nil {
		panic(ErrLoggerNotInitialize)
	}
	return batchLogger
}
