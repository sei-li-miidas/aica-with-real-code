package jobtype

import (
	miidasMaster "aica/api/domain/public/master"
	"strings"

	"gorm.io/gorm"
)

type (
	JobTypeRepository struct {
		db *gorm.DB
	}

	JobTypeSearchResult struct {
		ID          int
		Name        string
		Description string
		Distance    float64
	}

	JobTypePositionSearchToolMapping struct {
		JobTypeSmallID int    `gorm:"column:job_type_small_id"`
		JobTypeName    string `gorm:"column:job_type_name"`
		ToolName       string `gorm:"column:tool_name"`
	}
)

// NewJobTypeRepository .
func NewJobTypeRepository(db *gorm.DB) *JobTypeRepository {
	return &JobTypeRepository{
		db: db,
	}
}

func (r *JobTypeRepository) SemanticSearch(embedding string, distance float64, addConditions func(*gorm.DB) *gorm.DB) ([]*JobTypeSearchResult, error) {
	query := r.db.
		Table("public.job_type_small_vector").
		Model(JobTypeSmallVector{}).
		Select("id, name, description, embedding <=> ? as distance", embedding).
		Joins("JOIN public.job_type_small ON job_type_small.id = job_type_small_vector.job_type_small_id").
		Where("embedding <=> ? <= ?", embedding, distance).
		Order("distance")
	if addConditions != nil {
		query = addConditions(query)
	}

	var jobtypes []*JobTypeSearchResult
	result := query.Find(&jobtypes)

	if result.Error != nil {
		return nil, result.Error
	}

	return jobtypes, nil
}

func (r *JobTypeRepository) SearchByNature(wantedNatures []string, unwantedNatures []string, minNatureScore float32, minJobTypeScore float32, maxPriorExperienceRequired float32) ([]*JobTypeSearchResult, error) {
	var jobtypes []*JobTypeSearchResult

	subQuery := r.db.Table("jobtag_natures jn").Select("jmm.occupation_id", "MAX(jmm.score) max_score").Joins("JOIN jobtag_occupation_nature_scores jons ON jons.nature_id = jn.nature_id AND jons.score > ?", minNatureScore).Joins("JOIN jobtag_occupations jo ON jo.occupation_id = jons.occupation_id AND jo.prior_experience_required < ?", maxPriorExperienceRequired).Joins("JOIN jobtag_miidas_mapping jmm ON jmm.occupation_id = jons.occupation_id").Group("jmm.occupation_id").Having("MAX(jmm.score) > ?", minJobTypeScore)
	if len(wantedNatures) > 0 {
		subQuery = subQuery.Where("label IN (?)", wantedNatures)
	}
	if len(unwantedNatures) > 0 {
		subQuery = subQuery.Where("label NOT IN (?)", unwantedNatures)
	}

	result := r.db.Table("job_type_small jts").Select("jts.*").Joins("join jobtag_miidas_mapping jmm ON jmm.job_type_small_id = jts.id").Joins("join (?) most_matching on most_matching.occupation_id = jmm.occupation_id and jmm.score = most_matching.max_score", subQuery).Group("jts.id").Order("MAX(most_matching.max_score) desc").Limit(10).Find(&jobtypes)
	if result.Error != nil {
		return nil, result.Error
	}

	return jobtypes, nil
}

func (r *JobTypeRepository) GetMultiple(ids []miidasMaster.JobTypeSmallID) ([]*JobTypeSmall, error) {
	var jobtypes []*JobTypeSmall
	result := r.db.Find(&jobtypes, ids)
	if result.Error != nil {
		return nil, result.Error
	}

	return jobtypes, nil
}

func (r *JobTypeRepository) GetMultipleByNames(names []string) ([]*JobTypeSmall, error) {
	var jobtypes []*JobTypeSmall
	result := r.db.Table("public.job_type_small").Where("name IN ?", names).Find(&jobtypes)
	if result.Error != nil {
		return nil, result.Error
	}

	return jobtypes, nil
}

func (r *JobTypeRepository) All() ([]*JobTypeSmall, error) {
	var jobtypes []*JobTypeSmall
	result := r.db.Find(&jobtypes)
	if result.Error != nil {
		return nil, result.Error
	}

	return jobtypes, nil
}

func (r *JobTypeRepository) GetPositionSearchToolMappings(toolNames []string) ([]*JobTypePositionSearchToolMapping, error) {
	if len(toolNames) == 0 {
		return nil, nil
	}

	normalizedToolNames := make([]string, 0, len(toolNames))
	for _, toolName := range toolNames {
		if strings.TrimSpace(toolName) == "" {
			continue
		}
		normalizedToolNames = append(normalizedToolNames, strings.TrimSpace(toolName))
	}
	if len(normalizedToolNames) == 0 {
		return nil, nil
	}

	var mappings []*JobTypePositionSearchToolMapping
	result := r.db.
		Table("public.job_type_to_position_search_tools jtst").
		Select("jtst.job_type_small_id, jts.name as job_type_name, jtst.tool_name").
		Joins("JOIN public.job_type_small jts ON jts.id = jtst.job_type_small_id").
		Where("jtst.deleted_at IS NULL").
		Where("jtst.tool_name IN ?", normalizedToolNames).
		Order("jtst.tool_name ASC, jtst.job_type_small_id ASC").
		Find(&mappings)
	if result.Error != nil {
		return nil, result.Error
	}

	return mappings, nil
}

func (r *JobTypeRepository) DeleteByIds(ids []int) error {
	return r.db.Delete(&JobTypeSmallVector{}, ids).Error
}

func (r *JobTypeRepository) DeleteAll() error {
	return r.db.Where("1 = 1").Delete(&JobTypeSmallVector{}).Error
}
