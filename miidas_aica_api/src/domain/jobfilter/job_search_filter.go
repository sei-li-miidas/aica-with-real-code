package jobfilter

import (
	"time"

	"gorm.io/datatypes"
)

type jobSearchFilter struct {
	ID                    int64          `gorm:"column:id"`
	SessionID             string         `gorm:"column:session_id"`
	Jobtypes              datatypes.JSON `gorm:"column:jobtypes"`
	Locations             datatypes.JSON `gorm:"column:locations"`
	Salary                *int           `gorm:"column:salary"`
	SelectedFilterOptions datatypes.JSON `gorm:"column:selected_filter_options"`
	CreatedAt             time.Time      `gorm:"column:created_at"`
	UpdatedAt             *time.Time     `gorm:"column:updated_at"`
	DeletedAt             *time.Time     `gorm:"column:deleted_at"`
}

func (jobSearchFilter) TableName() string {
	return "job_search_filters"
}

type JobSearchFilterType string

const (
	JobSearchFilterTypeSingle   JobSearchFilterType = "single"
	JobSearchFilterTypeMultiple JobSearchFilterType = "multiple"
)

type JobSearchFilterOtherFilterOption struct {
	Label string `json:"Label"`
	Value string `json:"Value"`
}

type JobSearchFilterSelectableItem struct {
	JobSearchFilterOtherFilterOption

	Selected bool `json:"Selected"`
}

type JobtypeSelectableItem struct {
	JobSearchFilterSelectableItem

	Description string
}

type JobSearchFilterLocationSelectableItem struct {
	Label          string `json:"Label"`
	PrefectureName string `json:"PrefectureName,omitempty"`
	CityName       string `json:"CityName,omitempty"`
	Selected       bool   `json:"Selected"`
}

type JobSearchFilterAddress struct {
	PrefectureName string `json:"PrefectureName,omitempty"`
	CityName       string `json:"CityName,omitempty"`
}

type JobSearchFilterResidence struct {
	Address        *JobSearchFilterAddress
	CommutingAreas []*JobSearchFilterLocationSelectableItem
}

type JobSearchFilterLocations struct {
	Residence          *JobSearchFilterResidence
	WorkLocations      []*JobSearchFilterLocationSelectableItem
	RemoteWorkPossible *bool
}

type JobSearchFilterOtherFilter struct {
	Key     string
	Name    string
	Type    JobSearchFilterType
	Options []*JobSearchFilterOtherFilterOption
}

type JobSearchFilter struct {
	Jobtypes        map[string][]*JobtypeSelectableItem
	Locations       *JobSearchFilterLocations
	Salary          int
	PositionKeyword *string
	// その他条件に選択された値
	// key: tool name または common
	// value:
	//   key: filter name, value: selected option values
	SelectedOtherFilterOptions map[string]map[string][]string
}
