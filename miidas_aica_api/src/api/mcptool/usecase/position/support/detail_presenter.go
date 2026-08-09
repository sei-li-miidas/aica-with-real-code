package support

import (
	"cmp"
	"slices"
	"strconv"

	pmodel "aica/api/api/mcptool/usecase/position/model"
	"aica/api/api/mcptool/usecase/shared_dto"
	"aica/api/domain/public/master"
	"aica/api/domain/user/apply/position"
	"aica/api/domain/user/apply/vo"
	willPosition "aica/api/domain/user/profile/will/position"
	vo2 "aica/api/sdk/vo"
)

const overseaName = "海外"

func ShowRawInputValueText(v *vo.ValueText) *shared_dto.ValueText {
	return showRawInputValueText(v)
}

func ShowRemoteWork(r *position.RemoteWork, findMasterFunc func(id int) string) *shared_dto.ValueText {
	return showRemoteWork(r, findMasterFunc)
}

func ShowWorkAddresses(was *position.WorkAddresses, willWas willPosition.WorkAddress, masterCache *master.CacheProvider) *pmodel.WorkAddresses {
	return showWorkAddresses(was, willWas, masterCache)
}

func ShowJobs(jobs position.Jobs, masterCache *master.CacheProvider) []pmodel.Job {
	return showJobs(jobs, masterCache)
}

func ShowRegularOutsourcing(r *position.RegularOutsourcing) *pmodel.RegularOutsourcing {
	return showRegularOutsourcing(r)
}

func ShowCommissionOutsourcing(fee string, businessDescription string) *pmodel.CommissionOutsourcing {
	return showCommissionOutsourcing(fee, businessDescription)
}

func ShowSpotOutsourcing(s *position.SpotOutsourcing) *pmodel.SpotOutsourcing {
	return showSpotOutsourcing(s)
}

func ShowSpotJobRequest(p *position.Position, spotJobRequestMap map[master.SpotJobRequestID]*master.SpotJobRequest) *pmodel.SpotJobRequest {
	return showSpotJobRequest(p, spotJobRequestMap)
}

func ShowSpotExpLevels(
	p *position.Position,
	spotJobRequestMap map[master.SpotJobRequestID]*master.SpotJobRequest,
	getExpLevelFunc func(pattern master.SpotExpLevelPattern) master.SpotExpLevels,
) *[]pmodel.SpotExpLevels {
	return showSpotExpLevels(p, spotJobRequestMap, getExpLevelFunc)
}

func ShowOutsourcingAppeal(p *position.Position) *pmodel.OutsourcingAppeal {
	return showOutsourcingAppeal(p)
}

func ShowModelAnnualIncome(m *position.ModelAnnualIncome) *pmodel.ModelAnnualIncome {
	return showModelAnnualIncome(m)
}

func ShowHREvaluationType(h *position.HREvaluationType) *pmodel.HREvaluationType {
	return showHREvaluationType(h)
}

func ShowOvertimeSalary(h *position.OvertimeSalary) *pmodel.OvertimeSalary {
	return showOvertimeSalary(h)
}

func ShowHREvaluationCompetency(h *position.HREvaluationCompetency) *pmodel.HREvaluationCompetency {
	return showHREvaluationCompetency(h)
}

func ShowValueTextWithOptions(v *vo.ValueText, findMastersFunc func() []*master.TraitPositionOptionForUser) *pmodel.ValueTextWithOptions {
	return showValueTextWithOptions(v, findMastersFunc)
}

func ShowJobChange(in *vo2.FromTo, g *position.GuaranteedIncome) *pmodel.JobChange {
	return showJobChange(in, g)
}

func ShowInterview(isSpot bool, interview *position.Interview, masterCache *master.CacheProvider) *pmodel.InterviewDetail {
	return showInterview(isSpot, interview, masterCache)
}

// 名称がなく入力値をそのまま使う場合
// 例.
// - 基本月給 (ptj_base_monthly_salary)
// - 組織_2 配属部署人数 (ptj_org_trend__section_member_qty)
func showRawInputValueText(v *vo.ValueText) *shared_dto.ValueText {
	if v == nil {
		return nil
	}
	return &shared_dto.ValueText{
		ID:   v.ID,
		Name: strconv.Itoa(v.ID),
		Note: v.Text,
	}
}

