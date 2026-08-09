package extensions

import (
	jobfilter "aica/api/domain/jobfilter"
	"aica/api/domain/public/master"

	"miidas/m2/user/marketvalue/grpc/iface"
)

type RemoteWorkExtension struct {
	remoteWorkPossible bool
}

func NewRemoteWorkExtension(remoteWorkPossible bool) *RemoteWorkExtension {
	return &RemoteWorkExtension{remoteWorkPossible: remoteWorkPossible}
}

func (e *RemoteWorkExtension) ApplyMV2(_ *iface.Company, _ *iface.Business, positionWill *iface.Position) {
	if !e.remoteWorkPossible {
		return
	}

	positionWill.RemoteWork = &iface.RemoteWork{
		Importance: 3,
		Value: &iface.RemoteWorkValue{
			Exists: []int32{2, 3},
		},
	}
}

func (e *RemoteWorkExtension) BuildSelectedOtherFilterOptions() (string, []string) {
	return "", nil
}

func (e *RemoteWorkExtension) RemoteWorkPossible() bool {
	return e.remoteWorkPossible
}

type PositionKeywordExtension struct {
	keyword string
}

func NewPositionKeywordExtension(keyword string) *PositionKeywordExtension {
	return &PositionKeywordExtension{keyword: keyword}
}

func (e *PositionKeywordExtension) ApplyMV2(_ *iface.Company, _ *iface.Business, _ *iface.Position) {}

func (e *PositionKeywordExtension) BuildSelectedOtherFilterOptions() (string, []string) {
	return "", nil
}

func (e *PositionKeywordExtension) Keyword() string {
	return e.keyword
}

type SkillExtension struct {
	skillGroup     *jobfilter.JobSearchFilterOtherFilter
	selectedSkills master.Skills
}

func NewSkillExtension(skillGroup *jobfilter.JobSearchFilterOtherFilter, selectedSkills master.Skills) *SkillExtension {
	return &SkillExtension{skillGroup: skillGroup, selectedSkills: selectedSkills}
}

func (e *SkillExtension) ApplyMV2(_ *iface.Company, _ *iface.Business, positionWill *iface.Position) {
	if len(e.selectedSkills) == 0 {
		return
	}

	if positionWill.Skill == nil {
		positionWill.Skill = &iface.Skill{
			Importance: 3,
			Value:      []int32{},
		}
	}

	for _, skill := range e.selectedSkills {
		positionWill.Skill.Value = append(positionWill.Skill.Value, int32(skill.ID))
	}
}

func (e *SkillExtension) BuildSelectedOtherFilterOptions() (string, []string) {
	if e.skillGroup == nil {
		return "", nil
	}

	selected := map[string]struct{}{}
	for _, skill := range e.selectedSkills {
		selected[skill.GetPureName()] = struct{}{}
		selected[skill.GetName()] = struct{}{}
	}

	options := make([]string, 0, len(e.skillGroup.Options))
	for _, opt := range e.skillGroup.Options {
		if opt == nil {
			continue
		}
		_, selectedByValue := selected[opt.Value]
		if selectedByValue {
			options = append(options, opt.Value)
		}
	}

	return e.skillGroup.Name, options
}

type SalesStyleDiveExtension struct {
	name  string
	value int32
}

func NewSalesStyleDiveExtension(name string, value int32) *SalesStyleDiveExtension {
	return &SalesStyleDiveExtension{name: name, value: value}
}

func (e *SalesStyleDiveExtension) ApplyMV2(_ *iface.Company, _ *iface.Business, positionWill *iface.Position) {
	if e.value <= 0 {
		return
	}
	if positionWill.SalesStyleDive == nil {
		positionWill.SalesStyleDive = &iface.SalesStyleDive{}
	}
	positionWill.SalesStyleDive.Importance = 3
	positionWill.SalesStyleDive.Value = &e.value
}

func (e *SalesStyleDiveExtension) BuildSelectedOtherFilterOptions() (string, []string) {
	return "新規飛び込み", []string{e.name}
}
