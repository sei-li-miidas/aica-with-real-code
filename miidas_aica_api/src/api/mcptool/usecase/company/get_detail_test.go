package company

import (
	"aica/api/domain/public/master"
	uabusiness "aica/api/domain/user/apply/business"
	uacompany "aica/api/domain/user/apply/company"
	uaposition "aica/api/domain/user/apply/position"
	merr "aica/api/sdk/error"
	"errors"
	"reflect"
	"testing"
	"unsafe"

	"github.com/stretchr/testify/assert"
)

type stubLogger struct{}

func (l *stubLogger) Info(string, ...any)  {}
func (l *stubLogger) Warn(string, ...any)  {}
func (l *stubLogger) Error(string, ...any) {}
func (l *stubLogger) Fatal(string, ...any) {}

type stubReadPositionRepo struct {
	getCompanyID func(id uaposition.ID) (*uacompany.ID, error)
}

func (s *stubReadPositionRepo) GetCompanyID(id uaposition.ID) (*uacompany.ID, error) {
	return s.getCompanyID(id)
}

type stubReadCompanyRepo struct {
	get func(id uacompany.ID) (*uacompany.Company, error)
}

func (s *stubReadCompanyRepo) Get(id uacompany.ID) (*uacompany.Company, error) {
	return s.get(id)
}

type stubReadBusinessRepo struct {
	getByCompanyID func(companyID uacompany.ID) ([]uabusiness.Business, error)
}

func (s *stubReadBusinessRepo) GetByCompanyID(companyID uacompany.ID) ([]uabusiness.Business, error) {
	return s.getByCompanyID(companyID)
}

type stubPrefectureProvider struct {
	prefectureMap master.PrefectureMap
}

func (s *stubPrefectureProvider) PrefectureMap() master.PrefectureMap {
	return s.prefectureMap
}

func setMasterProviderCacheForTest(cache *master.Cache) {
	provider := master.Provider()
	v := reflect.ValueOf(provider).Elem().FieldByName("cache")
	reflect.NewAt(v.Type(), unsafe.Pointer(v.UnsafeAddr())).Elem().Set(reflect.ValueOf(cache))
}

