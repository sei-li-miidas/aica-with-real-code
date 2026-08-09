package service

import (
	"fmt"

	address "aica/api/api/mcptool/usecase/shared"
	"aica/api/domain/hyde"
	"aica/api/domain/provider"
	"aica/api/domain/public/master"
	"aica/api/domain/vectorizer"
	merr "aica/api/sdk/error"
	"aica/api/sdk/logger"
	"aica/api/sdk/util"
)

type MiidasCacheService struct {
	logger                     logger.LevelLogger
	cache                      *master.CacheProvider
	providerRepositoryRegistry *ProviderRepositoryRegistry
}

func NewMiidasCacheService(logger logger.LevelLogger, cache *master.CacheProvider, providerRepositoryRegistry *ProviderRepositoryRegistry) *MiidasCacheService {
	return &MiidasCacheService{
		logger:                     logger,
		cache:                      cache,
		providerRepositoryRegistry: providerRepositoryRegistry,
	}
}

func (s *MiidasCacheService) MasterProvider() *master.CacheProvider {
	return s.cache
}

func (s *MiidasCacheService) getVectorizerRepository(p provider.Provider) (vectorizer.VectorizerRepository, error) {
	return s.providerRepositoryRegistry.GetVectorizerRepository(p)
}

func (s *MiidasCacheService) getHydeRepository(p provider.Provider) (hyde.HyDERepository, error) {
	return s.providerRepositoryRegistry.GetHyDERepository(p)
}

func (s *MiidasCacheService) GetTraitPositionOptionUserSideNames(traitID master.MasterTraitPositionID) ([]string, error) {
	options := s.cache.GetAllTraitPositionOptions()[traitID]
	names := make([]string, len(options))
	for i, opt := range options {
		names[i] = opt.UserSideName
	}
	return names, nil
}

func (s *MiidasCacheService) GetTraitPositionOptionValueByNameOrUserSideName(traitID master.MasterTraitPositionID, name string) (int, error) {
	options := s.cache.GetAllTraitPositionOptions()[traitID]
	for _, opt := range options {
		if opt.UserSideName == name || opt.Name == name {
			return opt.Value, nil
		}
	}
	return 0, fmt.Errorf("TraitPositionOption not found for traitID=%s, name=%s", traitID, name)
}

func (s *MiidasCacheService) ExistsPrefectureCity(prefectureName string, cityName string) bool {
	prefectureName, cityName = util.MaybeReplaceTokyoWardName(prefectureName, cityName)
	cities := s.cache.PrefectureCities().GetByName(prefectureName, cityName)
	return len(cities) != 0
}

// 市区町村ID一覧から都道府県+市区町村の場所情報を返す
func (s *MiidasCacheService) GetLocationRequestsFromCityIDs(cityIDs []int32) []*address.LocationRequest {
	if len(cityIDs) == 0 {
		return nil
	}

	cityMap := s.cache.CityMap()
	prefectureMap := s.cache.PrefectureMap()
	seen := make(map[master.CityID]struct{}, len(cityIDs))
	result := make([]*address.LocationRequest, 0, len(cityIDs))

	for _, id := range cityIDs {
		cityID := master.CityID(id)
		if _, ok := seen[cityID]; ok {
			continue
		}
		city, found := cityMap.Get(cityID)
		if !found {
			continue
		}
		prefecture, found := prefectureMap.Get(city.PrefectureID)
		if !found {
			continue
		}
		result = append(result, &address.LocationRequest{
			LocationType:   address.LOCATION_TYPE_COMMUTING_AREAS,
			PrefectureName: prefecture.Name,
			CityName:       string(city.Name),
		})
		seen[cityID] = struct{}{}
	}

	return result
}

// 都道府県+市区町村の連結文字列（例: 東京都新宿区）から場所情報を返す
func (s *MiidasCacheService) ResolveLocationRequestByName(name string) (*address.LocationRequest, error) {
	if name == "" {
		return nil, merr.ErrInvalidRequest.WithCause(fmt.Errorf("location name is required"))
	}

	prefectureCities := s.cache.PrefectureCities()
	for _, pc := range prefectureCities {
		if pc == nil {
			continue
		}
		if pc.PrefectureName+string(pc.RealCityName) == name || pc.PrefectureName+string(pc.CityName) == name {
			cityName := string(pc.RealCityName)
			if cityName == "" {
				cityName = string(pc.CityName)
			}
			return &address.LocationRequest{
				PrefectureName: pc.PrefectureName,
				CityName:       cityName,
			}, nil
		}
	}

	return nil, merr.ErrInvalidRequest.WithCause(
		fmt.Errorf("場所が見つかりませんでした（%s）。正しい市区町村名を指定してください。", name),
	)
}

// 職種名からマスターキャッシュで職種小分類IDを取得する
func (s *MiidasCacheService) GetJobTypeSmallIDsByNames(names []string) ([]int32, error) {
	if len(names) == 0 {
		return nil, nil
	}

	var ids []int32
	for _, name := range names {
		if name == "" {
			continue
		}
		var found *master.JobTypeSmall
		for _, jt := range s.cache.JobTypeSmalls() {
			if jt.Name == name {
				found = jt
				break
			}
		}
		if found == nil {
			return nil, merr.ErrInvalidRequest.WithCause(
				fmt.Errorf("「%s」は不正な職種名です。正しい職種名を指定してください。", name),
			)
		}
		ids = append(ids, int32(found.ID))
	}

	return ids, nil
}

// スキル名一覧からマスターキャッシュでスキルを取得する
func (s *MiidasCacheService) GetSkillsByNames(names []string) (master.Skills, error) {
	if len(names) == 0 {
		return nil, nil
	}

	var skills master.Skills
	for _, name := range names {
		if name == "" {
			continue
		}
		var skill *master.Skill
		for _, sk := range s.cache.Skills() {
			if sk.GetPureName() == name || sk.GetName() == name {
				skill = sk
				break
			}
		}
		if skill == nil {
			return nil, merr.ErrInvalidRequest.WithCause(
				fmt.Errorf("「%s」は不正なスキル名です。正しいスキル名を指定してください。", name),
			)
		}
		skills = append(skills, skill)
	}

	return skills, nil
}

// GetAllSkills returns all skill masters from cache.
func (s *MiidasCacheService) GetAllSkills() master.Skills {
	return s.cache.Skills()
}

// GetAllSkillGroups returns all skill group masters from cache.
func (s *MiidasCacheService) GetAllSkillGroups() master.SkillGroups {
	return s.cache.SkillGroups()
}

// Logger returns service logger for callers that need startup-time diagnostics.
func (s *MiidasCacheService) Logger() logger.LevelLogger {
	if s == nil {
		return nil
	}
	return s.logger
}