func showRemoteWork(r *position.RemoteWork, findMasterFunc func(id int) string) *shared_dto.ValueText {
	if r == nil {
		return nil
	}
	return &shared_dto.ValueText{
		ID:   r.ID,
		Name: findMasterFunc(r.ID),
		Note: r.Text,
	}
}

// 希望勤務地に応じてポジション勤務地の並び替えを行う
// 1. 希望勤務地の「市区町村」がポジション勤務地と一致する場合、最上位に表示
// 2. 希望勤務地の「都道府県」がポジション勤務地と一致する場合、一致した「市区町村」の後ろに表示
// 3. 希望勤務地で海外がポジション勤務地と一致する場合、一致した「都道府県」の後ろに表示
// 4. 一致する勤務地がない場合はマスタ順
func showWorkAddresses(was *position.WorkAddresses, willWas willPosition.WorkAddress, masterCache *master.CacheProvider) *pmodel.WorkAddresses {
	if was == nil {
		return nil
	}
	prefMap := masterCache.PrefectureMap()
	cityMap := masterCache.CityMap()

	// 希望勤務地
	willCitySet := willWas.Value.Cities.ToSet()
	willPrefSet := willWas.Value.Prefectures.ToSet()

	ret := pmodel.WorkAddresses{Note: was.Text}
	values := make([]pmodel.WorkAddress, 0, len(was.Values))
	for _, v := range was.Values {
		wa := pmodel.WorkAddress{
			ID:       v.ID,
			Note:     v.Text,
			Priority: 4, // 希望勤務地に一致しなければ末尾
		}
		if v.IsOverseas() { // 海外
			wa.Name = overseaName
			if willWas.Value.OverseasFlg {
				wa.Priority = 3 // 海外が一致
			}
			values = append(values, wa)
			continue
		}

		var name string // 都道府県+市区町村のラベル
		// 都道府県
		prefID, _ := v.PrefectureID()
		name = func() string {
			if pref, found := prefMap[prefID]; found {
				return pref.Name
			}
			return ""
		}()
		if willPrefSet.ContainsOne(prefID) {
			wa.Priority = 2
		}
		// 市区町村
		if ok, _ := v.IsCityCodeAssigned(); ok {
			cityID, _ := v.CityID()
			name += func() string {
				if city, found := cityMap[cityID]; found {
					return string(city.Name)
				}
				return ""
			}()
			if willCitySet.ContainsOne(cityID) {
				wa.Priority = 1 // 市区町村まで一致
			}
		}
		wa.Name = name
		values = append(values, wa)
	}

	slices.SortStableFunc(values, func(a, b pmodel.WorkAddress) int { return cmp.Compare(a.Priority, b.Priority) })
	ret.Values = values
	return &ret
}

func showJobs(jobs position.Jobs, masterCache *master.CacheProvider) []pmodel.Job {
	if jobs == nil {
		return nil
	}

	jobSmallMap := masterCache.JobTypeSmallMap()
	skillMap := masterCache.SkillMap()
	skillGroupMap := masterCache.SkillGroupMap()
	ret := make([]pmodel.Job, 0, len(jobs))
	for _, pj := range jobs {
		skillGroups := make([]pmodel.SkillGroup, 0, len(pj.SkillGroups))
		for _, psg := range pj.SkillGroups {
			if s, found := skillGroupMap[master.SkillGroupID(psg.ID)]; found {
				skillGroups = append(skillGroups, pmodel.SkillGroup{
					ID:          psg.ID,
					Name:        s.Name,
					DummyGroups: convertSkills2DummyGroups(psg.Skills, skillMap),
				})
			} else {
				skillGroups = append(skillGroups, pmodel.SkillGroup{
					ID:          psg.ID,
					Name:        "",
					DummyGroups: convertSkills2DummyGroups(psg.Skills, skillMap),
				})
			}
		}
		if j, found := jobSmallMap[pj.SmallID]; found {
			ret = append(ret, pmodel.Job{
				SmallID:     pj.SmallID,
				Name:        j.Name,
				Main:        pj.Main,
				SkillGroups: skillGroups,
			})
		} else {
			ret = append(ret, pmodel.Job{
				SmallID:     pj.SmallID,
				Name:        "",
				Main:        pj.Main,
				SkillGroups: skillGroups,
			})
		}
	}
	return ret
}

