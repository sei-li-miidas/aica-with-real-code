package jobfilter

import (
	"aica/api/domain/jobtype"
	"encoding/json"
	"errors"

	"github.com/samber/lo"
	"gorm.io/datatypes"
	"gorm.io/gorm"
	"gorm.io/gorm/clause"
)

type JobSearchFilterRepository struct {
	db                *gorm.DB
	findRecordByID    func(sessionID string) (*jobSearchFilter, error)
	findJobtypesByIDs func(names []string) ([]*jobtype.JobTypeSmall, error)
}

func NewJobSearchFilterRepository(db *gorm.DB) *JobSearchFilterRepository {
	return &JobSearchFilterRepository{
		db: db,
	}
}

func (r *JobSearchFilterRepository) findRecord(sessionID string) (*jobSearchFilter, error) {
	if r.findRecordByID != nil {
		return r.findRecordByID(sessionID)
	}
	return r.getJobSearchFilterRecordBySessionID(sessionID)
}

func (r *JobSearchFilterRepository) findJobtypes(names []string) ([]*jobtype.JobTypeSmall, error) {
	if r.findJobtypesByIDs != nil {
		return r.findJobtypesByIDs(names)
	}
	repo := jobtype.NewJobTypeRepository(r.db)
	return repo.GetMultipleByNames(names)
}

func (r *JobSearchFilterRepository) GetTypedJobSearchFilterBySessionID(sessionID string) (*JobSearchFilter, error) {
	record, err := r.findRecord(sessionID)
	if err != nil {
		return nil, err
	}
	if record == nil {
		return nil, nil
	}

	selected := decodeJSONOrDefault(record.SelectedFilterOptions, map[string]map[string][]string{})
	latest := &JobSearchFilter{
		Jobtypes:                   decodeJSONOrDefault(record.Jobtypes, map[string][]*JobtypeSelectableItem{}),
		Locations:                  decodeJSONOrDefault(record.Locations, (*JobSearchFilterLocations)(nil)),
		Salary:                     0,
		PositionKeyword:            payloadPositionKeyword(selected),
		SelectedOtherFilterOptions: selected,
	}
	if record.Salary != nil {
		latest.Salary = *record.Salary
	}
	normalizeLocations(latest.Locations)
	if err := r.fillJobtypeDescriptions(latest.Jobtypes); err != nil {
		return nil, err
	}
	return latest, nil
}

func (r *JobSearchFilterRepository) fillJobtypeDescriptions(groups map[string][]*JobtypeSelectableItem) error {
	if len(groups) == 0 {
		return nil
	}

	names := make([]string, 0)
	seen := map[string]struct{}{}
	for _, items := range groups {
		for _, item := range items {
			if item == nil || item.Value == "" {
				continue
			}
			if _, ok := seen[item.Value]; ok {
				continue
			}
			seen[item.Value] = struct{}{}
			names = append(names, item.Value)
		}
	}
	if len(names) == 0 {
		return nil
	}

	jobtypes, err := r.findJobtypes(names)
	if err != nil {
		return err
	}
	descByName := make(map[string]string, len(jobtypes))
	for _, jt := range jobtypes {
		if jt == nil || jt.Name == "" {
			continue
		}
		descByName[jt.Name] = jt.Description
	}
	for _, items := range groups {
		for _, item := range items {
			if item == nil {
				continue
			}
			item.Description = descByName[item.Value]
		}
	}

	return nil
}

func (r *JobSearchFilterRepository) UpdateJobSearchFilterBySessionID(sessionID string, jobSearchFilter datatypes.JSON) error {
	return r.UpsertJobSearchFilter(sessionID, jobSearchFilter)
}

func (r *JobSearchFilterRepository) UpsertJobSearchFilter(sessionID string, jobSearchFilterJSON datatypes.JSON) error {
	var payload JobSearchFilter
	if len(jobSearchFilterJSON) > 0 {
		if err := json.Unmarshal(jobSearchFilterJSON, &payload); err != nil {
			return err
		}
	}

	jobtypesJSON, err := json.Marshal(lo.Ternary(payload.Jobtypes == nil, map[string][]*JobtypeSelectableItem{}, payload.Jobtypes))
	if err != nil {
		return err
	}
	locationsJSON, err := json.Marshal(payload.Locations)
	if err != nil {
		return err
	}
	selectedJSON, err := json.Marshal(lo.Ternary(payload.SelectedOtherFilterOptions == nil, map[string]map[string][]string{}, payload.SelectedOtherFilterOptions))
	if err != nil {
		return err
	}
	salary := payload.Salary
	record := &jobSearchFilter{
		SessionID:             sessionID,
		Jobtypes:              datatypes.JSON(jobtypesJSON),
		Locations:             datatypes.JSON(locationsJSON),
		Salary:                &salary,
		SelectedFilterOptions: datatypes.JSON(selectedJSON),
	}

	return r.db.Clauses(clause.OnConflict{
		Columns:   []clause.Column{{Name: "session_id"}},
		DoUpdates: clause.AssignmentColumns([]string{"jobtypes", "locations", "salary", "selected_filter_options", "updated_at"}),
	}).Create(record).Error
}

