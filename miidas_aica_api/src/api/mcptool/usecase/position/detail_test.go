package position

import (
	"context"
	"errors"
	"os"
	"testing"

	tmock "aica/api/api/mcptool/testutil/mock"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	"aica/api/domain/public/master"
	mcompany "aica/api/domain/user/apply/company"
	mposition "aica/api/domain/user/apply/position"
	mvo "aica/api/domain/user/apply/vo"

	"github.com/stretchr/testify/assert"
)

func TestDetailUseCase_Execute_BasicBranches(t *testing.T) {
	t.Run("不正な雇用形態の場合はNotFoundを返す", func(t *testing.T) {
		uc := NewDetailUseCase(
			&detailPositionRepoStub{get: func(id mposition.ID) (*mposition.Position, error) {
				return &mposition.Position{
					ID:        id,
					CompanyID: 1,
					Detail: mposition.Detail{
						EmploymentType: &mvo.ValueText{ID: 999},
					},
				}, nil
			}},
			&detailCompanyRepoStub{get: func(id mcompany.ID) (*mcompany.Company, error) {
				return &mcompany.Company{}, nil
			}},
			master.Provider(),
			&tmock.MockLogger{},
		)

		got, err := uc.Execute(context.Background(), 10)
		assert.Nil(t, got)
		assert.Error(t, err)
	})

	t.Run("業務委託経路でレスポンスを構築できる", func(t *testing.T) {
		setMasterCacheProviderCache(master.Provider(), &master.Cache{
			SpotJobRequests:      master.SpotJobRequests{},
			SpotExpLevels:        master.SpotExpLevels{},
			Prefectures:          master.Prefectures{},
			Cities:               master.Cities{},
			TraitPositionOptions: map[master.MasterTraitPositionID][]*master.TraitPositionOption{},
		})

		uc := NewDetailUseCase(
			&detailPositionRepoStub{get: func(id mposition.ID) (*mposition.Position, error) {
				return &mposition.Position{
					ID:        id,
					CompanyID: 1,
					Detail: mposition.Detail{
						EmploymentType: &mvo.ValueText{ID: int(master.PositionEmploymentTypeIDOutsourcing)},
					},
				}, nil
			}},
			&detailCompanyRepoStub{get: func(id mcompany.ID) (*mcompany.Company, error) {
				return &mcompany.Company{
					ID: id,
					Detail: mcompany.Detail{
						Name:     "c1",
						Withdrew: true,
					},
				}, nil
			}},
			master.Provider(),
			&tmock.MockLogger{},
		)

		got, err := uc.Execute(context.Background(), 11)
		assert.NoError(t, err)
		assert.NotNil(t, got)
		assert.NotNil(t, got.Company)
	})
}

func TestDetailUseCase_GetSharedInfo_AndHelpers(t *testing.T) {
	uc := NewDetailUseCase(
		&detailPositionRepoStub{get: func(id mposition.ID) (*mposition.Position, error) {
			return nil, errors.New("position repo error")
		}},
		&detailCompanyRepoStub{get: func(id mcompany.ID) (*mcompany.Company, error) {
			return &mcompany.Company{}, nil
		}},
		master.Provider(),
		&tmock.MockLogger{},
	)
	_, err := uc.getSharedInfo(1)
	assert.Error(t, err)

	uc = NewDetailUseCase(
		&detailPositionRepoStub{get: func(id mposition.ID) (*mposition.Position, error) {
			return nil, nil
		}},
		&detailCompanyRepoStub{get: func(id mcompany.ID) (*mcompany.Company, error) {
			return &mcompany.Company{}, nil
		}},
		master.Provider(),
		&tmock.MockLogger{},
	)
	_, err = uc.getSharedInfo(2)
	assert.Error(t, err)

	uc = NewDetailUseCase(
		&detailPositionRepoStub{get: func(id mposition.ID) (*mposition.Position, error) {
			return &mposition.Position{ID: id, CompanyID: 99}, nil
		}},
		&detailCompanyRepoStub{get: func(id mcompany.ID) (*mcompany.Company, error) {
			return nil, errors.New("company repo error")
		}},
		master.Provider(),
		&tmock.MockLogger{},
	)
	_, err = uc.getSharedInfo(3)
	assert.Error(t, err)

	setMasterCacheProviderCache(master.Provider(), &master.Cache{
		SpotJobRequests:      master.SpotJobRequests{},
		SpotExpLevels:        master.SpotExpLevels{},
		Prefectures:          master.Prefectures{},
		Cities:               master.Cities{},
		TraitPositionOptions: map[master.MasterTraitPositionID][]*master.TraitPositionOption{},
	})
	res := buildDetailPosition(
		&mposition.Position{},
		&mcompany.Company{Detail: mcompany.Detail{Withdrew: false}},
		nil,
		nil,
		master.Provider(),
	)
	assert.NotNil(t, res)
}

