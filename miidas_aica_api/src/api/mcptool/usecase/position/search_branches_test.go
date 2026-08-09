package position

import (
	"context"
	"testing"

	"miidas/m2/user/marketvalue/grpc/iface"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"

	tmock "aica/api/api/mcptool/testutil/mock"
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	address "aica/api/api/mcptool/usecase/shared"
	"aica/api/domain/user/apply/position"
	merr "aica/api/sdk/error"
)

func TestGenericSearchUseCase_ExecuteByInput_ConfigErrors(t *testing.T) {
	params := &pmodel.GenericPositionSearchParams{}

	t.Run("バリデータが未設定の場合", func(t *testing.T) {
		uc := NewGenericSearchUseCase(nil, nil, nil, nil, nil, nil, nil)
		_, _, err := uc.ExecuteByInputWithResolvedJobTypeIDs(context.Background(), params, nil, "")
		assert.Error(t, err)
		assert.True(t, merr.Is(err, merr.ErrInternalServer))
	})

	t.Run("リゾルバが未設定の場合", func(t *testing.T) {
		validator := new(mockPositionSearchValidator)
		uc := NewGenericSearchUseCase(nil, nil, nil, nil, nil, validator, nil)
		_, _, err := uc.ExecuteByInputWithResolvedJobTypeIDs(context.Background(), params, nil, "")
		assert.Error(t, err)
		assert.True(t, merr.Is(err, merr.ErrInternalServer))
		validator.AssertNotCalled(t, "ValidatePositionSearchParams", mock.Anything)
	})
}

func TestGenericSearchUseCase_Execute_ValidationBranches(t *testing.T) {
	uc := NewGenericSearchUseCase(nil, nil, nil, nil, nil, nil, nil)

	_, _, err := uc.Execute(
		context.Background(),
		&pmodel.GenericPositionSearchParams{
			CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
				DayOffs: loPtr([]string{"invalid"}),
			},
		},
		nil,
		nil,
		"",
	)
	assert.Error(t, err)
	assert.True(t, merr.Is(err, merr.ErrInvalidRequest))

	_, _, err = uc.Execute(
		context.Background(),
		&pmodel.GenericPositionSearchParams{
			CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
				DayOffs:         loPtr([]string{string(pcontracts.DAYOFF_WEEKEND)}),
				AverageOvertime: loPtr("invalid"),
			},
		},
		nil,
		nil,
		"",
	)
	assert.Error(t, err)
	assert.True(t, merr.Is(err, merr.ErrInvalidRequest))
}

func TestGenericSearchUseCase_Execute_RemoteBranch(t *testing.T) {
	mockMVGateway := new(mockMvGateway)
	mockReadPositionRepo := new(mockReadPositionRepository)

	mockMVGateway.On(
		"GetWillPositionList",
		mock.Anything,
		mock.Anything,
		mock.MatchedBy(func(p *iface.Position) bool {
			return p != nil &&
				p.WorkAddress != nil && p.WorkAddress.Importance == 0 &&
				p.RemoteWork != nil && p.RemoteWork.Importance == 3 &&
				len(p.RemoteWork.Value.Exists) == 2
		}),
	).Return([]*iface.PositionListEntry{{PositionId: 1}}, nil).Once()
	mockReadPositionRepo.On("GetByIDs", []position.ID{1}).Return(position.Positions{{ID: 1}}, nil).Once()

	uc := NewGenericSearchUseCase(&tmock.MockLogger{}, mockMVGateway, nil, nil, mockReadPositionRepo, nil, nil)
	ids, rows, err := uc.Execute(
		context.Background(),
		&pmodel.GenericPositionSearchParams{
			CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
				Salary: 100,
				Locations: []*address.LocationRequest{
					{LocationType: address.LOCATION_TYPE_FULL_REMOTE_WORK},
				},
			},
		},
		[]int{10},
		[]int{20},
		"",
	)
	assert.NoError(t, err)
	assert.Equal(t, []position.ID{1}, ids)
	assert.Len(t, rows, 1)

	mockMVGateway.AssertExpectations(t)
	mockReadPositionRepo.AssertExpectations(t)
}
