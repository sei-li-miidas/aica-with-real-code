package main

import (
	"aica/api/api/mcptool/internal"
	"aica/api/api/mcptool/service"
	"aica/api/domain/commutingarea"
	"aica/api/domain/public/master"
	"aica/api/sdk/logger"

	"gorm.io/gorm"
)

type appSharedDependencies struct {
	AgentDBProvider            func() *gorm.DB
	MiidasDBProvider           func() *gorm.DB
	CacheService               *service.MiidasCacheService
	LocationLookupService      *service.LocationLookupService
	ProviderRepositoryRegistry *service.ProviderRepositoryRegistry
}

func newSharedDependenciesFactory(l logger.LevelLogger) appSharedDependencies {
	commutingAreaRepository := commutingarea.NewCommutingAreaRepository(internal.AgentDBWriter())
	providerRepositoryRegistry := service.NewProviderRepositoryRegistry(l)
	return appSharedDependencies{
		AgentDBProvider:            internal.AgentDBWriter,
		MiidasDBProvider:           internal.MiidasDBReader,
		CacheService:               service.NewMiidasCacheService(l, master.Provider(), providerRepositoryRegistry),
		LocationLookupService:      service.NewLocationLookupService(l, master.Provider(), commutingAreaRepository),
		ProviderRepositoryRegistry: providerRepositoryRegistry,
	}
}
