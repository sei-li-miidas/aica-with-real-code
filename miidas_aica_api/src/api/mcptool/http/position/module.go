package position

import (
	"fmt"

	"gorm.io/gorm"

	"aica/api/api/mcptool/domain/mv2"
	"aica/api/api/mcptool/service"
	positionUC "aica/api/api/mcptool/usecase/position"
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	positionFilter "aica/api/api/mcptool/usecase/position/filter"
	pinterfaces "aica/api/api/mcptool/usecase/position/interfaces"
	jobSpecificParams "aica/api/api/mcptool/usecase/position/params"
	positionValidation "aica/api/api/mcptool/usecase/position/validation"
	jobfilter "aica/api/domain/jobfilter"
	"aica/api/domain/jobtype"
	dposition "aica/api/domain/position"
	"aica/api/domain/provider"
	mCompany "aica/api/domain/user/apply/company"
	mPosition "aica/api/domain/user/apply/position"
	"aica/api/sdk/logger"
)

type DBProvider func() *gorm.DB

type Dependencies struct {
	Logger                     logger.LevelLogger
	CacheService               *service.MiidasCacheService
	ProviderRepositoryRegistry *service.ProviderRepositoryRegistry
	LocationLookup             pinterfaces.LocationLookup
	MVGateway                  mv2.MarketValueGateway
	AgentDBProvider            DBProvider
	MiidasDBProvider           DBProvider
	VectorizerProvider         provider.Provider
}

type Module struct {
	handler routeHandler
}

func NewModule(deps Dependencies) (*Module, error) {
	if deps.Logger == nil {
		return nil, fmt.Errorf("logger is required")
	}
	if deps.CacheService == nil {
		return nil, fmt.Errorf("cache service is required")
	}
	if deps.ProviderRepositoryRegistry == nil {
		return nil, fmt.Errorf("provider repository registry is required")
	}
	if deps.LocationLookup == nil {
		return nil, fmt.Errorf("location lookup is required")
	}
	if deps.MVGateway == nil {
		return nil, fmt.Errorf("mv gateway is required")
	}
	if deps.AgentDBProvider == nil {
		return nil, fmt.Errorf("agent db provider is required")
	}
	if deps.MiidasDBProvider == nil {
		return nil, fmt.Errorf("miidas db provider is required")
	}

	if deps.VectorizerProvider == "" {
		deps.VectorizerProvider = provider.DefaultProvider
	}
	if err := jobSpecificParams.Setup(deps.CacheService); err != nil {
		return nil, fmt.Errorf("failed to setup job specific params: %w", err)
	}

	agentDB := deps.AgentDBProvider()
	miidasDB := deps.MiidasDBProvider()
	if agentDB == nil {
		return nil, fmt.Errorf("agent db is nil")
	}
	if miidasDB == nil {
		return nil, fmt.Errorf("miidas db is nil")
	}

	resolver := positionUC.NewJobSpecificSearchResolver(deps.CacheService, deps.LocationLookup)
	positionValidator := positionValidation.NewPositionValidator(deps.CacheService)
	positionVectorRepo := dposition.NewPositionRepository(agentDB)
	vectorizerRepository, err := deps.ProviderRepositoryRegistry.GetVectorizerRepository(deps.VectorizerProvider)
	if err != nil {
		return nil, err
	}
	readPositionRepo := mPosition.NewReadPositionRepository(miidasDB)
	readCompanyRepo := mCompany.NewReadCompanyRepository(miidasDB)
	jobSearchFilterRepo := jobfilter.NewJobSearchFilterRepository(agentDB)
	jobSearchFilterService := positionFilter.NewJobSearchFilterService(deps.Logger, jobSearchFilterRepo).
		WithGenericLocationPersistence(deps.LocationLookup, deps.CacheService)
	jobTypeSearchToolResolver := newCachedJobTypeSearchToolResolver(jobtype.NewJobTypeRepository(agentDB))
	handlerDeps := HandlerDependencies{
		NewGenericSearchUseCase: func(l logger.LevelLogger) GenericSearchUseCase {
			return positionUC.NewGenericSearchUseCase(
				l,
				deps.MVGateway,
				vectorizerRepository,
				positionVectorRepo,
				readPositionRepo,
				positionValidator,
				deps.LocationLookup,
			)
		},
		NewJobTypeSmallIDResolver: func(_ logger.LevelLogger) pcontracts.JobSpecificSearchResolver {
			return resolver
		},
		NewDetailUseCase: func(l logger.LevelLogger) DetailUseCase {
			return positionUC.NewDetailUseCase(readPositionRepo, readCompanyRepo, deps.CacheService.MasterProvider(), l)
		},
		NewSummariesUseCase: func(l logger.LevelLogger) SummariesUseCase {
			return positionUC.NewSummariesUseCase(l, readPositionRepo)
		},
		NewSearchWithJobTypeUseCase: func(l logger.LevelLogger, enablePersistence bool) (SearchWithJobTypeUseCase, error) {
			vectorizerRepository, err := deps.ProviderRepositoryRegistry.GetVectorizerRepository(deps.VectorizerProvider)
			if err != nil {
				return nil, err
			}

			var filterPersister *positionFilter.JobSearchFilterService
			if enablePersistence {
				filterPersister = jobSearchFilterService
			}

			return positionUC.NewSearchWithJobTypeUseCase(
				l,
				deps.MVGateway,
				vectorizerRepository,
				positionVectorRepo,
				readPositionRepo,
				resolver,
				jobSearchFilterService,
				filterPersister,
			), nil
		},
		NewGenericSearchFilterPersister: func(_ logger.LevelLogger) pinterfaces.JobSearchFilterGenericPersister {
			return jobSearchFilterService
		},
		NewJobSearchFilterReader: func(_ logger.LevelLogger) pinterfaces.JobSearchFilterReader {
			return jobSearchFilterService
		},
		NewJobTypesSelectedUseCase: func(l logger.LevelLogger) JobTypesSelectedUseCase {
			return positionUC.NewJobTypesSelectedUseCase(l, jobSearchFilterService, resolver, jobTypeSearchToolResolver)
		},
		NewJobTypeSearchFilterUseCase: func(l logger.LevelLogger) JobTypeSearchFilterUseCase {
			return positionUC.NewJobTypeSearchFilterUseCase(l, jobSearchFilterService, resolver)
		},
		JobTypeSearchToolResolver: jobTypeSearchToolResolver,
	}

	handler := NewHandler(handlerDeps)

	return &Module{handler: handler}, nil
}

func (m *Module) Handler() routeHandler {
	if m == nil {
		return nil
	}
	return m.handler
}
