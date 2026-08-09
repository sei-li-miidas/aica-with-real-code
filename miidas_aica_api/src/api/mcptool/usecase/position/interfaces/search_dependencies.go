package interfaces

import (
	"gorm.io/datatypes"

	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	address "aica/api/api/mcptool/usecase/shared"
	jobfilter "aica/api/domain/jobfilter"
	uaposition "aica/api/domain/user/apply/position"
)

type PositionGetter interface {
	GetByIDs(ids []uaposition.ID) (uaposition.Positions, error)
}

type JobSearchFilterRepository interface {
	GetTypedJobSearchFilterBySessionID(sessionID string) (*jobfilter.JobSearchFilter, error)
	UpsertJobSearchFilter(sessionID string, jobSearchFilter datatypes.JSON) error
}

type LocationLookup interface {
	GetCommutingAreasFromResidence(prefectureName string, cityName string) ([]int, error)
	GetCityIDsFromWorkLocations(locations []struct{ PrefectureName, CityName string }) ([]int, error)
}

type JobTypeSearchToolResolver interface {
	ToolNameByJobtypeName(name string) string
	JobtypeNamesByToolName(toolName string) []string
}

type PositionSearchValidator interface {
	ValidatePositionSearchParams(params *pmodel.GenericPositionSearchParams) error
}

type JobSearchFilterReader interface {
	GetBySessionID(sessionID string) (*jobfilter.JobSearchFilter, error)
}

type JobSearchFilterPersister interface {
	PersistFromSearchInput(sessionID string, input *pcontracts.JobSpecificSearchInput, commutingAreas []*address.LocationRequest, searchFilters *jobfilter.JobSearchFilter) (*jobfilter.JobSearchFilter, error)
}

type JobSearchFilterGenericPersister interface {
	PersistFromGenericSearchParams(sessionID string, params *pmodel.GenericPositionSearchParams) (*jobfilter.JobSearchFilter, error)
}

type JobSearchFilterJobtypesWriter interface {
	MergeJobTypes(sessionID string, selectedGroupKey string, groupedJobtypeNames map[string][]string) error
}
