package hydehistory

import (
	"time"
)

type HydeType int

const (
	HydeTypeJobType  HydeType = 1 // 職種
	HydeTypeIndustry HydeType = 2 // 業種
)

type HydeHistory struct {
	HydeType   HydeType  `gorm:"PrimaryKey;column:hyde_type"`
	Keyword    string    `gorm:"PrimaryKey;column:keyword"`
	HydeText   string    `gorm:"column:hyde_text"`
	LastUsedAt time.Time `gorm:"column:last_used_at"`
}

func (HydeHistory) TableName() string {
	return "hyde_histories"
}
