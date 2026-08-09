//go:build mock

package service

import (
	"aica/api/domain/public/master"
	"aica/api/sdk/logger"
)

// NewMockMiidasCacheService returns a cache service backed by an in-memory empty master cache.
func NewMockMiidasCacheService(logger logger.LevelLogger) *MiidasCacheService {
	return NewMiidasCacheService(logger, newMockMasterCacheProvider(), NewProviderRepositoryRegistry(logger))
}

func newMockMasterCacheProvider() *master.CacheProvider {
	return master.NewCacheProviderWithCache(&master.Cache{
		TraitPositionOptions: map[master.MasterTraitPositionID][]*master.TraitPositionOption{},
		TraitBusinessOptions: map[master.MasterTraitBusinessID][]*master.TraitBusinessOption{},
		TraitCompanyOptions:  map[master.MasterTraitCompanyID][]*master.TraitCompanyOption{},
	})
}