func convertSkills2DummyGroups(skills []position.Skill, skillMap master.SkillMap) []pmodel.DummyGroup {
	dummyGroupMap := map[string][]pmodel.Skill{}
	dgOrder := []string{}
	for _, s := range skills {
		if ms, found := skillMap[master.SkillID(s.ID)]; found {
			dummyGroupName := ms.Name.GetDummyGroupName()
			// 順番を担保するために初出の場合はキーの順番を保持
			if _, found := dummyGroupMap[dummyGroupName]; !found {
				dgOrder = append(dgOrder, dummyGroupName)
			}
			dummyGroupMap[dummyGroupName] = append(dummyGroupMap[dummyGroupName], pmodel.Skill{
				ID:   s.ID,
				Name: ms.Name.GetDisplayName(),
				Main: s.IsMain,
			})
		} // 存在しないとき、そのスキルは表示しない
	}
	var dummyGroups []pmodel.DummyGroup
	for _, name := range dgOrder {
		dummyGroups = append(dummyGroups, pmodel.DummyGroup{
			Name:   name,
			Skills: dummyGroupMap[name],
		})
	}

	return dummyGroups
}

func showRegularOutsourcing(r *position.RegularOutsourcing) *pmodel.RegularOutsourcing {
	if r == nil {
		return nil
	}

	return &pmodel.RegularOutsourcing{
		Fee:                r.Fee,
		ContractPeriod:     r.ContractPeriod,
		MonthlyWorkingTime: r.MonthlyWorkingTime,
		Incentive:          r.Incentive,
		MonthlyFee:         r.MonthlyFee,
		HourlyFee:          r.HourlyFee,
		Note:               r.Text,
	}
}

// 他の業務委託のレスポンスと形を合わせる
func showCommissionOutsourcing(fee string, businessDescription string) *pmodel.CommissionOutsourcing {
	if len(fee) == 0 && len(businessDescription) == 0 {
		return nil
	}
	return &pmodel.CommissionOutsourcing{
		Fee:                 fee,
		BusinessDescription: businessDescription,
	}
}

func showSpotOutsourcing(s *position.SpotOutsourcing) *pmodel.SpotOutsourcing {
	if s == nil {
		return nil
	}

	return &pmodel.SpotOutsourcing{
		Fee:         s.Fee,
		WorkingTime: s.WorkingTime,
		HourlyFee:   s.HourlyFee,
		Note:        s.Text,
	}
}

func showSpotJobRequest(p *position.Position, spotJobRequestMap map[master.SpotJobRequestID]*master.SpotJobRequest) *pmodel.SpotJobRequest {
	if !p.IsSpot() || p.SpotJobRequest == nil {
		return nil
	}

	jr, found := spotJobRequestMap[master.SpotJobRequestID(p.SpotJobRequest.ID)]
	if found {
		return &pmodel.SpotJobRequest{
			ID:                  p.SpotJobRequest.ID,
			Name:                jr.Name,
			SpotExpLevelPattern: string(jr.SpotExpLevelPattern),
		}
	} else {
		return &pmodel.SpotJobRequest{
			ID:                  p.SpotJobRequest.ID,
			Name:                "",
			SpotExpLevelPattern: "",
		}
	}
}

func showSpotExpLevels(
	p *position.Position,
	spotJobRequestMap map[master.SpotJobRequestID]*master.SpotJobRequest,
	getExpLevelFunc func(pattern master.SpotExpLevelPattern) master.SpotExpLevels,
) *[]pmodel.SpotExpLevels {

	if !p.IsSpot() {
		return nil
	}

	var expLevels []*master.ClassifiedSpotExpLevels
	if p.SpotJobRequest == nil {
		// スポット依頼内容が未設定の場合、パターン無しの熟練度を返す
		expLevels = getExpLevelFunc(master.SpotExpLevelPatternNone).Classify()
	} else {
		jr, found := spotJobRequestMap[master.SpotJobRequestID(p.SpotJobRequest.ID)]
		if found {
			expLevels = getExpLevelFunc(jr.SpotExpLevelPattern).Classify()
		} else { // 存在しない場合、パターン無しの熟練度を返す
			expLevels = getExpLevelFunc(master.SpotExpLevelPatternNone).Classify()
		}
	}

	var ret []pmodel.SpotExpLevels
	for i := range expLevels {
		var retList []shared_dto.IDWithName
		for _, el := range expLevels[i].List {
			retList = append(retList, shared_dto.IDWithName{
				ID:   int(el.ID),
				Name: el.Label,
			})
		}

		ret = append(ret, pmodel.SpotExpLevels{
			ClassNo: expLevels[i].ClassNo,
			List:    retList,
		})
	}

	return &ret
}

