package company

import (
	"time"

	"gorm.io/gorm"

	"aica/api/domain/public/master"
)

type (
	RCompanyRepository struct {
		db *gorm.DB
	}
)

func NewReadCompanyRepository(db *gorm.DB) *RCompanyRepository {
	return &RCompanyRepository{
		db: db,
	}
}

func (r *RCompanyRepository) Get(id ID) (*Company, error) {
	var row company
	if err := r.db.Where("id = ?", id).Take(&row).Error; err != nil {
		return nil, err
	}
	c := newCompanyFromRow(row)
	return &c, nil
}

func (r *RCompanyRepository) GetByIDs(ids []ID) ([]Company, error) {
	rows := make([]company, 0, len(ids))
	if err := r.db.Where("id IN (?)", ids).Find(&rows).Error; err != nil {
		return nil, err
	}

	cs := make([]Company, 0, len(rows))
	for i := range rows {
		cs = append(cs, newCompanyFromRow(rows[i]))
	}
	return cs, nil
}

func newCompanyFromRow(c company) Company {
	return Company{
		ID:                   ID(c.ID),
		Detail:               c.Detail,
		IsSearchable:         c.IsSearchable,
		StopOffer:            c.StopOfferFlag,
		StopOfferDatetime:    c.StopOfferDatetime,
		RegistrationStatusID: RegistrationStatus(c.RegistrationStatusID),
		LastModifiedAt:       c.LastModifiedAt,
		ImportedAt:           c.ImportedAt,
	}
}

func (r *RCompanyRepository) GetByNameIDs(nameIDs []master.CompanyNameID) ([]Company, error) {
	var rows []company
	if err := r.db.Where("name_id IN (?)", nameIDs).Find(&rows).Error; err != nil {
		return nil, err
	}
	var cs []Company
	for i := range rows {
		cs = append(cs, newCompanyFromRow(rows[i]))
	}
	return cs, nil
}

// company companyテーブル
type company struct {
	ID                   int `gorm:"primaryKey;autoIncrement:false"`
	Detail               Detail
	IsSearchable         bool
	LastModifiedAt       time.Time
	ImportedAt           time.Time
	StopOfferFlag        bool
	StopOfferDatetime    *time.Time
	RegistrationStatusID int
}

func (company) TableName() string {
	return "user_apply.company"
}
