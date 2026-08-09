package position

import (
	"aica/api/api/mcptool/service"
	tmock "aica/api/api/mcptool/testutil/mock"
	"testing"

	"gorm.io/gorm"
)

func TestNewModule_FailFastEachDependency(t *testing.T) {
	logger := &tmock.MockLogger{}
	registry := service.NewProviderRepositoryRegistry(logger)
	cache := service.NewMiidasCacheService(logger, makeInitializedMasterCacheProvider(), registry)
	locationLookup := makeInitializedLocationLookupService(logger, makeInitializedMasterCacheProvider())
	mv := &stubMVGateway{}
	agentProvider := func() *gorm.DB { return &gorm.DB{} }
	miidasProvider := func() *gorm.DB { return &gorm.DB{} }

	tests := []struct {
		name string
		deps Dependencies
	}{
		{
			name: "missing logger",
			deps: Dependencies{
				CacheService:               cache,
				ProviderRepositoryRegistry: registry,
				LocationLookup:             locationLookup,
				MVGateway:                  mv,
				AgentDBProvider:            agentProvider,
				MiidasDBProvider:           miidasProvider,
			},
		},
		{
			name: "missing cache",
			deps: Dependencies{
				Logger:                     logger,
				ProviderRepositoryRegistry: registry,
				LocationLookup:             locationLookup,
				MVGateway:                  mv,
				AgentDBProvider:            agentProvider,
				MiidasDBProvider:           miidasProvider,
			},
		},
		{
			name: "missing provider repository registry",
			deps: Dependencies{
				Logger:           logger,
				CacheService:     cache,
				LocationLookup:   locationLookup,
				MVGateway:        mv,
				AgentDBProvider:  agentProvider,
				MiidasDBProvider: miidasProvider,
			},
		},
		{
			name: "missing mv gateway",
			deps: Dependencies{
				Logger:                     logger,
				CacheService:               cache,
				ProviderRepositoryRegistry: registry,
				LocationLookup:             locationLookup,
				AgentDBProvider:            agentProvider,
				MiidasDBProvider:           miidasProvider,
			},
		},
		{
			name: "missing agent provider",
			deps: Dependencies{
				Logger:                     logger,
				CacheService:               cache,
				ProviderRepositoryRegistry: registry,
				LocationLookup:             locationLookup,
				MVGateway:                  mv,
				MiidasDBProvider:           miidasProvider,
			},
		},
		{
			name: "missing miidas provider",
			deps: Dependencies{
				Logger:                     logger,
				CacheService:               cache,
				ProviderRepositoryRegistry: registry,
				LocationLookup:             locationLookup,
				MVGateway:                  mv,
				AgentDBProvider:            agentProvider,
			},
		},
		{
			name: "agent db nil",
			deps: Dependencies{
				Logger:                     logger,
				CacheService:               cache,
				ProviderRepositoryRegistry: registry,
				LocationLookup:             locationLookup,
				MVGateway:                  mv,
				AgentDBProvider:            func() *gorm.DB { return nil },
				MiidasDBProvider:           miidasProvider,
			},
		},
		{
			name: "miidas db nil",
			deps: Dependencies{
				Logger:                     logger,
				CacheService:               cache,
				ProviderRepositoryRegistry: registry,
				LocationLookup:             locationLookup,
				MVGateway:                  mv,
				AgentDBProvider:            agentProvider,
				MiidasDBProvider:           func() *gorm.DB { return nil },
			},
		},
	}

	runCase := func(tc struct {
		name string
		deps Dependencies
	}) {
		t.Run(tc.name, func(t *testing.T) {
			module, err := NewModule(tc.deps)
			if err == nil || module != nil {
				t.Fatalf("expected error for %s", tc.name)
			}
		})
	}

	runCase(tests[0])
	runCase(tests[1])
	runCase(tests[2])
	runCase(tests[3])
	runCase(tests[4])
	runCase(tests[5])
	runCase(tests[6])
	runCase(tests[7])
}
