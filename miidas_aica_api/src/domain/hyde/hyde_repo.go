package hyde

import (
	"aica/api/domain/provider"
	"aica/api/sdk/logger"
	"fmt"
)

// HyDE (Hypothetical Document Embedding)を生成するインターフェース
type HyDERepository interface {
	GenerateJobTypeHyDEText(text string) (string, error)
	GenerateIndustryHyDEText(text string) (string, error)
}

func NewHyDERepository(p provider.Provider, logger logger.LevelLogger) (HyDERepository, error) {
	switch p {
	case provider.ProviderOpenAI:
		return NewOpenAIHyDERepository(logger), nil
	default:
		logger.Error("Unknown hyde provider", "provider", p)
		return nil, fmt.Errorf("unknown hyde provider: %s", p)
	}
}
