package business

import (
	"aica/api/domain/public/master"
	uabusiness "aica/api/domain/user/apply/business"
	uacompany "aica/api/domain/user/apply/company"
	uaposition "aica/api/domain/user/apply/position"
	applyVO "aica/api/domain/user/apply/vo"
	userMaster "aica/api/domain/user/master"
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
	getBusinessID func(id uaposition.ID) (*uabusiness.ID, error)
}

func (s *stubReadPositionRepo) GetBusinessID(id uaposition.ID) (*uabusiness.ID, error) {
	return s.getBusinessID(id)
}

type stubReadBusinessRepo struct {
	get func(id uabusiness.ID) (*uabusiness.Business, error)
}

func (s *stubReadBusinessRepo) Get(id uabusiness.ID) (*uabusiness.Business, error) {
	return s.get(id)
}

type stubReadCompanyRepo struct {
	get func(id uacompany.ID) (*uacompany.Company, error)
}

func (s *stubReadCompanyRepo) Get(id uacompany.ID) (*uacompany.Company, error) {
	return s.get(id)
}

type stubIndustryMaster struct {
	getIndustrySmallNameIncludingAllIndustry func(smallID master.IndustrySmallID) string
}

func (s *stubIndustryMaster) GetIndustrySmallNameIncludingAllIndustry(smallID master.IndustrySmallID) string {
	return s.getIndustrySmallNameIncludingAllIndustry(smallID)
}

func setMasterProviderCacheForTest(cache *master.Cache) {
	provider := master.Provider()
	v := reflect.ValueOf(provider).Elem().FieldByName("cache")
	reflect.NewAt(v.Type(), unsafe.Pointer(v.UnsafeAddr())).Elem().Set(reflect.ValueOf(cache))
}

