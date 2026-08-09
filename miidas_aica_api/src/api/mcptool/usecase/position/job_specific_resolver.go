package position

import (
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	pinterfaces "aica/api/api/mcptool/usecase/position/interfaces"
	psupport "aica/api/api/mcptool/usecase/position/support"
	address "aica/api/api/mcptool/usecase/shared"
	"aica/api/domain/public/master"
	merr "aica/api/sdk/error"
	"fmt"
)

type cacheReadable interface {
	ExistsPrefectureCity(prefectureName string, cityName string) bool
	GetJobTypeSmallIDsByNames(names []string) ([]int32, error)
	GetLocationRequestsFromCityIDs(cityIDs []int32) []*address.LocationRequest
	ResolveLocationRequestByName(name string) (*address.LocationRequest, error)
	GetSkillsByNames(names []string) (master.Skills, error)
	GetTraitPositionOptionValueByNameOrUserSideName(traitID master.MasterTraitPositionID, name string) (int, error)
}

type jobSpecificSearchResolverImpl struct {
	cacheService   cacheReadable
	locationLookup pinterfaces.LocationLookup
}

func NewJobSpecificSearchResolver(cacheService cacheReadable, locationLookup pinterfaces.LocationLookup) pcontracts.JobSpecificSearchResolver {
	return &jobSpecificSearchResolverImpl{
		cacheService:   cacheService,
		locationLookup: locationLookup,
	}
}

func (r *jobSpecificSearchResolverImpl) ExistsPrefectureCity(prefectureName string, cityName string) bool {
	return r.cacheService.ExistsPrefectureCity(prefectureName, cityName)
}

func (r *jobSpecificSearchResolverImpl) ResolveJobTypeSmallIDs(names []string) ([]int32, error) {
	return r.cacheService.GetJobTypeSmallIDsByNames(names)
}

func (r *jobSpecificSearchResolverImpl) ResolveLocationByName(name string) (*address.LocationRequest, error) {
	return r.cacheService.ResolveLocationRequestByName(name)
}

