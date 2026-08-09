package position

import (
	"testing"

	"github.com/stretchr/testify/assert"

	tmock "aica/api/api/mcptool/testutil/mock"
	"aica/api/domain/user/apply/position"
)

func TestSummariesUseCase_Execute_Empty(t *testing.T) {
	uc := NewSummariesUseCase(&tmock.MockLogger{}, &mockReadPositionRepository{})
	got, err := uc.Execute([]position.ID{})
	assert.NoError(t, err)
	assert.NotNil(t, got)
	assert.Len(t, got, 0)
}