func TestGetDetailUseCase_Execute(t *testing.T) {
	setMasterProviderCacheForTest(&master.Cache{
		TraitCompanyOptions: map[master.MasterTraitCompanyID][]*master.TraitCompanyOption{},
	})
	prefMap := master.PrefectureMap{
		13: &master.Prefecture{ID: 13, Name: "東京都"},
	}

	t.Run("position repo error", func(t *testing.T) {
		uc := NewGetDetailUseCaseWithRepositories(
			&stubLogger{},
			&stubReadPositionRepo{getCompanyID: func(uaposition.ID) (*uacompany.ID, error) { return nil, errors.New("failed") }},
			&stubReadCompanyRepo{},
			&stubReadBusinessRepo{},
			&stubPrefectureProvider{prefectureMap: prefMap},
		)
		res, err := uc.Execute(1)
		assert.Nil(t, res)
		assert.True(t, merr.Is(err, merr.ErrInternalServer))
	})

	t.Run("position not found", func(t *testing.T) {
		uc := NewGetDetailUseCaseWithRepositories(
			&stubLogger{},
			&stubReadPositionRepo{getCompanyID: func(uaposition.ID) (*uacompany.ID, error) { return nil, nil }},
			&stubReadCompanyRepo{},
			&stubReadBusinessRepo{},
			&stubPrefectureProvider{prefectureMap: prefMap},
		)
		res, err := uc.Execute(1)
		assert.Nil(t, res)
		assert.True(t, merr.Is(err, merr.ErrResourceNotFound))
	})

	t.Run("company repo error", func(t *testing.T) {
		id := uacompany.ID(10)
		uc := NewGetDetailUseCaseWithRepositories(
			&stubLogger{},
			&stubReadPositionRepo{getCompanyID: func(uaposition.ID) (*uacompany.ID, error) { return &id, nil }},
			&stubReadCompanyRepo{get: func(uacompany.ID) (*uacompany.Company, error) { return nil, errors.New("failed") }},
			&stubReadBusinessRepo{},
			&stubPrefectureProvider{prefectureMap: prefMap},
		)
		res, err := uc.Execute(1)
		assert.Nil(t, res)
		assert.True(t, merr.Is(err, merr.ErrInternalServer))
	})

	t.Run("company not found", func(t *testing.T) {
		id := uacompany.ID(10)
		uc := NewGetDetailUseCaseWithRepositories(
			&stubLogger{},
			&stubReadPositionRepo{getCompanyID: func(uaposition.ID) (*uacompany.ID, error) { return &id, nil }},
			&stubReadCompanyRepo{get: func(uacompany.ID) (*uacompany.Company, error) { return nil, nil }},
			&stubReadBusinessRepo{},
			&stubPrefectureProvider{prefectureMap: prefMap},
		)
		res, err := uc.Execute(1)
		assert.Nil(t, res)
		assert.True(t, merr.Is(err, merr.ErrResourceNotFound))
	})

	t.Run("company withdrew", func(t *testing.T) {
		id := uacompany.ID(10)
		uc := NewGetDetailUseCaseWithRepositories(
			&stubLogger{},
			&stubReadPositionRepo{getCompanyID: func(uaposition.ID) (*uacompany.ID, error) { return &id, nil }},
			&stubReadCompanyRepo{
				get: func(uacompany.ID) (*uacompany.Company, error) {
					return &uacompany.Company{
						IsSearchable: true,
						Detail:       uacompany.Detail{Withdrew: true, Address: &uacompany.Address{}},
					}, nil
				},
			},
			&stubReadBusinessRepo{},
			&stubPrefectureProvider{prefectureMap: prefMap},
		)
		res, err := uc.Execute(1)
		assert.Nil(t, res)
		assert.True(t, merr.Is(err, merr.ErrResourceNotFound))
	})

	t.Run("business repo error", func(t *testing.T) {
		id := uacompany.ID(10)
		uc := NewGetDetailUseCaseWithRepositories(
			&stubLogger{},
			&stubReadPositionRepo{getCompanyID: func(uaposition.ID) (*uacompany.ID, error) { return &id, nil }},
			&stubReadCompanyRepo{
				get: func(uacompany.ID) (*uacompany.Company, error) {
					return &uacompany.Company{
						ID:           id,
						IsSearchable: true,
						Detail:       uacompany.Detail{Address: &uacompany.Address{PrefectureID: 13, Address: "新宿"}},
					}, nil
				},
			},
			&stubReadBusinessRepo{getByCompanyID: func(uacompany.ID) ([]uabusiness.Business, error) { return nil, errors.New("failed") }},
			&stubPrefectureProvider{prefectureMap: prefMap},
		)
		res, err := uc.Execute(1)
		assert.Nil(t, res)
		assert.True(t, merr.Is(err, merr.ErrInternalServer))
	})

	t.Run("success", func(t *testing.T) {
		id := uacompany.ID(10)
		uc := NewGetDetailUseCaseWithRepositories(
			&stubLogger{},
			&stubReadPositionRepo{getCompanyID: func(uaposition.ID) (*uacompany.ID, error) { return &id, nil }},
			&stubReadCompanyRepo{
				get: func(uacompany.ID) (*uacompany.Company, error) {
					return &uacompany.Company{
						ID:           id,
						IsSearchable: true,
						Detail: uacompany.Detail{
							Name:    "Company",
							Address: &uacompany.Address{PrefectureID: 13, Address: "新宿"},
						},
					}, nil
				},
			},
			&stubReadBusinessRepo{
				getByCompanyID: func(uacompany.ID) ([]uabusiness.Business, error) {
					return []uabusiness.Business{
						{Detail: uabusiness.Detail{Name: "Biz1"}},
						{Detail: uabusiness.Detail{Name: "Biz2"}},
					}, nil
				},
			},
			&stubPrefectureProvider{prefectureMap: prefMap},
		)
		res, err := uc.Execute(1)
		assert.NoError(t, err)
		assert.NotNil(t, res)
		assert.Equal(t, "Company", res.Name)
		assert.Equal(t, []string{"Biz1", "Biz2"}, res.BusinessNames)
	})
}

func TestCompanyHelpers(t *testing.T) {
	assert.Equal(t, "https://example.com", showWebsite("https://example.com"))
	assert.Equal(t, "", showWebsite("not-url"))

	prefMap := master.PrefectureMap{13: &master.Prefecture{ID: 13, Name: "東京都"}}
	assert.Equal(t, "東京都", showPrefecture(13, prefMap))
	assert.Equal(t, "東京都新宿", showAddress(&uacompany.Address{PrefectureID: 13, Address: "新宿"}, prefMap))

	assert.Equal(t, []string{}, showBusinessNames([]string{"one"}))
	assert.Equal(t, []string{"one", "two"}, showBusinessNames([]string{"one", "two"}))

	docs := showDocument([]*uacompany.Document{{ID: 1, Label: "a"}})
	assert.Len(t, docs, 1)
	assert.Equal(t, 1, docs[0].ID)
	assert.Equal(t, "a", docs[0].Label)
}