func TestShowImages_Branches(t *testing.T) {
	assert.Nil(t, showImages(nil))
	assert.Nil(t, showImages(mposition.Images{}))

	// Keep this branch deterministic regardless of envFile-loaded variables.
	old, existed := os.LookupEnv("MIIDAS_S3_USER_ASSETS_ENDPOINT")
	_ = os.Unsetenv("MIIDAS_S3_USER_ASSETS_ENDPOINT")
	defer func() {
		if existed {
			_ = os.Setenv("MIIDAS_S3_USER_ASSETS_ENDPOINT", old)
		} else {
			_ = os.Unsetenv("MIIDAS_S3_USER_ASSETS_ENDPOINT")
		}
	}()
	assert.Nil(t, showImages(mposition.Images{{DisplayType: 1, FilePath: "x/y.png"}}))

	t.Setenv("MIIDAS_S3_USER_ASSETS_ENDPOINT", "assets.example.com")
	got := showImages(mposition.Images{
		{DisplayType: 2, FilePath: "foo/bar.png"},
	})
	if assert.Len(t, got, 1) {
		assert.Equal(t, 2, got[0].DisplayType)
		assert.Equal(t, "https://assets.example.com/foo/bar.png", got[0].URL)
	}
}

func TestDetailUseCase_Execute_EmployeeAndContractPaths(t *testing.T) {
	setMasterCacheProviderCache(master.Provider(), &master.Cache{
		SpotJobRequests:      master.SpotJobRequests{},
		SpotExpLevels:        master.SpotExpLevels{},
		Prefectures:          master.Prefectures{},
		Cities:               master.Cities{},
		TraitPositionOptions: map[master.MasterTraitPositionID][]*master.TraitPositionOption{},
	})

	tests := []struct {
		name           string
		employmentType master.PositionEmploymentTypeID
		incomeFrom     *int
	}{
		{
			name:           "employee with income from nil",
			employmentType: master.PositionEmploymentTypeIDEmployee,
			incomeFrom:     nil,
		},
		{
			name:           "contract with income from set",
			employmentType: master.PositionEmploymentTypeIDContract,
			incomeFrom:     loPtr(400),
		},
	}

	runCase := func(tt struct {
		name           string
		employmentType master.PositionEmploymentTypeID
		incomeFrom     *int
	}) {
		t.Run(tt.name, func(t *testing.T) {
			uc := NewDetailUseCase(
				&detailPositionRepoStub{get: func(id mposition.ID) (*mposition.Position, error) {
					return &mposition.Position{
						ID:        id,
						CompanyID: 1,
						Detail: mposition.Detail{
							EmploymentType: &mvo.ValueText{ID: int(tt.employmentType)},
							GuaranteedIncome: &mposition.GuaranteedIncome{
								BulkIncomeFrom: tt.incomeFrom,
								BulkIncomeTo:   loPtr(500),
							},
						},
					}, nil
				}},
				&detailCompanyRepoStub{get: func(id mcompany.ID) (*mcompany.Company, error) {
					return &mcompany.Company{
						ID: id,
						Detail: mcompany.Detail{
							Name:     "c1",
							Withdrew: false,
						},
					}, nil
				}},
				master.Provider(),
				&tmock.MockLogger{},
			)

			got, err := uc.Execute(context.Background(), 100)
			assert.NoError(t, err)
			assert.NotNil(t, got)
			assert.NotNil(t, got.Position)
		})
	}

	runCase(tests[0])
	runCase(tests[1])
}

func TestDetailUseCase_Execute_GetSharedInfoError(t *testing.T) {
	uc := NewDetailUseCase(
		&detailPositionRepoStub{get: func(id mposition.ID) (*mposition.Position, error) {
			return nil, errors.New("position get failed")
		}},
		&detailCompanyRepoStub{get: func(id mcompany.ID) (*mcompany.Company, error) {
			return &mcompany.Company{}, nil
		}},
		master.Provider(),
		&tmock.MockLogger{},
	)
	got, err := uc.Execute(context.Background(), 1)
	assert.Nil(t, got)
	assert.Error(t, err)
}

func TestBuildDetailResponse_NotNil(t *testing.T) {
	got := buildDetailResponse(&pmodel.DetailPosition{}, &pmodel.DetailCompany{})
	assert.NotNil(t, got)
}