func TestGetDetailUseCase_Execute(t *testing.T) {
	setMasterProviderCacheForTest(&master.Cache{
		TraitBusinessOptions: map[master.MasterTraitBusinessID][]*master.TraitBusinessOption{},
	})

	t.Run("position repo error", func(t *testing.T) {
		uc := NewGetDetailUseCaseWithRepositories(
			&stubLogger{},
			&stubReadPositionRepo{getBusinessID: func(uaposition.ID) (*uabusiness.ID, error) { return nil, errors.New("failed") }},
			&stubReadBusinessRepo{},
			&stubReadCompanyRepo{},
			&stubIndustryMaster{getIndustrySmallNameIncludingAllIndustry: func(master.IndustrySmallID) string { return "" }},
		)
		res, err := uc.Execute(1)
		assert.Nil(t, res)
		assert.True(t, merr.Is(err, merr.ErrInternalServer))
	})

	t.Run("position repo not found", func(t *testing.T) {
		uc := NewGetDetailUseCaseWithRepositories(
			&stubLogger{},
			&stubReadPositionRepo{getBusinessID: func(uaposition.ID) (*uabusiness.ID, error) { return nil, nil }},
			&stubReadBusinessRepo{},
			&stubReadCompanyRepo{},
			&stubIndustryMaster{getIndustrySmallNameIncludingAllIndustry: func(master.IndustrySmallID) string { return "" }},
		)
		res, err := uc.Execute(1)
		assert.Nil(t, res)
		assert.True(t, merr.Is(err, merr.ErrResourceNotFound))
	})

	t.Run("business repo error", func(t *testing.T) {
		id := uabusiness.ID(10)
		uc := NewGetDetailUseCaseWithRepositories(
			&stubLogger{},
			&stubReadPositionRepo{getBusinessID: func(uaposition.ID) (*uabusiness.ID, error) { return &id, nil }},
			&stubReadBusinessRepo{get: func(uabusiness.ID) (*uabusiness.Business, error) { return nil, errors.New("failed") }},
			&stubReadCompanyRepo{},
			&stubIndustryMaster{getIndustrySmallNameIncludingAllIndustry: func(master.IndustrySmallID) string { return "" }},
		)
		res, err := uc.Execute(1)
		assert.Nil(t, res)
		assert.True(t, merr.Is(err, merr.ErrInternalServer))
	})

	t.Run("business not found", func(t *testing.T) {
		id := uabusiness.ID(10)
		uc := NewGetDetailUseCaseWithRepositories(
			&stubLogger{},
			&stubReadPositionRepo{getBusinessID: func(uaposition.ID) (*uabusiness.ID, error) { return &id, nil }},
			&stubReadBusinessRepo{get: func(uabusiness.ID) (*uabusiness.Business, error) { return nil, nil }},
			&stubReadCompanyRepo{},
			&stubIndustryMaster{getIndustrySmallNameIncludingAllIndustry: func(master.IndustrySmallID) string { return "" }},
		)
		res, err := uc.Execute(1)
		assert.Nil(t, res)
		assert.True(t, merr.Is(err, merr.ErrResourceNotFound))
	})

	t.Run("company repo error", func(t *testing.T) {
		id := uabusiness.ID(10)
		uc := NewGetDetailUseCaseWithRepositories(
			&stubLogger{},
			&stubReadPositionRepo{getBusinessID: func(uaposition.ID) (*uabusiness.ID, error) { return &id, nil }},
			&stubReadBusinessRepo{
				get: func(uabusiness.ID) (*uabusiness.Business, error) {
					return &uabusiness.Business{ID: id, CompanyID: 20}, nil
				},
			},
			&stubReadCompanyRepo{get: func(uacompany.ID) (*uacompany.Company, error) { return nil, errors.New("failed") }},
			&stubIndustryMaster{getIndustrySmallNameIncludingAllIndustry: func(master.IndustrySmallID) string { return "" }},
		)
		res, err := uc.Execute(1)
		assert.Nil(t, res)
		assert.True(t, merr.Is(err, merr.ErrInternalServer))
	})

	t.Run("company not found", func(t *testing.T) {
		id := uabusiness.ID(10)
		uc := NewGetDetailUseCaseWithRepositories(
			&stubLogger{},
			&stubReadPositionRepo{getBusinessID: func(uaposition.ID) (*uabusiness.ID, error) { return &id, nil }},
			&stubReadBusinessRepo{
				get: func(uabusiness.ID) (*uabusiness.Business, error) {
					return &uabusiness.Business{ID: id, CompanyID: 20}, nil
				},
			},
			&stubReadCompanyRepo{get: func(uacompany.ID) (*uacompany.Company, error) { return nil, nil }},
			&stubIndustryMaster{getIndustrySmallNameIncludingAllIndustry: func(master.IndustrySmallID) string { return "" }},
		)
		res, err := uc.Execute(1)
		assert.Nil(t, res)
		assert.True(t, merr.Is(err, merr.ErrInternalServer))
	})

	t.Run("company not registered", func(t *testing.T) {
		id := uabusiness.ID(10)
		uc := NewGetDetailUseCaseWithRepositories(
			&stubLogger{},
			&stubReadPositionRepo{getBusinessID: func(uaposition.ID) (*uabusiness.ID, error) { return &id, nil }},
			&stubReadBusinessRepo{
				get: func(uabusiness.ID) (*uabusiness.Business, error) {
					return &uabusiness.Business{ID: id, CompanyID: 20}, nil
				},
			},
			&stubReadCompanyRepo{
				get: func(uacompany.ID) (*uacompany.Company, error) {
					return &uacompany.Company{RegistrationStatusID: uacompany.RegistrationStatusTemporary}, nil
				},
			},
			&stubIndustryMaster{getIndustrySmallNameIncludingAllIndustry: func(master.IndustrySmallID) string { return "" }},
		)
		res, err := uc.Execute(1)
		assert.Nil(t, res)
		assert.True(t, merr.Is(err, merr.ErrResourceNotFound))
	})

	t.Run("success", func(t *testing.T) {
		id := uabusiness.ID(10)
		uc := NewGetDetailUseCaseWithRepositories(
			&stubLogger{},
			&stubReadPositionRepo{getBusinessID: func(uaposition.ID) (*uabusiness.ID, error) { return &id, nil }},
			&stubReadBusinessRepo{
				get: func(uabusiness.ID) (*uabusiness.Business, error) {
					return &uabusiness.Business{
						ID:        id,
						CompanyID: 20,
						Detail: uabusiness.Detail{
							Name: "Biz",
						},
					}, nil
				},
			},
			&stubReadCompanyRepo{
				get: func(uacompany.ID) (*uacompany.Company, error) {
					return &uacompany.Company{RegistrationStatusID: uacompany.RegistrationStatusRegistered}, nil
				},
			},
			&stubIndustryMaster{getIndustrySmallNameIncludingAllIndustry: func(master.IndustrySmallID) string { return "" }},
		)
		res, err := uc.Execute(1)
		assert.NoError(t, err)
		assert.NotNil(t, res)
		assert.Equal(t, "Biz", res.Business.Name)
	})
}

