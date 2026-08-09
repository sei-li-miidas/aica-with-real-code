package jobtype

import (
	"aica/api/domain/jobtype"
	"errors"
	"testing"

	"github.com/stretchr/testify/assert"
)

type stubByNatureRepo struct {
	searchByNature func(wantedNatures []string, unwantedNatures []string, minNatureScore float32, minJobTypeScore float32, maxPriorExperienceRequired float32) ([]*jobtype.JobTypeSearchResult, error)
}

func (r *stubByNatureRepo) SearchByNature(wantedNatures []string, unwantedNatures []string, minNatureScore float32, minJobTypeScore float32, maxPriorExperienceRequired float32) ([]*jobtype.JobTypeSearchResult, error) {
	return r.searchByNature(wantedNatures, unwantedNatures, minNatureScore, minJobTypeScore, maxPriorExperienceRequired)
}

func TestSearchJobTypesByNatureUseCase(t *testing.T) {
	t.Run("コンストラクタ", func(t *testing.T) {
		uc := NewSearchJobTypesByNatureUseCaseWithRepository(nil, &stubByNatureRepo{})
		assert.NotNil(t, uc)
	})

	t.Run("Executeが成功する場合", func(t *testing.T) {
		repo := &stubByNatureRepo{
			searchByNature: func(wantedNatures []string, unwantedNatures []string, minNatureScore float32, minJobTypeScore float32, maxPriorExperienceRequired float32) ([]*jobtype.JobTypeSearchResult, error) {
				assert.Equal(t, []string{"営業"}, wantedNatures)
				assert.Equal(t, []string{"夜勤"}, unwantedNatures)
				assert.Equal(t, float32(0.6), minNatureScore)
				assert.Equal(t, float32(0.7), minJobTypeScore)
				assert.Equal(t, float32(0.8), maxPriorExperienceRequired)
				return []*jobtype.JobTypeSearchResult{{ID: 1, Name: "法人営業"}}, nil
			},
		}
		minNature := float32(0.6)
		minJobType := float32(0.7)
		maxPrior := float32(0.8)
		uc := NewSearchJobTypesByNatureUseCaseWithRepository(nil, repo)
		res, err := uc.Execute(&SearchJobTypesByNatureRequest{
			JobNaturePreferences: []*JobNaturePreference{
				{JobNature: "営業", Preference: Wanted},
				{JobNature: "夜勤", Preference: Unwanted},
				{JobNature: "残業", Preference: Whatever},
			},
			MinNatureScore:             &minNature,
			MinJobTypeScore:            &minJobType,
			MaxPriorExperienceRequired: &maxPrior,
		})
		assert.NoError(t, err)
		assert.Len(t, res, 1)
		assert.Equal(t, "法人営業", res[0].Name)
	})

	t.Run("Executeがエラーを返す場合", func(t *testing.T) {
		repo := &stubByNatureRepo{
			searchByNature: func([]string, []string, float32, float32, float32) ([]*jobtype.JobTypeSearchResult, error) {
				return nil, errors.New("failed")
			},
		}
		minNature := float32(0.6)
		minJobType := float32(0.7)
		maxPrior := float32(0.8)
		uc := NewSearchJobTypesByNatureUseCaseWithRepository(nil, repo)
		res, err := uc.Execute(&SearchJobTypesByNatureRequest{
			JobNaturePreferences:       []*JobNaturePreference{},
			MinNatureScore:             &minNature,
			MinJobTypeScore:            &minJobType,
			MaxPriorExperienceRequired: &maxPrior,
		})
		assert.Nil(t, res)
		assert.EqualError(t, err, "failed")
	})
}
