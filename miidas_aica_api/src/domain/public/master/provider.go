package master

import (
	"context"
	"slices"
	"strings"
	"sync"

	"aica/api/sdk/gormio"
	mlogger "aica/api/sdk/logger"
	"aica/api/sdk/slice"
)

type (
	CacheProvider struct {
		cp    gormio.ConnProvider
		cache *Cache
	}
)

var (
	p CacheProvider
)

// SetupProvider キャッシュプロバイダーのセットアップ
func SetupProvider(ctx context.Context, cp gormio.ConnProvider, logger mlogger.LevelLogger) {
	p = CacheProvider{
		cp:    cp,
		cache: newCache(ctx, cp, logger),
	}
}

// Provider キャッシュプロバイダーを返す
func Provider() *CacheProvider {
	return &p
}

// NewCacheProviderWithCache returns a cache provider backed by the given cache.
func NewCacheProviderWithCache(cache *Cache) *CacheProvider {
	if cache == nil {
		cache = &Cache{}
	}

	return &CacheProvider{
		cache: cache,
	}
}

// Get マスターデータを取得する
func (p *CacheProvider) Get(ctx context.Context, name string) (any, error) {
	return p.cache.Get(name)
}

func (p *CacheProvider) Cities() Cities {
	return p.cache.Cities
}

var cityMap = sync.OnceValue(func() CityMap {
	return p.Cities().ToMap()
})

func (p *CacheProvider) CityMap() CityMap {
	return cityMap()
}

func (p *CacheProvider) Prefectures() Prefectures {
	return p.cache.Prefectures
}

var prefectureMap = sync.OnceValue(func() PrefectureMap {
	return p.Prefectures().ToMap()
})

func (p *CacheProvider) PrefectureMap() PrefectureMap {
	return prefectureMap()
}

func (p *CacheProvider) PrefectureCities() PrefectureCities {
	return p.cache.PrefectureCities
}

func (p *CacheProvider) IndustrySmalls() IndustrySmalls {
	return p.cache.IndustrySmalls
}

func (p *CacheProvider) IndustrySmallMap() IndustrySmallMap {
	return p.IndustrySmalls().ToMap()
}

var industrySmallMap = sync.OnceValue(func() IndustrySmallMap {
	return p.IndustrySmalls().ToMap()
})

func (p *CacheProvider) JobTypeLarges() JobTypeLarges {
	return p.cache.JobTypeLarges
}

var jobTypeLargeMap = sync.OnceValue(func() JobTypeLargeMap {
	return p.JobTypeLarges().ToMap()
})

func (p *CacheProvider) JobTypeLargeMap() JobTypeLargeMap {
	return jobTypeLargeMap()
}

func (p *CacheProvider) JobTypeSmalls() JobTypeSmalls {
	return p.cache.JobTypeSmalls
}

var jobTypeSmallMap = sync.OnceValue(func() JobTypeSmallMap {
	return p.JobTypeSmalls().ToMap()
})

func (p *CacheProvider) JobTypeSmallMap() JobTypeSmallMap {
	return jobTypeSmallMap()
}

func (p *CacheProvider) SpotExpLevels() SpotExpLevels {
	return p.cache.SpotExpLevels
}
func (p *CacheProvider) SpotJobRequests() SpotJobRequests {
	return p.cache.SpotJobRequests
}

var spotJobRequestMap = sync.OnceValue(func() Map[SpotJobRequestID, SpotJobRequest] {
	return p.SpotJobRequests().ToMap()
})

func (p *CacheProvider) Skills() Skills {
	return p.cache.Skills
}

var skillsMap = sync.OnceValue(func() SkillMap {
	return p.Skills().ToMap()
})

func (p *CacheProvider) SkillMap() SkillMap {
	return skillsMap()
}

func (p *CacheProvider) SkillGroups() SkillGroups {
	return p.cache.SkillGroups
}

var skillGroupMap = sync.OnceValue(func() SkillGroupMap {
	return p.SkillGroups().ToMap()
})

func (p *CacheProvider) SkillGroupMap() SkillGroupMap {
	return skillGroupMap()
}

func (p *CacheProvider) SpotJobRequestMap() Map[SpotJobRequestID, SpotJobRequest] {
	return spotJobRequestMap()
}

func (p *CacheProvider) IndustrySmallMap2() IndustrySmallMap {
	return industrySmallMap()
}

func (p *CacheProvider) GetIndustrySmallNameIncludingAllIndustry(smallID IndustrySmallID) string {
	if smallID == AllIndustry {
		return AllIndustryName
	}

	smallMap := p.IndustrySmallMap2()
	small, ok := smallMap.Get(smallID)
	if !ok {
		return ""
	}
	return small.Name
}

func (p *CacheProvider) Interviewers() Interviewers {
	return p.cache.Interviewers
}

var interviewerMap = sync.OnceValue(func() Map[InterviewerID, Interviewer] {
	return p.Interviewers().ToMap()
})

func (p *CacheProvider) InterviewerMap() Map[InterviewerID, Interviewer] {
	return interviewerMap()
}

func (p *CacheProvider) WorkExperiencePatterns() WorkExperiencePatterns {
	return p.cache.WorkExperiencePatterns
}

var workExperiencePatternMap = sync.OnceValue(func() WorkExperiencePatternMap {
	return p.WorkExperiencePatterns().ToMap()
})

func (p *CacheProvider) WorkExperiencePatternMap() WorkExperiencePatternMap {
	return workExperiencePatternMap()
}

func (p *CacheProvider) WorkExperienceContentTypes() WorkExperienceContentTypes {
	return p.cache.WorkExperienceContentTypes
}

var workExperienceContentTypeMap = sync.OnceValue(func() WorkExperienceContentTypeMap {
	return p.WorkExperienceContentTypes().ToMap()
})

