package hydehistory

import (
	"errors"
	"time"

	perr "github.com/pkg/errors"
	"gorm.io/gorm"
)

type HydeHistoryFinderAndSaver interface {
	GetHydeText(hydeType HydeType, keyword string) (*string, error)
	Save(history *HydeHistory) error
}

type (
	HydeHistoryRepository struct {
		db *gorm.DB
	}
)

func NewHydeHistoryRepository(db *gorm.DB) *HydeHistoryRepository {
	return &HydeHistoryRepository{
		db: db,
	}
}

func (r *HydeHistoryRepository) GetByPK(hydeType HydeType, keyword string) (*HydeHistory, error) {
	var history HydeHistory
	if err := r.db.Where("hyde_type = ? AND keyword = ?", hydeType, keyword).First(&history).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		return nil, perr.WithStack(err)
	}

	return &history, nil
}

func (r *HydeHistoryRepository) Save(history *HydeHistory) error {
	if err := r.db.Save(history).Error; err != nil {
		return perr.WithStack(err)
	}
	return nil
}

func (r *HydeHistoryRepository) GetHydeText(hydeType HydeType, keyword string) (*string, error) {
	history, err := r.GetByPK(hydeType, keyword)
	if err != nil {
		return nil, err
	}

	if history == nil {
		return nil, nil
	}

	// 最終使用日時を更新
	history.LastUsedAt = time.Now()
	if err := r.Save(history); err != nil {
		return nil, err
	}

	return &history.HydeText, nil
}
