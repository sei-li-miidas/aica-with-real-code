package vectorizer

import (
	tmock "aica/api/api/mcptool/testutil/mock"
	"aica/api/domain/provider"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestNewVectorizerRepository(t *testing.T) {
	logger := &tmock.MockLogger{}

	t.Run("openai", func(t *testing.T) {
		repo, err := NewVectorizerRepository(provider.ProviderOpenAI, logger)
		assert.NoError(t, err)
		assert.IsType(t, &OpenAIVectorizerRepository{}, repo)
	})

	t.Run("bedrock", func(t *testing.T) {
		repo, err := NewVectorizerRepository(provider.ProviderBedrock, logger)
		assert.NoError(t, err)
		assert.IsType(t, &BedrockVectorizerRepository{}, repo)
	})

	t.Run("unknown", func(t *testing.T) {
		repo, err := NewVectorizerRepository(provider.Provider("unknown"), logger)
		assert.Error(t, err)
		assert.Nil(t, repo)
	})
}
