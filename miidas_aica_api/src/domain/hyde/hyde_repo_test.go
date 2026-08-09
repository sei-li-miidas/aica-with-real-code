package hyde

import (
	tmock "aica/api/api/mcptool/testutil/mock"
	"aica/api/domain/provider"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestNewHyDERepository_OpenAI(t *testing.T) {
	logger := &tmock.MockLogger{}

	repoOpenAI, err := NewHyDERepository(provider.ProviderOpenAI, logger)
	assert.NoError(t, err)
	assert.IsType(t, OpenAIHyDERepository{}, repoOpenAI)
}

func TestNewHyDERepository_UnsupportedProvider(t *testing.T) {
	logger := &tmock.MockLogger{}

	repoGemini, err := NewHyDERepository(provider.ProviderGemini, logger)
	assert.Error(t, err)
	assert.Nil(t, repoGemini)

	repoBedrock, err := NewHyDERepository(provider.ProviderBedrock, logger)
	assert.Error(t, err)
	assert.Nil(t, repoBedrock)
}
