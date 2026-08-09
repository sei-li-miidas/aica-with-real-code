package service

import (
	"time"

	hydehistory "aica/api/domain/hyde_history"
	"aica/api/sdk/logger"
)

type GenerateHydeTextFunc func(keyword string) (string, error)

type HydeService struct {
	logger      logger.LevelLogger
	historyRepo hydehistory.HydeHistoryFinderAndSaver
}

func NewHydeService(logger logger.LevelLogger, historyRepo hydehistory.HydeHistoryFinderAndSaver) *HydeService {
	return &HydeService{
		logger:      logger,
		historyRepo: historyRepo,
	}
}

// GetOrGenerateHydeText HyDE履歴から取得、もしくは新規生成する
func (s *HydeService) GetOrGenerateHydeText(
	hydeType hydehistory.HydeType,
	keyword string,
	useHydeHistory bool,
	generateFunc GenerateHydeTextFunc,
) (string, error) {
	var hydeText string
	shouldGenerateHyde := true

	if useHydeHistory {
		// HyDE履歴に存在すれば履歴を使用
		hydeTextPtr, err := s.historyRepo.GetHydeText(hydeType, keyword)
		if err != nil {
			s.logger.Error("HyDE履歴の検索に失敗しました。", "keyword", keyword, "error", err)
			return "", err
		}

		if hydeTextPtr != nil {
			hydeText = *hydeTextPtr
			shouldGenerateHyde = false
		}
	}

	if shouldGenerateHyde {
		var err error
		hydeText, err = generateFunc(keyword)
		if err != nil {
			return "", err
		}

		if useHydeHistory {
			// HyDE履歴に保存
			if err := s.historyRepo.Save(&hydehistory.HydeHistory{
				HydeType:   hydeType,
				Keyword:    keyword,
				HydeText:   hydeText,
				LastUsedAt: time.Now(),
			}); err != nil {
				s.logger.Error("HyDE履歴の保存に失敗しました。", "keyword", keyword, "error", err)
				return "", err
			}
		}
	}

	s.logger.Info("HyDE", keyword, hydeText)
	return hydeText, nil
}
