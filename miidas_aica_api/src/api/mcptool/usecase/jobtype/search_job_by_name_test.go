package jobtype

import (
	"aica/api/domain/jobtype"
	"errors"
	"testing"

	"github.com/stretchr/testify/assert"
)

type stubByNameRepo struct {
	getMultipleByNames func(names []string) ([]*jobtype.JobTypeSmall, error)
}

func (r *stubByNameRepo) GetMultipleByNames(names []string) ([]*jobtype.JobTypeSmall, error) {
	return r.getMultipleByNames(names)
}

func TestSearchJobTypesByNameUseCase(t *testing.T) {
	t.Run("コンストラクタ", func(t *testing.T) {
		uc := NewSearchJobTypesByNameUseCaseWithRepository(nil, &stubByNameRepo{})
		assert.NotNil(t, uc)
	})

	t.Run("Executeが成功する場合", func(t *testing.T) {
		uc := NewSearchJobTypesByNameUseCaseWithRepository(nil, &stubByNameRepo{
			getMultipleByNames: func(names []string) ([]*jobtype.JobTypeSmall, error) {
				assert.Equal(t, []string{"A"}, names)
				return []*jobtype.JobTypeSmall{{ID: 1, Name: "A"}}, nil
			},
		})
		res, err := uc.Execute([]string{"A"})
		assert.NoError(t, err)
		assert.Len(t, res, 1)
		assert.Equal(t, "A", res[0].Name)
	})

	t.Run("Executeがエラーを返す場合", func(t *testing.T) {
		uc := NewSearchJobTypesByNameUseCaseWithRepository(nil, &stubByNameRepo{
			getMultipleByNames: func(_ []string) ([]*jobtype.JobTypeSmall, error) {
				return nil, errors.New("failed")
			},
		})
		res, err := uc.Execute([]string{"A"})
		assert.Nil(t, res)
		assert.EqualError(t, err, "failed")
	})
}