func (p *CacheProvider) WorkExperienceContentTypeMap() WorkExperienceContentTypeMap {
	return workExperienceContentTypeMap()
}

func (p *CacheProvider) WorkExperienceTimings() WorkExperienceTimings {
	return p.cache.WorkExperienceTimings
}

var workExperienceTimingMap = sync.OnceValue(func() WorkExperienceTimingMap {
	return p.WorkExperienceTimings().ToMap()
})

func (p *CacheProvider) WorkExperienceTimingMap() WorkExperienceTimingMap {
	return workExperienceTimingMap()
}

func (p *CacheProvider) WorkExperienceTimeframes() WorkExperienceTimeframes {
	return p.cache.WorkExperienceTimeframes
}

var workExperienceTimeframeMap = sync.OnceValue(func() WorkExperienceTimeframeMap {
	return p.WorkExperienceTimeframes().ToMap()
})

func (p *CacheProvider) WorkExperienceTimeframeMap() WorkExperienceTimeframeMap {
	return workExperienceTimeframeMap()
}

func (p *CacheProvider) WorkExperienceNeedtimes() WorkExperienceNeedtimes {
	return p.cache.WorkExperienceNeedtimes
}

var workExperienceNeedtimesMap = sync.OnceValue(func() WorkExperienceNeedtimeMap {
	return p.WorkExperienceNeedtimes().ToMap()
})

func (p *CacheProvider) WorkExperienceNeedtimeMap() WorkExperienceNeedtimeMap {
	return workExperienceNeedtimesMap()
}

func (p *CacheProvider) WorkExperienceRewards() WorkExperienceRewards {
	return p.cache.WorkExperienceRewards
}

var workExperienceRewardsMap = sync.OnceValue(func() WorkExperienceRewardMap {
	return p.WorkExperienceRewards().ToMap()
})

func (p *CacheProvider) WorkExperienceRewardMap() WorkExperienceRewardMap {
	return workExperienceRewardsMap()
}

func (p *CacheProvider) GetAllTraitPositionOptions() map[MasterTraitPositionID][]*TraitPositionOption {
	return p.cache.TraitPositionOptions
}

func (p *CacheProvider) GetTraitCompanyOptionsAllForUser() map[MasterTraitCompanyID][]*TraitCompanyOptionForUser {
	ret := make(map[MasterTraitCompanyID][]*TraitCompanyOptionForUser, len(p.cache.TraitCompanyOptions))
	for k, opts := range p.cache.TraitCompanyOptions {
		list := slice.Extract(opts, func(_ int, o *TraitCompanyOption) *TraitCompanyOptionForUser {
			return &TraitCompanyOptionForUser{
				TraitCompanyID: o.TraitCompanyID,
				Value:          o.Value,
				UserSideName:   o.UserSideName, // ユーザー側
				SortOrder:      o.SortOrder,
			}
		})
		ret[k] = list
	}
	return ret
}

func (p *CacheProvider) GetTraitBusinessOptionsAllForUser() map[MasterTraitBusinessID][]*TraitBusinessOptionForUser {
	ret := make(map[MasterTraitBusinessID][]*TraitBusinessOptionForUser, len(p.cache.TraitBusinessOptions))
	for k, opts := range p.cache.TraitBusinessOptions {
		list := slice.Extract(opts, func(_ int, o *TraitBusinessOption) *TraitBusinessOptionForUser {
			return &TraitBusinessOptionForUser{
				TraitBusinessID: o.TraitBusinessID,
				Value:           o.Value,
				UserSideName:    o.UserSideName, // ユーザー側
				SortOrder:       o.SortOrder,
			}
		})
		ret[k] = list
	}
	return ret
}

// GetTraitPositionOptionsAllForUser ユーザー用ポジションの全トレイトオプション
func (p *CacheProvider) GetTraitPositionOptionsAllForUser() map[MasterTraitPositionID][]*TraitPositionOptionForUser {
	ret := make(map[MasterTraitPositionID][]*TraitPositionOptionForUser, len(p.cache.TraitPositionOptions))
	for k, opts := range p.cache.TraitPositionOptions {
		list := slice.Extract(opts, func(_ int, o *TraitPositionOption) *TraitPositionOptionForUser {
			return &TraitPositionOptionForUser{
				TraitPositionID: o.TraitPositionID,
				Value:           o.Value,
				UserSideName:    o.UserSideName, // ユーザー向け
				SortOrder:       o.SortOrder,
			}
		})
		ret[k] = list
	}
	return ret
}

func (p *CacheProvider) GetTraitBusinessOptionsForUser(id MasterTraitBusinessID) TraitBusinessOptionListForUser {
	return p.GetTraitBusinessOptionsAllForUser()[id]
}

func (p *CacheProvider) GetTraitCompanyOptionsForUser(id MasterTraitCompanyID) TraitCompanyOptionListForUser {
	return p.GetTraitCompanyOptionsAllForUser()[id]
}

func (p *CacheProvider) GetTraitPositionOptionsForUser(id MasterTraitPositionID) TraitPositionOptionListForUser {
	return p.GetTraitPositionOptionsAllForUser()[id]
}

func (p *CacheProvider) SearchLocation(keyword string) PrefectureCities {
	var result PrefectureCities
	var uniqCityIDs []CityID

	for _, prefectureCity := range p.cache.PrefectureCities {
		if strings.Contains(prefectureCity.Name, keyword) || strings.Contains(prefectureCity.Kana, keyword) {
			if !slices.Contains(uniqCityIDs, prefectureCity.CityID) {
				uniqCityIDs = append(uniqCityIDs, prefectureCity.CityID)
				result = append(result, prefectureCity)
			}
		}
	}

	return result
}