func (r *JobSearchFilterRepository) UpdateJobTypesBySessionID(sessionID string, jobTypes map[string][]*JobtypeSelectableItem) error {
	return r.updateJobSearchFilterKey(sessionID, "jobtypes", jobTypes)
}

func (r *JobSearchFilterRepository) UpdateLocationsBySessionID(sessionID string, locations *JobSearchFilterLocations) error {
	return r.updateJobSearchFilterKey(sessionID, "locations", locations)
}

func (r *JobSearchFilterRepository) UpdateSalaryBySessionID(sessionID string, salary int) error {
	return r.updateJobSearchFilterKey(sessionID, "salary", salary)
}

func (r *JobSearchFilterRepository) UpdateOtherFiltersBySessionID(sessionID string, otherFilters map[string]map[string][]string) error {
	return r.updateJobSearchFilterKey(sessionID, "SelectedOtherFilterOptions", otherFilters)
}

func (r *JobSearchFilterRepository) updateJobSearchFilterKey(sessionID string, key string, value any) error {
	current, err := r.GetTypedJobSearchFilterBySessionID(sessionID)
	if err != nil {
		return err
	}
	if current == nil {
		current = &JobSearchFilter{}
	}

	switch key {
	case "jobtypes":
		items, ok := value.(map[string][]*JobtypeSelectableItem)
		if !ok {
			return errors.New("invalid jobtypes payload")
		}
		current.Jobtypes = items
	case "locations":
		items, ok := value.(*JobSearchFilterLocations)
		if !ok {
			return errors.New("invalid locations payload")
		}
		current.Locations = items
	case "salary":
		salary, ok := value.(int)
		if !ok {
			return errors.New("invalid salary payload")
		}
		current.Salary = salary
	case "SelectedOtherFilterOptions":
		items, ok := value.(map[string]map[string][]string)
		if !ok {
			return errors.New("invalid selected filter options payload")
		}
		current.SelectedOtherFilterOptions = items
		current.PositionKeyword = payloadPositionKeyword(items)
	default:
		return errors.New("unsupported job search filter key")
	}

	payload, err := json.Marshal(current)
	if err != nil {
		return err
	}
	return r.UpsertJobSearchFilter(sessionID, datatypes.JSON(payload))
}

func (r *JobSearchFilterRepository) getJobSearchFilterRecordBySessionID(sessionID string) (*jobSearchFilter, error) {
	var record jobSearchFilter
	if err := r.db.
		Joins("JOIN chat_sessions ON chat_sessions.session_id = job_search_filters.session_id").
		Where("job_search_filters.session_id = ?", sessionID).
		Where("job_search_filters.deleted_at IS NULL").
		Where("chat_sessions.deleted_at IS NULL").
		Take(&record).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		return nil, err
	}
	return &record, nil
}

func decodeJSONOrDefault[T any](raw datatypes.JSON, defaultValue T) T {
	if len(raw) == 0 || string(raw) == "null" {
		return defaultValue
	}
	var dst T
	if err := json.Unmarshal(raw, &dst); err != nil {
		return defaultValue
	}
	return dst
}

func payloadPositionKeyword(selected map[string]map[string][]string) *string {
	if len(selected) == 0 {
		return nil
	}
	common := selected["common"]
	if len(common) == 0 {
		return nil
	}
	values := common["PositionKeyword"]
	if len(values) == 0 || values[0] == "" {
		return nil
	}
	value := values[0]
	return &value
}

// normalizeLocations は旧フォーマットで WorkLocations に "フルリモート" が含まれている場合に正規化する。
// "フルリモート" エントリを WorkLocations から除去し、RemoteWorkPossible を true に設定する。
func normalizeLocations(locations *JobSearchFilterLocations) {
	if locations == nil {
		return
	}
	filtered := make([]*JobSearchFilterLocationSelectableItem, 0, len(locations.WorkLocations))
	hasFullRemote := false
	for _, item := range locations.WorkLocations {
		if item != nil && item.Label == "フルリモート" {
			hasFullRemote = true
			continue
		}
		filtered = append(filtered, item)
	}
	if hasFullRemote {
		locations.WorkLocations = filtered
		v := true
		locations.RemoteWorkPossible = &v
	}
}