func (r *jobSpecificSearchResolverImpl) ResolveLocations(locations []*address.LocationRequest, remoteWorkPossible bool) ([]int32, *address.LocationRequest, []*address.LocationRequest, []*address.LocationRequest, error) {
	var cityIDs []int32
	// residenceLocation は検索条件として採用した居住地。保存用フィルタの Residence.Address に使う。
	var residenceLocation *address.LocationRequest
	// commutingAreaResponses は保存用フィルタの Residence.CommutingAreas に返す通勤圏リクエスト一覧。
	commutingAreaResponses := make([]*address.LocationRequest, 0, len(locations))
	// workLocationResponses は明示的に指定された希望勤務地リクエスト。保存用フィルタの WorkLocations に使う。
	workLocationResponses := make([]*address.LocationRequest, 0, len(locations))
	// commutingAreas は通勤圏の city ID 解決に渡すための生データ。
	commutingAreas := make([]struct{ PrefectureName, CityName string }, 0, len(locations))
	// workLocations は希望勤務地の city ID 解決に渡すための生データ。
	workLocations := make([]struct{ PrefectureName, CityName string }, 0, len(locations))
	// hasExplicitCommutingAreas は通勤圏が明示指定されたかどうか。true の場合は居住地からの通勤圏逆引きをしない。
	hasExplicitCommutingAreas := false

	for _, loc := range locations {
		switch loc.LocationType {
		case address.LOCATION_TYPE_RESIDENCE:
			if residenceLocation == nil {
				residenceLocation = &address.LocationRequest{
					LocationType:   loc.LocationType,
					PrefectureName: loc.PrefectureName,
					CityName:       loc.CityName,
				}
			}
		case address.LOCATION_TYPE_COMMUTING_AREAS:
			hasExplicitCommutingAreas = true
			commutingAreaResponses = append(commutingAreaResponses, &address.LocationRequest{
				LocationType:   loc.LocationType,
				PrefectureName: loc.PrefectureName,
				CityName:       loc.CityName,
			})
			if remoteWorkPossible {
				// フルリモート可の検索では勤務地 city ID に絞り込まないため、ID 解決だけをスキップする。
				// 一方で通勤圏そのものは保存用フィルタ再構築に必要なので commutingAreaResponses には残す。
				continue
			}
			commutingAreas = append(commutingAreas, struct{ PrefectureName, CityName string }{
				PrefectureName: loc.PrefectureName,
				CityName:       loc.CityName,
			})
		case address.LOCATION_TYPE_WORK_LOCATION:
			workLocationResponses = append(workLocationResponses, &address.LocationRequest{
				LocationType:   loc.LocationType,
				PrefectureName: loc.PrefectureName,
				CityName:       loc.CityName,
			})
			if remoteWorkPossible {
				// フルリモート可の検索では勤務地 city ID による検索条件を作らないため、ID 解決だけをスキップする。
				// 希望勤務地自体は保存用フィルタの WorkLocations に必要なので workLocationResponses には残す。
				continue
			}
			workLocations = append(workLocations, struct{ PrefectureName, CityName string }{
				PrefectureName: loc.PrefectureName,
				CityName:       loc.CityName,
			})
		}
	}

	if !remoteWorkPossible && !hasExplicitCommutingAreas && residenceLocation != nil {
		ids, err := r.locationLookup.GetCommutingAreasFromResidence(residenceLocation.PrefectureName, residenceLocation.CityName)
		if err != nil {
			return nil, nil, nil, nil, err
		}
		commutingAreaResponses = r.cacheService.GetLocationRequestsFromCityIDs(toInt32IDs(ids))
		for _, id := range ids {
			cityIDs = append(cityIDs, int32(id))
		}
	}

	if !remoteWorkPossible && len(commutingAreas) > 0 {
		ids, err := r.locationLookup.GetCityIDsFromWorkLocations(commutingAreas)
		if err != nil {
			return nil, nil, nil, nil, err
		}
		for _, id := range ids {
			cityIDs = append(cityIDs, int32(id))
		}
	}

	if !remoteWorkPossible && len(workLocations) > 0 {
		ids, err := r.locationLookup.GetCityIDsFromWorkLocations(workLocations)
		if err != nil {
			return nil, nil, nil, nil, err
		}
		for _, id := range ids {
			cityIDs = append(cityIDs, int32(id))
		}
	}

	return cityIDs, residenceLocation, commutingAreaResponses, workLocationResponses, nil
}

func (r *jobSpecificSearchResolverImpl) ResolveSkills(skillNames []string) (master.Skills, error) {
	return r.cacheService.GetSkillsByNames(skillNames)
}

func (r *jobSpecificSearchResolverImpl) ResolveDayOffs(dayOffs *[]string) ([]int32, error) {
	values, err := psupport.ConvertDayOffs(dayOffs)
	if err != nil {
		return nil, merr.ErrInvalidRequest.WithCause(err)
	}
	return values, nil
}

func (r *jobSpecificSearchResolverImpl) ResolveAverageOvertime(overtime *string) (int32, error) {
	value, err := psupport.ConvertAverageOvertime(overtime)
	if err != nil {
		return 0, merr.ErrInvalidRequest.WithCause(err)
	}
	return value, nil
}

func (r *jobSpecificSearchResolverImpl) ResolveSalesStyleDive(salesStyleDive *string) (int32, error) {
	if salesStyleDive == nil {
		return 0, nil
	}

	value, err := r.cacheService.GetTraitPositionOptionValueByNameOrUserSideName(master.PtjSalesStyleDive, *salesStyleDive)
	if err != nil {
		return 0, merr.ErrInvalidRequest.WithCause(
			fmt.Errorf("新規飛び込み(SalesStyleDive)に指定できる値は、「あり」／「なし」のみなので、設定し直してください。"),
		)
	}

	return int32(value), nil
}
