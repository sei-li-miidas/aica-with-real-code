package position_tag

import (
	"aica/api/domain/public/master"
	"aica/api/domain/user/apply/company"
	"aica/api/domain/user/apply/position"
)

// GetList 業務委託ポジションのアピールポイントタグを表示用に作る。該当するタグはすべて返す。
func GetList(pos *position.Position, com *company.Company) []position.Tag {
	// 業務委託ポジション以外はタグなし
	if !pos.IsOutsourcing() {
		return []position.Tag{}
	}

	ret := []position.Tag{}

	isRegular := pos.RegularOutsourcing != nil
	isSpot := pos.SpotOutsourcing != nil
	canRemoteWorkFully := false
	canOnlineInterview := false

	// 企業側ポジション設定のアピールポイント設定から直接持ってくるタグ
	oa := pos.OutsourcingAppeal
	if oa != nil {
		if oa.ExperienceNotEssential {
			ret = append(ret, position.TagInexperiencedWelcome())
		}
		if oa.WeekendWorker {
			ret = append(ret, position.TagWorkOnHoliday())
		}
		if oa.RemoteWorkType != nil {
			switch *oa.RemoteWorkType {
			case 1:
				ret = append(ret, position.TagTeleworkFully())
				canRemoteWorkFully = true
			case 2:
				ret = append(ret, position.TagTeleworkPartly())
			}
		}
		if oa.DailyWage != nil {
			if *oa.DailyWage >= 30000 {
				ret = append(ret, position.TagPayOver30000YenPerDay())
			} else if *oa.DailyWage >= 25000 {
				ret = append(ret, position.TagPayOver25000YenPerDay())
			}
		}
		if oa.ShortTimeWorker {
			ret = append(ret, position.TagWorkShortTime())
		}
		if oa.DailyPayment {
			ret = append(ret, position.TagPayOnSameDay())
		}
		if oa.WorkTimeNegotiable {
			ret = append(ret, position.TagNegotiableWorkingHours())
		}
		if isSpot && oa.OnlineInterview {
			ret = append(ret, position.TagOnlineJobInterview())
			canOnlineInterview = true
		}
	}

	// その他、企業情報やポジション情報から取ってくるタグ
	for _, id := range com.Detail.AppealPoint.GetIntIDs() {
		switch id {
		case master.CtxCompanyAppealVenture:
			ret = append(ret, position.TagVentureCompany())
		case master.CtxCompanyAppealStableStage:
			if !isSpot {
				ret = append(ret, position.TagStableBusiness())
			}
		}
	}
	for _, id := range com.Detail.CapitalType.GetIntIDs() {
		switch id {
		case master.CtxCapitalTypeForeign:
			ret = append(ret, position.TagForeignCompany())
		case master.CtxCapitalTypeListed:
			ret = append(ret, position.TagListedCompany())
		}
	}
	if !isSpot && !canOnlineInterview {
		if pos.Interview.Online.EnableFlg {
			ret = append(ret, position.TagOnlineJobInterview())
		} else if pos.Interview.Meeting.EnableFlg && pos.Interview.Meeting.TransportationPaymentFlg {
			ret = append(ret, position.TagPayTransportCostForInterview())
		}
	}
	if pos.RegularOutsourcing != nil {
		if pos.RegularOutsourcing.MonthlyWorkingTime <= 20 {
			ret = append(ret, position.TagWorkUnder20HoursPerMonth())
		} else if pos.RegularOutsourcing.MonthlyWorkingTime <= 40 {
			ret = append(ret, position.TagWorkUnder40HoursPerMonth())
		} else if pos.RegularOutsourcing.MonthlyWorkingTime >= 140 {
			ret = append(ret, position.TagWorkOver140HoursPerMonth())
		}

		if pos.RegularOutsourcing.HourlyFee >= 5000 {
			ret = append(ret, position.TagPayOver5000YenPerHour())
		} else if pos.RegularOutsourcing.HourlyFee >= 4000 {
			ret = append(ret, position.TagPayOver4000YenPerHour())
		} else if pos.RegularOutsourcing.HourlyFee >= 3000 {
			ret = append(ret, position.TagPayOver3000YenPerHour())
		}
	}
	if pos.SpotOutsourcing != nil {
		if pos.SpotOutsourcing.WorkingTime <= 20 {
			ret = append(ret, position.TagWorkUnder20HoursPerMonth())
		} else if pos.SpotOutsourcing.WorkingTime <= 40 {
			ret = append(ret, position.TagWorkUnder40HoursPerMonth())
		} else if pos.SpotOutsourcing.WorkingTime >= 140 {
			ret = append(ret, position.TagWorkOver140HoursPerMonth())
		}

		if pos.SpotOutsourcing.HourlyFee >= 5000 {
			ret = append(ret, position.TagPayOver5000YenPerHour())
		} else if pos.SpotOutsourcing.HourlyFee >= 4000 {
			ret = append(ret, position.TagPayOver4000YenPerHour())
		} else if pos.SpotOutsourcing.HourlyFee >= 3000 {
			ret = append(ret, position.TagPayOver3000YenPerHour())
		}
	}
	if pos.GetRemoteWork() != nil {
		switch *pos.GetRemoteWork() {
		case master.RemoteWorkOkConditionally:
			ret = append(ret, position.TagTeleworkPartly())
		case master.RemoteWorkOkFully:
			ret = append(ret, position.TagTeleworkFully())
			canRemoteWorkFully = true
		}
	}
	if pos.ContractExtension != nil && pos.ContractExtension.ID == master.ContractExtensionOk {
		ret = append(ret, position.TagLabelExtendContract())
	}
	if isRegular {
		jtlMap := master.Provider().JobTypeLargeMap()
		for _, j := range pos.Jobs {
			if !j.Main {
				continue
			}
			largeID := j.SmallID.JobTypeLargeID()
			if jr, ok := jtlMap[largeID]; ok {
				ret = append(ret, position.Tag{Label: jr.Name})
				break
			}
		}
	}
	if isSpot {
		if i := pos.SpotJobRequest.GetIntPtr(); i != nil {
			jrm := master.Provider().SpotJobRequestMap()
			if jr, ok := jrm[master.SpotJobRequestID(*i)]; ok && jr.SpotJobRequestGenreID != "other" {
				ret = append(ret, position.Tag{Label: jr.Category})
			}
		}
	}
	if !canRemoteWorkFully {
		if oa != nil && oa.TransportationPayment {
			ret = append(ret, position.TagPayTransportCost())
		}
	}
	for _, id := range pos.WorkingEnvironment.GetIntIDs() {
		switch id {
		case master.WorkingEnvironmentClothes:
			if !canRemoteWorkFully {
				ret = append(ret, position.TagDressCasuallyToWork())
			}
		case master.WorkingEnvironmentByCar:
			if !canRemoteWorkFully {
				ret = append(ret, position.TagCommuteByCar())
			}
		case master.WorkingEnvironmentWalk5Min:
			if !canRemoteWorkFully {
				ret = append(ret, position.TagWithin5MinutesWalk())
			}
		case master.WorkingEnvironmentWalk10Min:
			if !canRemoteWorkFully {
				ret = append(ret, position.TagWithin10MinutesWalk())
			}
		case master.WorkingEnvironmentNotRained:
			if !canRemoteWorkFully {
				ret = append(ret, position.TagWithoutGettingWetFromStation())
			}
		case master.WorkingEnvironmentEnglish:
			ret = append(ret, position.TagUseEnglishSkills())
		case master.WorkingEnvironmentTimeArrangeable:
			ret = append(ret, position.TagWorkFlexibly())
		}
	}
	return ret
}