func TestBusinessHelperFunctions(t *testing.T) {
	assert.Nil(t, showIndustries(nil))
	assert.NotNil(t, showIndustries(&uabusiness.Industries{
		Industries: []*uabusiness.Industry{{SmallID: 1, Label: "x", MainFlg: true}},
	}))

	assert.Nil(t, showProduct(userMaster.TraitHelper{}, nil))
	assert.NotNil(t, showProduct(userMaster.TraitHelper{}, &uabusiness.Product{
		Tangibleness: &uabusiness.Tangibleness{},
	}))

	assert.Nil(t, showTangibleness(userMaster.TraitHelper{}, nil))
	assert.NotNil(t, showTangibleness(userMaster.TraitHelper{}, &uabusiness.Tangibleness{}))

	assert.Nil(t, showTargetCustomer(userMaster.TraitHelper{}, nil, func(master.IndustrySmallID) string { return "" }))
	assert.NotNil(t, showTargetCustomer(userMaster.TraitHelper{}, &uabusiness.TargetCustomer{
		BtoB: &uabusiness.BtoB{},
		BtoC: &uabusiness.BtoC{},
	}, func(master.IndustrySmallID) string { return "" }))

	assert.Nil(t, showBtoB(nil, func(master.IndustrySmallID) string { return "" }))
	assert.NotNil(t, showBtoB(&uabusiness.BtoB{}, func(master.IndustrySmallID) string { return "" }))

	assert.Nil(t, showBtoBIndustrySmalls(nil, func(master.IndustrySmallID) string { return "" }))
	assert.Len(t, showBtoBIndustrySmalls(applyVO.IDOnlyList{&applyVO.IDOnly{ID: 1}}, func(master.IndustrySmallID) string { return "name" }), 1)

	assert.Nil(t, showBtoC(userMaster.TraitHelper{}, nil))
	assert.NotNil(t, showBtoC(userMaster.TraitHelper{}, &uabusiness.BtoC{
		TargetIDs: applyVO.IDOnlyList{&applyVO.IDOnly{ID: 1}},
	}))

	assert.Nil(t, showBtoCTargets(userMaster.TraitHelper{}, nil))
	assert.Len(t, showBtoCTargets(userMaster.TraitHelper{}, applyVO.IDOnlyList{&applyVO.IDOnly{ID: 1}}), 1)

	assert.Nil(t, showDecisionType(userMaster.TraitHelper{}, nil))
	assert.NotNil(t, showDecisionType(userMaster.TraitHelper{}, &uabusiness.DecisionType{
		Type1: 1, Type2: 2, Type3: 3, Type4: 4,
	}))
	assert.Nil(t, showDecisionTypeValue(nil, 0))
	assert.NotNil(t, showDecisionTypeValue(nil, 1))

	assert.Nil(t, showEmployeeCharacter(userMaster.TraitHelper{}, nil))
	assert.NotNil(t, showEmployeeCharacter(userMaster.TraitHelper{}, &uabusiness.EmployeeCharacter{
		Character1: 1, Character2: 2, Character3: 3, Character4: 4,
		Character5: 5, Character6: 6, Character7: 7, Character8: 8,
		Character9: 9, Character10: 10, Character11: 11, Character12: 12,
	}))
	assert.Nil(t, showEmployeeCharacterValue(nil, 0))
	assert.NotNil(t, showEmployeeCharacterValue(nil, 1))
}
