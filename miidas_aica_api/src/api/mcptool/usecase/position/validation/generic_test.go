package validation_test

import (
	pmodel "aica/api/api/mcptool/usecase/position/model"
	pvalidation "aica/api/api/mcptool/usecase/position/validation"
	address "aica/api/api/mcptool/usecase/shared"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

type mockCacheProvider struct {
	mock.Mock
}

func (m *mockCacheProvider) ExistsPrefectureCity(prefectureName string, cityName string) bool {
	args := m.Called(prefectureName, cityName)
	return args.Bool(0)
}

func TestPositionValidator_ValidatePositionSearchParams(t *testing.T) {
	tests := []struct {
		name    string
		params  pmodel.GenericPositionSearchParams
		wantErr bool
	}{
		{
			name: "年収＋職種＋フルリモート",
			params: pmodel.GenericPositionSearchParams{
				CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
					JobtypeNames: []string{"SE"},
					Salary:       123,
					Locations: []*address.LocationRequest{
						{
							LocationType:   address.LOCATION_TYPE_FULL_REMOTE_WORK,
							PrefectureName: "",
							CityName:       "",
						},
					},
				},
			},
			wantErr: false,
		},
		{
			name: "年収＋フルリモート",
			params: pmodel.GenericPositionSearchParams{
				CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
					Salary: 123,
					Locations: []*address.LocationRequest{
						{
							LocationType:   address.LOCATION_TYPE_FULL_REMOTE_WORK,
							PrefectureName: "",
							CityName:       "",
						},
					},
				},
			},
			wantErr: true,
		},
		{
			name: "年収＋場所＋職種なし",
			params: pmodel.GenericPositionSearchParams{
				CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
					Salary: 123,
					Locations: []*address.LocationRequest{
						{
							LocationType:   address.LOCATION_TYPE_WORK_LOCATION,
							PrefectureName: "東京都",
							CityName:       "府中市",
						},
					},
				},
			},
			wantErr: true,
		},
		{
			name: "年収＋場所＋空白のみの職種",
			params: pmodel.GenericPositionSearchParams{
				CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
					JobtypeNames: []string{"   "},
					Salary:       123,
					Locations: []*address.LocationRequest{
						{
							LocationType:   address.LOCATION_TYPE_WORK_LOCATION,
							PrefectureName: "東京都",
							CityName:       "府中市",
						},
					},
				},
			},
			wantErr: true,
		},
		{
			name: "年収＋希望勤務地",
			params: pmodel.GenericPositionSearchParams{
				CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
					JobtypeNames: []string{"SE"},
					Salary:       123,
					Locations: []*address.LocationRequest{
						{
							LocationType:   address.LOCATION_TYPE_WORK_LOCATION,
							PrefectureName: "東京都",
							CityName:       "府中市",
						},
					},
				},
			},
			wantErr: false,
		},
		{
			name: "年収＋場所（空の配列）",
			params: pmodel.GenericPositionSearchParams{
				CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
					JobtypeNames: []string{"SE"},
					Salary:       123,
					Locations:    []*address.LocationRequest{},
				},
			},
			wantErr: true,
		},
		{
			name: "年収＋希望勤務地（都道府県名のみ）",
			params: pmodel.GenericPositionSearchParams{
				CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
					JobtypeNames: []string{"SE"},
					Salary:       123,
					Locations: []*address.LocationRequest{
						{
							LocationType:   address.LOCATION_TYPE_WORK_LOCATION,
							PrefectureName: "東京都",
							CityName:       "",
						},
					},
				},
			},
			wantErr: true,
		},
		{
			name: "年収＋希望勤務地（市区町村名のみ）",
			params: pmodel.GenericPositionSearchParams{
				CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
					JobtypeNames: []string{"SE"},
					Salary:       123,
					Locations: []*address.LocationRequest{
						{
							LocationType:   address.LOCATION_TYPE_WORK_LOCATION,
							PrefectureName: "",
							CityName:       "府中市",
						},
					},
				},
			},
			wantErr: true,
		},
		{
			name: "年収＋居住地",
			params: pmodel.GenericPositionSearchParams{
				CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
					JobtypeNames: []string{"SE"},
					Salary:       123,
					Locations: []*address.LocationRequest{
						{
							LocationType:   address.LOCATION_TYPE_RESIDENCE,
							PrefectureName: "東京都",
							CityName:       "府中市",
						},
					},
				},
			},
			wantErr: false,
		},
		{
			name: "年収＋居住地（都道府県名のみ）",
			params: pmodel.GenericPositionSearchParams{
				CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
					JobtypeNames: []string{"SE"},
					Salary:       123,
					Locations: []*address.LocationRequest{
						{
							LocationType:   address.LOCATION_TYPE_RESIDENCE,
							PrefectureName: "東京都",
							CityName:       "",
						},
					},
				},
			},
			wantErr: true,
		},
		{
			name: "年収＋居住地（市区町村名のみ）",
			params: pmodel.GenericPositionSearchParams{
				CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
					JobtypeNames: []string{"SE"},
					Salary:       123,
					Locations: []*address.LocationRequest{
						{
							LocationType:   address.LOCATION_TYPE_RESIDENCE,
							PrefectureName: "",
							CityName:       "府中市",
						},
					},
				},
			},
			wantErr: true,
		},
		{
			name: "年収なし",
			params: pmodel.GenericPositionSearchParams{
				CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
					JobtypeNames: []string{"SE"},
					Locations: []*address.LocationRequest{
						{
							LocationType:   address.LOCATION_TYPE_RESIDENCE,
							PrefectureName: "東京都",
							CityName:       "府中市",
						},
					},
				},
			},
			wantErr: true,
		},
		{
			name: "存在しない職種名（意味情報検索）",
			params: pmodel.GenericPositionSearchParams{
				CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
					Salary: 123,
					Locations: []*address.LocationRequest{
						{
							LocationType:   address.LOCATION_TYPE_FULL_REMOTE_WORK,
							PrefectureName: "",
							CityName:       "",
						},
					},
					JobtypeNames: []string{"セールス"},
				},
			},
			wantErr: false,
		},
	}

	runCase := func(tt struct {
		name    string
		params  pmodel.GenericPositionSearchParams
		wantErr bool
	}) {
		t.Run(tt.name, func(t *testing.T) {
			mockCache := new(mockCacheProvider)
			mockCache.On("ExistsPrefectureCity", mock.Anything, mock.Anything).Return(true)

			err := pvalidation.NewPositionValidator(mockCache).ValidatePositionSearchParams(&tt.params)
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}

	runCase(tests[0])
	runCase(tests[1])
	runCase(tests[2])
	runCase(tests[3])
	runCase(tests[4])
	runCase(tests[5])
	runCase(tests[6])
	runCase(tests[7])
	runCase(tests[8])
	runCase(tests[9])
	runCase(tests[10])
	runCase(tests[11])
}
