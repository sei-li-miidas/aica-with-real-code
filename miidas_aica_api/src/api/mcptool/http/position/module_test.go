package position

import (
	"aica/api/api/mcptool/service"
	tmock "aica/api/api/mcptool/testutil/mock"
	"aica/api/domain/public/master"
	"reflect"
	"testing"
	"unsafe"

	"github.com/stretchr/testify/assert"
	"gorm.io/gorm"
)

func TestNewModule_Success(t *testing.T) {
	logger := &tmock.MockLogger{}
	masterCache := makeInitializedMasterCacheProvider()
	providerRepoRegistry := service.NewProviderRepositoryRegistry(logger)
	module, err := NewModule(Dependencies{
		Logger:                     logger,
		CacheService:               service.NewMiidasCacheService(logger, masterCache, providerRepoRegistry),
		ProviderRepositoryRegistry: providerRepoRegistry,
		LocationLookup:             makeInitializedLocationLookupService(logger, masterCache),
		MVGateway:                  &stubMVGateway{},
		AgentDBProvider:            func() *gorm.DB { return &gorm.DB{} },
		MiidasDBProvider:           func() *gorm.DB { return &gorm.DB{} },
	})
	assert.NoError(t, err)
	assert.NotNil(t, module)
	assert.NotNil(t, module.Handler())
}

func TestNewModule_FailFastOnMissingDependencies(t *testing.T) {
	logger := &tmock.MockLogger{}
	_, err := NewModule(Dependencies{
		Logger:    logger,
		MVGateway: &stubMVGateway{},
	})
	assert.Error(t, err)
}

func makeInitializedMasterCacheProvider() *master.CacheProvider {
	cp := &master.CacheProvider{}
	cacheField := reflect.ValueOf(cp).Elem().FieldByName("cache")
	ptr := reflect.NewAt(cacheField.Type(), unsafe.Pointer(cacheField.UnsafeAddr())).Elem()
	ptr.Set(reflect.ValueOf(&master.Cache{
		Skills:               master.Skills{},
		SkillGroups:          master.SkillGroups{},
		TraitPositionOptions: map[master.MasterTraitPositionID][]*master.TraitPositionOption{},
	}))
	return cp
}

type initializedCommutingAreaSearcher struct{}

func (s *initializedCommutingAreaSearcher) SearchCommutingAreas(_ int) ([]*master.PrefectureCity, error) {
	return nil, nil
}

func makeInitializedLocationLookupService(logger *tmock.MockLogger, cache *master.CacheProvider) *service.LocationLookupService {
	return service.NewLocationLookupService(logger, cache, &initializedCommutingAreaSearcher{})
}
