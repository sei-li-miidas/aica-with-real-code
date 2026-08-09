//go:build mock

package main

import (
	"aica/api/api/mcptool/internal"
	"aica/api/api/mcptool/service"
	"aica/api/domain/public/master"
	"aica/api/sdk/logger"

	"gorm.io/gorm"
)

func newMockSharedDependenciesFactory(l logger.LevelLogger) appSharedDependencies {
	cacheProvider := master.NewCacheProviderWithCache(&master.Cache{
		TraitPositionOptions: map[master.MasterTraitPositionID][]*master.TraitPositionOption{},
		TraitBusinessOptions: map[master.MasterTraitBusinessID][]*master.TraitBusinessOption{},
		TraitCompanyOptions:  map[master.MasterTraitCompanyID][]*master.TraitCompanyOption{},
	})
	providerRepositoryRegistry := service.NewProviderRepositoryRegistry(l)
	return appSharedDependencies{
		AgentDBProvider:            func() *gorm.DB { return internal.AgentDBWriter() },
		MiidasDBProvider:           func() *gorm.DB { return internal.MiidasDBReader() },
		CacheService:               service.NewMiidasCacheService(l, cacheProvider, providerRepositoryRegistry),
		LocationLookupService:      service.NewLocationLookupService(l, cacheProvider, newMockCommutingAreaSearcher()),
		ProviderRepositoryRegistry: providerRepositoryRegistry,
	}
}

type mockCommutingAreaSearcher struct{}

func newMockCommutingAreaSearcher() *mockCommutingAreaSearcher {
	return &mockCommutingAreaSearcher{}
}

func (m *mockCommutingAreaSearcher) SearchCommutingAreas(_ int) ([]*master.PrefectureCity, error) {
	return nil, nil
}