func showOutsourcingAppeal(p *position.Position) *pmodel.OutsourcingAppeal {
	if p == nil || p.OutsourcingAppeal == nil || !p.IsOutsourcing() {
		return nil
	}

	appeal := p.OutsourcingAppeal
	return &pmodel.OutsourcingAppeal{
		ExperienceNotEssential: appeal.ExperienceNotEssential,
		WeekendWorker:          appeal.WeekendWorker,
		RemoteWorkType:         appeal.RemoteWorkType,
		TransportationPayment:  appeal.TransportationPayment,
		DailyWage:              appeal.DailyWage,
		OnlineInterview:        appeal.OnlineInterview,
		ShortTimeWorker:        appeal.ShortTimeWorker,
		DailyPayment:           appeal.DailyPayment,
		WorkTimeNegotiable:     appeal.WorkTimeNegotiable,
		WorkType:               appeal.WorkType,
	}
}

func showModelAnnualIncome(m *position.ModelAnnualIncome) *pmodel.ModelAnnualIncome {
	if m == nil {
		return nil
	}

	return &pmodel.ModelAnnualIncome{
		Income20s: m.Income20s,
		Income30s: m.Income30s,
		Income40s: m.Income40s,
		Note:      m.Text,
	}
}

func showHREvaluationType(h *position.HREvaluationType) *pmodel.HREvaluationType {
	if h == nil {
		return nil
	}

	return &pmodel.HREvaluationType{
		Type1: h.Type1,
		Type2: h.Type2,
		Type3: h.Type3,
		Type4: h.Type4,
		Note:  h.Text,
	}
}

func showOvertimeSalary(h *position.OvertimeSalary) *pmodel.OvertimeSalary {
	if h == nil {
		return nil
	}

	return &pmodel.OvertimeSalary{
		HasOvertimeSalary: h.HasOvertimeSalary,
		MonthlyAmount:     h.MonthlyAmount,
		ExpectedHours:     h.ExpectedHours,
	}
}

func showHREvaluationCompetency(h *position.HREvaluationCompetency) *pmodel.HREvaluationCompetency {
	if h == nil {
		return nil
	}

	return &pmodel.HREvaluationCompetency{
		Axes: h.Axes,
		Note: h.Text,
	}
}

func showValueTextWithOptions(v *vo.ValueText, findMastersFunc func() []*master.TraitPositionOptionForUser) *pmodel.ValueTextWithOptions {
	if v == nil {
		return nil
	}

	ret := pmodel.ValueTextWithOptions{}
	for _, opt := range findMastersFunc() {
		ret.Options = append(ret.Options, shared_dto.IDWithName{
			ID:   opt.Value,
			Name: opt.UserSideName,
		})
	}

	ret.ID = v.ID
	ret.Note = v.Text

	return &ret
}

func showJobChange(in *vo2.FromTo, g *position.GuaranteedIncome) *pmodel.JobChange {
	if g == nil || in == nil { // 作り上双方のnilチェックを行っているが片方のみがnilというケースは存在しない
		return nil
	}
	return &pmodel.JobChange{
		Income: &pmodel.IncomeRange{
			From: in.From,
			To:   in.To,
			Note: g.Text,
		},
	}
}

