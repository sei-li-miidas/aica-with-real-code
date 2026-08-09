package position

import (
	tmock "aica/api/api/mcptool/testutil/mock"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	address "aica/api/api/mcptool/usecase/shared"
	uaposition "aica/api/domain/user/apply/position"
	"testing"

	"miidas/m2/user/marketvalue/grpc/iface"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

type mockPositionSearchValidator struct{ mock.Mock }

func (m *mockPositionSearchValidator) ValidatePositionSearchParams(params *pmodel.GenericPositionSearchParams) error {
	args := m.Called(params)
	return args.Error(0)
}

type mockLocationLookup struct{ mock.Mock }

func (m *mockLocationLookup) GetCommutingAreasFromResidence(prefectureName string, cityName string) ([]int, error) {
	args := m.Called(prefectureName, cityName)
	return args.Get(0).([]int), args.Error(1)
}

func (m *mockLocationLookup) GetCityIDsFromWorkLocations(locations []struct{ PrefectureName, CityName string }) ([]int, error) {
	args := m.Called(locations)
	return args.Get(0).([]int), args.Error(1)
}

func TestSearchUseCase_ExecuteByInput_Success(t *testing.T) {
	mockLogger := &tmock.MockLogger{}
	mockMVGateway := new(mockMvGateway)
	mockPositionRepo := new(mockPositionRepository)
	mockReadPositionRepo := new(mockReadPositionRepository)
	validator := new(mockPositionSearchValidator)
	locationLookup := new(mockLocationLookup)

	params := &pmodel.GenericPositionSearchParams{
		CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
			Salary:       500,
			JobtypeNames: []string{"A"},
			Locations: []*address.LocationRequest{
				{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "東京都", CityName: "新宿区"},
			},
		},
	}
	validator.On("ValidatePositionSearchParams", params).Return(nil).Once()
	locationLookup.On("GetCommutingAreasFromResidence", "東京都", "新宿区").Return([]int{1}, nil).Once()

	mockMVGateway.On("GetWillPositionList", mock.Anything, mock.Anything, mock.Anything).
		Return([]*iface.PositionListEntry{{PositionId: 101}}, nil).Once()
	mockReadPositionRepo.On("GetByIDs", []uaposition.ID{101}).Return(uaposition.Positions{{ID: 101}}, nil).Once()

	uc := NewGenericSearchUseCase(
		mockLogger,
		mockMVGateway,
		nil,
		mockPositionRepo,
		mockReadPositionRepo,
		validator,
		locationLookup,
	)

	ids, positions, err := uc.ExecuteByInputWithResolvedJobTypeIDs(t.Context(), params, []int{2}, "")
	assert.NoError(t, err)
	assert.Equal(t, []uaposition.ID{101}, ids)
	assert.Equal(t, []*pmodel.PositionSummary{{ID: 101}}, positions)

	validator.AssertExpectations(t)
	locationLookup.AssertExpectations(t)
	mockMVGateway.AssertExpectations(t)
	mockReadPositionRepo.AssertExpectations(t)
}

func TestSearchUseCase_ExecuteByInput_ValidationError(t *testing.T) {
	validator := new(mockPositionSearchValidator)
	locationLookup := new(mockLocationLookup)
	params := &pmodel.GenericPositionSearchParams{
		CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
			JobtypeNames: []string{"A"},
		},
	}

	validator.On("ValidatePositionSearchParams", params).Return(assert.AnError).Once()

	uc := NewGenericSearchUseCase(
		&tmock.MockLogger{},
		nil,
		nil,
		nil,
		nil,
		validator,
		locationLookup,
	)

	_, _, err := uc.ExecuteByInputWithResolvedJobTypeIDs(t.Context(), params, nil, "")
	assert.Error(t, err)
	validator.AssertExpectations(t)
	locationLookup.AssertNotCalled(t, "GetCommutingAreasFromResidence", mock.Anything, mock.Anything)
}

func TestSearchUseCase_ExecuteByInput_LocationLookupError(t *testing.T) {
	validator := new(mockPositionSearchValidator)
	locationLookup := new(mockLocationLookup)
	params := &pmodel.GenericPositionSearchParams{
		CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
			JobtypeNames: []string{"A"},
			Locations: []*address.LocationRequest{
				{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "東京都", CityName: "新宿区"},
			},
		},
	}

	validator.On("ValidatePositionSearchParams", params).Return(nil).Once()
	locationLookup.On("GetCommutingAreasFromResidence", "東京都", "新宿区").Return([]int(nil), assert.AnError).Once()

	uc := NewGenericSearchUseCase(
		&tmock.MockLogger{},
		nil,
		nil,
		nil,
		nil,
		validator,
		locationLookup,
	)

	_, _, err := uc.ExecuteByInputWithResolvedJobTypeIDs(t.Context(), params, nil, "")
	assert.Error(t, err)
}

func TestSearchUseCase_ExecuteByInput_MissingResolvedJobTypeIDs(t *testing.T) {
	validator := new(mockPositionSearchValidator)
	locationLookup := new(mockLocationLookup)
	params := &pmodel.GenericPositionSearchParams{
		CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
			JobtypeNames: []string{"A"},
			Locations: []*address.LocationRequest{
				{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "東京都", CityName: "新宿区"},
			},
		},
	}

	validator.On("ValidatePositionSearchParams", params).Return(nil).Once()
	locationLookup.On("GetCommutingAreasFromResidence", "東京都", "新宿区").Return([]int{}, nil).Once()

	uc := NewGenericSearchUseCase(
		&tmock.MockLogger{},
		nil,
		nil,
		nil,
		nil,
		validator,
		locationLookup,
	)

	_, _, err := uc.ExecuteByInputWithResolvedJobTypeIDs(t.Context(), params, nil, "")
	assert.Error(t, err)
}

func TestSearchUseCase_ExecuteByInputWithResolvedJobTypeIDs_SkipJobTypeSemanticSearch(t *testing.T) {
	mockLogger := &tmock.MockLogger{}
	mockMVGateway := new(mockMvGateway)
	mockPositionRepo := new(mockPositionRepository)
	mockReadPositionRepo := new(mockReadPositionRepository)
	validator := new(mockPositionSearchValidator)
	locationLookup := new(mockLocationLookup)

	params := &pmodel.GenericPositionSearchParams{
		CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
			Salary:       500,
			JobtypeNames: []string{"A"},
			Locations: []*address.LocationRequest{
				{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "東京都", CityName: "新宿区"},
			},
		},
	}
	validator.On("ValidatePositionSearchParams", params).Return(nil).Once()
	locationLookup.On("GetCommutingAreasFromResidence", "東京都", "新宿区").Return([]int{1}, nil).Once()
	mockMVGateway.On("GetWillPositionList", mock.Anything, mock.Anything, mock.Anything).
		Return([]*iface.PositionListEntry{{PositionId: 101}}, nil).Once()
	mockReadPositionRepo.On("GetByIDs", []uaposition.ID{101}).Return(uaposition.Positions{{ID: 101}}, nil).Once()

	uc := NewGenericSearchUseCase(
		mockLogger,
		mockMVGateway,
		nil,
		mockPositionRepo,
		mockReadPositionRepo,
		validator,
		locationLookup,
	)

	ids, positions, err := uc.ExecuteByInputWithResolvedJobTypeIDs(t.Context(), params, []int{2}, "")
	assert.NoError(t, err)
	assert.Equal(t, []uaposition.ID{101}, ids)
	assert.Equal(t, []*pmodel.PositionSummary{{ID: 101}}, positions)
}
