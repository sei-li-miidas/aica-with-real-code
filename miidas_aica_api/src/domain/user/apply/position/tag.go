package position

const (
	// タグ種別（表示アイコン種類）
	tagGenreNone                 = ""
	tagGenreInexperiencedWelcome = "inexperienced_welcome"
	tagGenreWorkTime             = "work_time"
	tagGenreRemote               = "remote"
	tagGenreIncome               = "income"

	// タグ表示名
	tagLabelInexperiencedWelcome         = "未経験歓迎"
	tagLabelWorkOnHoliday                = "土日稼働可能"
	tagLabelTeleworkFully                = "リモートワーク可能（出社なし）"
	tagLabelTeleworkPartly               = "リモートワーク可能（一部出社あり）"
	tagLabelPayOver30000YenPerDay        = "日給30000円以上可能（実績あり）"
	tagLabelPayOver25000YenPerDay        = "日給25000円以上可能（実績あり）"
	tagLabelWorkShortTime                = "スキマ時間での稼働OK"
	tagLabelPayOnSameDay                 = "即日払い"
	tagLabelNegotiableWorkingHours       = "稼働時間応相談"
	tagLabelOnlineJobInterview           = "オンライン面接"
	tagLabelVentureCompany               = "ベンチャー企業"
	tagLabelStableBusiness               = "安定した事業"
	tagLabelForeignCompany               = "外資系企業"
	tagLabelListedCompany                = "上場企業"
	tagLabelPayTransportCostForInterview = "面談交通費支給"
	tagLabelWorkUnder20HoursPerMonth     = "月の稼働が20時間以下"
	tagLabelWorkUnder40HoursPerMonth     = "月の稼働が40時間以下"
	tagLabelWorkOver140HoursPerMonth     = "月の稼働が140時間以上"
	tagLabelPayOver5000YenPerHour        = "時給換算で5000円以上"
	tagLabelPayOver4000YenPerHour        = "時給換算で4000円以上"
	tagLabelPayOver3000YenPerHour        = "時給換算で3000円以上"
	tagLabelExtendContract               = "契約延長あり"
	tagLabelPayTransportCost             = "交通費支給あり"
	tagLabelDressCasuallyToWork          = "私服勤務"
	tagLabelCommuteByCar                 = "マイカー通勤"
	tagLabelWithin5MinutesWalk           = "徒歩5分以内"
	tagLabelWithin10MinutesWalk          = "徒歩10分以内"
	tagLabelWithoutGettingWetFromStation = "駅から雨に濡れない"
	tagLabelUseEnglishSkills             = "英語が活かせる"
	tagLabelWorkFlexibly                 = "出勤時間・退社時間は自由"
)

type Tag struct {
	Genre       string // タグ種別（表示アイコン種類）
	Label       string // タグ表示名
	IsImportant bool   // アピールポイントであるか
}

