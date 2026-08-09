package support

import (
	pmodel "aica/api/api/mcptool/usecase/position/model"
	"aica/api/domain/public/master"
	"aica/api/domain/user/apply/position"
	"aica/api/domain/user/apply/vo"
	willPosition "aica/api/domain/user/profile/will/position"
	vo2 "aica/api/sdk/vo"
	"aica/api/sdk/vo/xsv"
	"reflect"
	"testing"
	"unsafe"
)

func setMasterCache(cache *master.Cache) {
	cp := master.Provider()
	field := reflect.ValueOf(cp).Elem().FieldByName("cache")
	reflect.NewAt(field.Type(), unsafe.Pointer(field.UnsafeAddr())).Elem().Set(reflect.ValueOf(cache))
}

func TestDetailPresenter_WrappersAndInternals(t *testing.T) {
	setMasterCache(&master.Cache{
		Prefectures: master.Prefectures{
			&master.Prefecture{ID: 13, Name: "東京都"},
		},
		Cities: master.Cities{
			&master.City{ID: 13101, Name: "千代田区", PrefectureID: 13},
		},
		JobTypeSmalls: master.JobTypeSmalls{
			&master.JobTypeSmall{ID: 1, Name: "SE"},
		},
		SkillGroups: []*master.SkillGroup{
			{ID: 100, Name: "言語"},
		},
		Skills: []*master.Skill{
			{ID: 1, Name: "言語（all）$Go"},
		},
		SpotJobRequests: master.SpotJobRequests{
			&master.SpotJobRequest{ID: 1, Name: "req1", SpotExpLevelPattern: master.SpotExpLevelPatternA},
		},
		SpotExpLevels: master.SpotExpLevels{
			&master.SpotExpLevel{ID: 1, Label: "L1", ClassNo: 1, Pattern: master.SpotExpLevelPatternA},
			&master.SpotExpLevel{ID: 2, Label: "L2", ClassNo: 1, Pattern: master.SpotExpLevelPatternNone},
		},
		Interviewers: []*master.Interviewer{
			{ID: 1, Name: "面接官A"},
		},
		WorkExperiencePatterns: []*master.WorkExperiencePattern{
			{ID: 1, Name: "実施方式A"},
		},
		WorkExperienceTimings: []*master.WorkExperienceTiming{
			{ID: 1, Name: "タイミングA"},
		},
		WorkExperienceContentTypes: []*master.WorkExperienceContentType{
			{ID: 1, Name: "内容A"},
		},
		WorkExperienceTimeframes: []*master.WorkExperienceTimeframe{
			{ID: 1, Name: "日時A"},
		},
		WorkExperienceNeedtimes: []*master.WorkExperienceNeedtime{
			{ID: 1, Name: "所要A"},
		},
		WorkExperienceRewards: []*master.WorkExperienceReward{
			{ID: 1, Name: "報酬A"},
		},
	})

	if ShowRawInputValueText(nil) != nil {
		t.Fatalf("expected nil")
	}
	if ShowRemoteWork(nil, func(_ int) string { return "" }) != nil {
		t.Fatalf("expected nil")
	}
	if ShowWorkAddresses(nil, willPosition.WorkAddress{}, master.Provider()) != nil {
		t.Fatalf("expected nil")
	}
	if ShowJobs(nil, master.Provider()) != nil {
		t.Fatalf("expected nil")
	}
	if ShowRegularOutsourcing(nil) != nil {
		t.Fatalf("expected nil")
	}
	if ShowCommissionOutsourcing("", "") != nil {
		t.Fatalf("expected nil")
	}
	if ShowSpotOutsourcing(nil) != nil {
		t.Fatalf("expected nil")
	}
	if ShowOutsourcingAppeal(nil) != nil {
		t.Fatalf("expected nil")
	}
	if ShowModelAnnualIncome(nil) != nil {
		t.Fatalf("expected nil")
	}
	if ShowHREvaluationType(nil) != nil {
		t.Fatalf("expected nil")
	}
	if ShowOvertimeSalary(nil) != nil {
		t.Fatalf("expected nil")
	}
	if ShowHREvaluationCompetency(nil) != nil {
		t.Fatalf("expected nil")
	}
	if ShowValueTextWithOptions(nil, func() []*master.TraitPositionOptionForUser { return nil }) != nil {
		t.Fatalf("expected nil")
	}
	if ShowJobChange(nil, nil) != nil {
		t.Fatalf("expected nil")
	}
	if ShowInterview(true, &position.Interview{}, master.Provider()) != nil {
		t.Fatalf("expected nil")
	}

	_ = ShowRawInputValueText(&vo.ValueText{ID: 3, Text: "memo"})
	_ = ShowRemoteWork(&position.RemoteWork{ID: 2, Text: "r"}, func(_ int) string { return "あり" })
	_ = ShowWorkAddresses(
		&position.WorkAddresses{
			Text: "note",
			Values: position.WorkAddressList{
				{ID: master.NewWorkAddressID(true, 13, 0), Text: "pref"},
				{ID: master.NewWorkAddressID(true, 13, 13101), Text: "city"},
				{ID: master.NewWorkAddressID(true, 13, 13102), Text: "unknown-city"},
				{ID: master.NewWorkAddressID(false, 0, 0), Text: "os"},
			},
		},
		willPosition.WorkAddress{
			Value: willPosition.WorkAddressValue{
				OverseasFlg: true,
				Prefectures: willPosition.Prefectures{13},
				Cities:      willPosition.Cities{13101},
			},
		},
		master.Provider(),
	)
	_ = ShowJobs(position.Jobs{
		{SmallID: 1, Main: true, SkillGroups: []position.SkillGroup{{ID: 100, Skills: []position.Skill{{ID: 1, IsMain: true}}}}},
		{SmallID: 999, Main: false, SkillGroups: []position.SkillGroup{{ID: 999, Skills: []position.Skill{{ID: 999}}}}},
	}, master.Provider())
	_ = ShowRegularOutsourcing(&position.RegularOutsourcing{Fee: 1, Text: "x"})
	_ = ShowCommissionOutsourcing("100%", "biz")
	_ = ShowSpotOutsourcing(&position.SpotOutsourcing{Fee: 1, Text: "x"})
	_ = ShowSpotJobRequest(
		&position.Position{
			Detail: position.Detail{
				EmploymentType: &vo.ValueText{ID: int(master.PositionEmploymentTypeIDSpotOutsourcing)},
				SpotJobRequest: &vo.ValueText{ID: 1},
			},
		},
		master.Provider().SpotJobRequestMap(),
	)
	_ = ShowSpotJobRequest(
		&position.Position{
			Detail: position.Detail{
				EmploymentType: &vo.ValueText{ID: int(master.PositionEmploymentTypeIDSpotOutsourcing)},
				SpotJobRequest: &vo.ValueText{ID: 999},
			},
		},
		master.Provider().SpotJobRequestMap(),
	)
	_ = ShowSpotJobRequest(
		&position.Position{
			Detail: position.Detail{
				EmploymentType: &vo.ValueText{ID: int(master.PositionEmploymentTypeIDEmployee)},
				SpotJobRequest: &vo.ValueText{ID: 1},
			},
		},
		master.Provider().SpotJobRequestMap(),
	)
	_ = ShowSpotExpLevels(
		&position.Position{
			Detail: position.Detail{
				EmploymentType: &vo.ValueText{ID: int(master.PositionEmploymentTypeIDSpotOutsourcing)},
				SpotJobRequest: &vo.ValueText{ID: 1},
			},
		},
		master.Provider().SpotJobRequestMap(),
		master.Provider().SpotExpLevels().GetByPattern,
	)
	_ = ShowSpotExpLevels(
		&position.Position{
			Detail: position.Detail{
				EmploymentType: &vo.ValueText{ID: int(master.PositionEmploymentTypeIDSpotOutsourcing)},
			},
		},
		master.Provider().SpotJobRequestMap(),
		master.Provider().SpotExpLevels().GetByPattern,
	)
	_ = ShowSpotExpLevels(
		&position.Position{
			Detail: position.Detail{
				EmploymentType: &vo.ValueText{ID: int(master.PositionEmploymentTypeIDSpotOutsourcing)},
				SpotJobRequest: &vo.ValueText{ID: 999},
			},
		},
		master.Provider().SpotJobRequestMap(),
		master.Provider().SpotExpLevels().GetByPattern,
	)
	_ = ShowSpotExpLevels(
		&position.Position{
			Detail: position.Detail{
				EmploymentType: &vo.ValueText{ID: int(master.PositionEmploymentTypeIDEmployee)},
			},
		},
		master.Provider().SpotJobRequestMap(),
		master.Provider().SpotExpLevels().GetByPattern,
	)
	_ = ShowOutsourcingAppeal(&position.Position{
		Detail: position.Detail{
			EmploymentType:    &vo.ValueText{ID: int(master.PositionEmploymentTypeIDOutsourcing)},
			OutsourcingAppeal: &position.OutsourcingAppeal{ExperienceNotEssential: true},
		},
	})
	_ = ShowModelAnnualIncome(&position.ModelAnnualIncome{Income20s: 1, Text: "x"})
	_ = ShowHREvaluationType(&position.HREvaluationType{Type1: 1, Text: "x"})
	_ = ShowOvertimeSalary(&position.OvertimeSalary{HasOvertimeSalary: 1})
	_ = ShowHREvaluationCompetency(&position.HREvaluationCompetency{})
	_ = ShowValueTextWithOptions(&vo.ValueText{ID: 1, Text: "n"}, func() []*master.TraitPositionOptionForUser {
		return []*master.TraitPositionOptionForUser{{Value: 1, UserSideName: "u"}}
	})
	_ = ShowJobChange(&vo2.FromTo{From: 100, To: 200}, &position.GuaranteedIncome{Text: "g"})
	_ = ShowInterview(false, &position.Interview{
		Shared: position.SharedSetting{
			Interviewers: xsv.IntCSV[master.InterviewerID]{1, 999},
		},
		WorkExperience: position.WorkExperience{
			PatternID:   1,
			TimingID:    1,
			WorkTypeIDs: xsv.IntTSV[master.WorkExperienceContentTypeID]{1, 999},
			TimeframeID: 1,
			NeedTimeID:  1,
			RewardID:    1,
		},
	}, master.Provider())
}

func TestShowInterviewWorkExperience_UnknownMasterFallback(t *testing.T) {
	setMasterCache(&master.Cache{})
	out := showInterviewWorkExperience(position.WorkExperience{
		PatternID:   999,
		TimingID:    999,
		WorkTypeIDs: xsv.IntTSV[master.WorkExperienceContentTypeID]{999},
		TimeframeID: 999,
		NeedTimeID:  999,
		RewardID:    999,
	}, master.Provider())
	if out.Pattern.Name != "" || out.Timing.Name != "" {
		t.Fatalf("expected fallback empty names")
	}
}

var _ pmodel.WorkAddress