func showInterview(isSpot bool, interview *position.Interview, masterCache *master.CacheProvider) *pmodel.InterviewDetail {
	if isSpot {
		return nil
	}
	return &pmodel.InterviewDetail{
		Shared: pmodel.Shared{
			EstimatedTerm:                interview.Shared.EstimatedTerm,
			InterviewTimes:               interview.Shared.InterviewTimes,
			SelectionAptitudeTestExists:  interview.Shared.SelectionAptitudeTestExists,
			SelectionPaperTestExists:     interview.Shared.SelectionPaperTestExists,
			SelectionPracticalTestExists: interview.Shared.SelectionPracticalTestExists,
			SelectionOtherTestExists:     interview.Shared.SelectionOtherTestExists,
			SelectionRemarks:             interview.Shared.SelectionRemarks,
			CasualDressFlg:               interview.Shared.CasualDressFlg,
			Interviewers: func() []vo2.IntIDNamePair {
				m := masterCache.InterviewerMap()
				tmp := make([]vo2.IntIDNamePair, 0, len(interview.Shared.Interviewers))
				for _, interviewer := range interview.Shared.Interviewers {
					if i, found := m[interviewer]; found {
						tmp = append(tmp, *vo2.NewIntIDNamePair(int(interviewer), i.Name))
					} else {
						tmp = append(tmp, *vo2.NewIntIDNamePair(int(interviewer), ""))
					}
				}
				return tmp
			}(),
			OtherInterviewer: interview.Shared.OtherInterviewer,
			Contact:          interview.Shared.Contact,
		},
		Meeting:        interview.Meeting,
		Online:         interview.Online,
		Phone:          interview.Phone,
		WorkExperience: showInterviewWorkExperience(interview.WorkExperience, masterCache),
	}
}

func showInterviewWorkExperience(w position.WorkExperience, masterCache *master.CacheProvider) pmodel.WorkExperience {
	return pmodel.WorkExperience{
		Pattern: func() vo2.IntIDNamePair {
			if i, found := masterCache.WorkExperiencePatternMap().Get(w.PatternID); found {
				return *vo2.NewIntIDNamePair(w.PatternID, i.Name)
			} else {
				return *vo2.NewIntIDNamePair(w.PatternID, "")
			}
		}(),
		Timing: func() vo2.IntIDNamePair {
			if i, found := masterCache.WorkExperienceTimingMap().Get(w.TimingID); found {
				return *vo2.NewIntIDNamePair(w.TimingID, i.Name)
			} else {
				return *vo2.NewIntIDNamePair(w.TimingID, "")
			}
		}(),
		TimingRemarks:   w.TimingRemarks,
		OtherTimingText: w.OtherTimingText,
		WorkTypes: func() vo2.IntIDNamePairs {
			tmp := make(vo2.IntIDNamePairs, 0, len(w.WorkTypeIDs))
			m := masterCache.WorkExperienceContentTypeMap()
			for _, workTypeID := range w.WorkTypeIDs {
				if i, found := m[workTypeID]; found {
					tmp = append(tmp, *vo2.NewIntIDNamePair(workTypeID, i.Name))
				} else {
					tmp = append(tmp, *vo2.NewIntIDNamePair(workTypeID, ""))
				}
			}
			return tmp
		}(),
		WorkContent: w.WorkContent,
		Timeframe: func() vo2.IntIDNamePair {
			if i, found := masterCache.WorkExperienceTimeframeMap().Get(w.TimeframeID); found {
				return *vo2.NewIntIDNamePair(w.TimeframeID, i.Name)
			} else {
				return *vo2.NewIntIDNamePair(w.TimeframeID, "")
			}
		}(),
		TimeframeRemarks: w.TimeframeRemarks,
		NeedTime: func() vo2.IntIDNamePair {
			if i, found := masterCache.WorkExperienceNeedtimeMap().Get(w.NeedTimeID); found {
				return *vo2.NewIntIDNamePair(w.NeedTimeID, i.Name)
			} else {
				return *vo2.NewIntIDNamePair(w.NeedTimeID, "")
			}
		}(),
		NeedTimeRemarks: w.NeedTimeRemarks,
		Reward: func() vo2.IntIDNamePair {
			if i, found := masterCache.WorkExperienceRewardMap().Get(w.RewardID); found {
				return *vo2.NewIntIDNamePair(w.RewardID, i.Name)
			} else {
				return *vo2.NewIntIDNamePair(w.RewardID, "")
			}
		}(),
		RewardValue:   w.RewardValue,
		RewardRemarks: w.RewardRemarks,
	}
}