func TagInexperiencedWelcome() Tag {
	return Tag{
		Genre:       tagGenreInexperiencedWelcome,
		Label:       tagLabelInexperiencedWelcome,
		IsImportant: true,
	}
}
func TagWorkOnHoliday() Tag {
	return Tag{
		Genre:       tagGenreWorkTime,
		Label:       tagLabelWorkOnHoliday,
		IsImportant: true,
	}
}
func TagTeleworkFully() Tag {
	return Tag{
		Genre:       tagGenreRemote,
		Label:       tagLabelTeleworkFully,
		IsImportant: true,
	}
}
func TagTeleworkPartly() Tag {
	return Tag{
		Genre:       tagGenreRemote,
		Label:       tagLabelTeleworkPartly,
		IsImportant: true,
	}
}
func TagPayOver30000YenPerDay() Tag {
	return Tag{
		Genre:       tagGenreIncome,
		Label:       tagLabelPayOver30000YenPerDay,
		IsImportant: true,
	}
}
func TagPayOver25000YenPerDay() Tag {
	return Tag{
		Genre:       tagGenreIncome,
		Label:       tagLabelPayOver25000YenPerDay,
		IsImportant: true,
	}
}
func TagWorkShortTime() Tag {
	return Tag{
		Genre:       tagGenreWorkTime,
		Label:       tagLabelWorkShortTime,
		IsImportant: true,
	}
}
func TagPayOnSameDay() Tag {
	return Tag{
		Genre:       tagGenreNone,
		Label:       tagLabelPayOnSameDay,
		IsImportant: false,
	}
}
func TagNegotiableWorkingHours() Tag {
	return Tag{
		Genre:       tagGenreWorkTime,
		Label:       tagLabelNegotiableWorkingHours,
		IsImportant: true,
	}
}
func TagOnlineJobInterview() Tag {
	return Tag{
		Genre:       tagGenreNone,
		Label:       tagLabelOnlineJobInterview,
		IsImportant: false,
	}
}
func TagVentureCompany() Tag {
	return Tag{
		Genre:       tagGenreNone,
		Label:       tagLabelVentureCompany,
		IsImportant: false,
	}
}
func TagStableBusiness() Tag {
	return Tag{
		Genre:       tagGenreNone,
		Label:       tagLabelStableBusiness,
		IsImportant: false,
	}
}
func TagForeignCompany() Tag {
	return Tag{
		Genre:       tagGenreNone,
		Label:       tagLabelForeignCompany,
		IsImportant: false,
	}
}
func TagListedCompany() Tag {
	return Tag{
		Genre:       tagGenreNone,
		Label:       tagLabelListedCompany,
		IsImportant: false,
	}
}
func TagPayTransportCostForInterview() Tag {
	return Tag{
		Genre:       tagGenreNone,
		Label:       tagLabelPayTransportCostForInterview,
		IsImportant: false,
	}
}
func TagWorkUnder20HoursPerMonth() Tag {
	return Tag{
		Genre:       tagGenreWorkTime,
		Label:       tagLabelWorkUnder20HoursPerMonth,
		IsImportant: true,
	}
}
func TagWorkUnder40HoursPerMonth() Tag {
	return Tag{
		Genre:       tagGenreWorkTime,
		Label:       tagLabelWorkUnder40HoursPerMonth,
		IsImportant: true,
	}
}
func TagWorkOver140HoursPerMonth() Tag {
	return Tag{
		Genre:       tagGenreNone,
		Label:       tagLabelWorkOver140HoursPerMonth,
		IsImportant: false,
	}
}
func TagPayOver5000YenPerHour() Tag {
	return Tag{
		Genre:       tagGenreIncome,
		Label:       tagLabelPayOver5000YenPerHour,
		IsImportant: true,
	}
}
func TagPayOver4000YenPerHour() Tag {
	return Tag{
		Genre:       tagGenreIncome,
		Label:       tagLabelPayOver4000YenPerHour,
		IsImportant: true,
	}
}
func TagPayOver3000YenPerHour() Tag {
	return Tag{
		Genre:       tagGenreIncome,
		Label:       tagLabelPayOver3000YenPerHour,
		IsImportant: true,
	}
}
func TagLabelExtendContract() Tag {
	return Tag{
		Genre:       tagGenreNone,
		Label:       tagLabelExtendContract,
		IsImportant: false,
	}
}
func TagPayTransportCost() Tag {
	return Tag{
		Genre:       tagGenreNone,
		Label:       tagLabelPayTransportCost,
		IsImportant: false,
	}
}
func TagDressCasuallyToWork() Tag {
	return Tag{
		Genre:       tagGenreNone,
		Label:       tagLabelDressCasuallyToWork,
		IsImportant: false,
	}
}
func TagCommuteByCar() Tag {
	return Tag{
		Genre:       tagGenreNone,
		Label:       tagLabelCommuteByCar,
		IsImportant: false,
	}
}
func TagWithin5MinutesWalk() Tag {
	return Tag{
		Genre:       tagGenreNone,
		Label:       tagLabelWithin5MinutesWalk,
		IsImportant: false,
	}
}
func TagWithin10MinutesWalk() Tag {
	return Tag{
		Genre:       tagGenreNone,
		Label:       tagLabelWithin10MinutesWalk,
		IsImportant: false,
	}
}
func TagWithoutGettingWetFromStation() Tag {
	return Tag{
		Genre:       tagGenreNone,
		Label:       tagLabelWithoutGettingWetFromStation,
		IsImportant: false,
	}
}
func TagUseEnglishSkills() Tag {
	return Tag{
		Genre:       tagGenreNone,
		Label:       tagLabelUseEnglishSkills,
		IsImportant: false,
	}
}
func TagWorkFlexibly() Tag {
	return Tag{
		Genre:       tagGenreNone,
		Label:       tagLabelWorkFlexibly,
		IsImportant: false,
	}
}
