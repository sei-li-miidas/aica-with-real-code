package params

import (
	"aica/api/api/mcptool/service"
	jobfilter "aica/api/domain/jobfilter"
	"aica/api/domain/public/master"
	"fmt"
)

func Setup(cacheService *service.MiidasCacheService) error {
	if cacheService == nil {
		return fmt.Errorf("cache service is required")
	}

	initITEngineerSearchFilters(cacheService)
	initFinancialSalesSearchFilters(cacheService)

	return nil
}

func buildSkillFilter(cacheService *service.MiidasCacheService, name string) *jobfilter.JobSearchFilterOtherFilter {
	skillGroups := cacheService.GetAllSkillGroups()

	var targetGroup *master.SkillGroup
	for _, group := range skillGroups {
		if group.Name != name {
			continue
		}
		targetGroup = group
		break
	}

	if targetGroup == nil {
		if l := cacheService.Logger(); l != nil {
			l.Error(
				"failed to build job specific search filter: skill group not found",
				"skill_group_name", name,
				"cached_skill_group_names", skillGroupNames(skillGroups),
				"cached_skill_group_count", len(skillGroups),
			)
		}
		return nil
	}

	return buildSkillFilterWithGroup(cacheService, targetGroup, name)
}

func buildSkillFilterByGroupID(cacheService *service.MiidasCacheService, groupID master.SkillGroupID, fallbackName string) *jobfilter.JobSearchFilterOtherFilter {
	for _, group := range cacheService.GetAllSkillGroups() {
		if group.ID != groupID {
			continue
		}
		return buildSkillFilterWithGroup(cacheService, group, fallbackName)
	}

	if l := cacheService.Logger(); l != nil {
		l.Error("failed to build job specific search filter: skill group not found", "skill_group_id", groupID)
	}
	return nil
}

func buildSkillFilterWithGroup(cacheService *service.MiidasCacheService, group *master.SkillGroup, fallbackName string) *jobfilter.JobSearchFilterOtherFilter {
	if group == nil {
		return nil
	}

	filterName := fallbackName
	if group.Name != "" {
		filterName = group.Name
	}

	flags := make([]*jobfilter.JobSearchFilterOtherFilterOption, 0)
	seenOptions := make(map[string]struct{})
	for _, skill := range cacheService.GetAllSkills() {
		if skill.SkillGroupID != group.ID {
			continue
		}
		option := skill.GetPureName()
		if option == "" {
			continue
		}
		if _, seen := seenOptions[option]; seen {
			continue
		}
		seenOptions[option] = struct{}{}
		flags = append(flags, &jobfilter.JobSearchFilterOtherFilterOption{Label: option, Value: option})
	}

	return &jobfilter.JobSearchFilterOtherFilter{Name: filterName, Type: jobfilter.JobSearchFilterTypeMultiple, Options: flags}
}

func findFilterByName(filters []*jobfilter.JobSearchFilterOtherFilter, name string) *jobfilter.JobSearchFilterOtherFilter {
	for _, filter := range filters {
		if filter == nil {
			continue
		}
		if filter.Name == name {
			return filter
		}
	}
	return nil
}

func skillGroupNames(groups master.SkillGroups) []string {
	names := make([]string, 0, len(groups))
	for _, group := range groups {
		if group == nil {
			continue
		}
		names = append(names, group.Name)
	}
	return names
}
