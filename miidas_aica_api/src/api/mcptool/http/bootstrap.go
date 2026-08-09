package main

import (
	"aica/api/api/mcptool/domain/mv2"
	"aica/api/api/mcptool/http/business"
	"aica/api/api/mcptool/http/company"
	"aica/api/api/mcptool/http/industry"
	"aica/api/api/mcptool/http/jobtype"
	"aica/api/api/mcptool/http/location"
	masterRoute "aica/api/api/mcptool/http/master"
	"aica/api/api/mcptool/http/position"
	"aica/api/api/mcptool/service"
	businessUC "aica/api/api/mcptool/usecase/business"
	companyUC "aica/api/api/mcptool/usecase/company"
	industryUC "aica/api/api/mcptool/usecase/industry"
	jobtypeUC "aica/api/api/mcptool/usecase/jobtype"
	locationUC "aica/api/api/mcptool/usecase/location"
	masterUC "aica/api/api/mcptool/usecase/master"
	semantic "aica/api/api/mcptool/usecase/shared/semantic"
	"aica/api/domain/commutingarea"
	"aica/api/domain/hyde"
	hydehistory "aica/api/domain/hyde_history"
	dindustry "aica/api/domain/industry"
	djobtype "aica/api/domain/jobtype"
	"aica/api/domain/provider"
	"aica/api/domain/public/master"
	applybusiness "aica/api/domain/user/apply/business"
	applycompany "aica/api/domain/user/apply/company"
	applyposition "aica/api/domain/user/apply/position"
	"aica/api/domain/vectorizer"
	mecho "aica/api/sdk/echo"
	"aica/api/sdk/echo/middleware"
	merr "aica/api/sdk/error"
	mhttp "aica/api/sdk/http"
	mlogger "aica/api/sdk/logger"
	"flag"
	"fmt"
	"os"

	"github.com/labstack/echo/v4"
)

type appConfig struct {
	showRoute bool
	category  string
	port      int
	debugMode bool
}

type sharedDependenciesFactory func(logger mlogger.LevelLogger) appSharedDependencies
type mvGatewayFactory func(logger mlogger.LevelLogger) mv2.MarketValueGateway

type businessModuleFactory func(business.Dependencies) (*business.Module, error)
type companyModuleFactory func(company.Dependencies) (*company.Module, error)
type locationModuleFactory func(location.Dependencies) (*location.Module, error)

type industryModuleFactory func(industry.Dependencies) (*industry.Module, error)
type jobtypeModuleFactory func(jobtype.Dependencies) (*jobtype.Module, error)
type masterModuleFactory func(masterRoute.Dependencies) (*masterRoute.Module, error)
type positionModuleFactory func(position.Dependencies) (*position.Module, error)

type setupRoutesOptions struct {
	sharedFactory         sharedDependenciesFactory
	mvGatewayFactory      mvGatewayFactory
	businessModuleFactory businessModuleFactory
	companyModuleFactory  companyModuleFactory
	locationModuleFactory locationModuleFactory
	industryModuleFactory industryModuleFactory
	jobtypeModuleFactory  jobtypeModuleFactory
	masterModuleFactory   masterModuleFactory
	positionModuleFactory positionModuleFactory
}

func parseFlags() appConfig {
	cfg := appConfig{}
	flag.BoolVar(&cfg.showRoute, "show-routes", false, "ルートの表示")
	flag.StringVar(&cfg.category, "category", logCategory, "apiの種類。logのcategoryに出力される。他apiと重複しないようにすること。デフォルトは"+(logCategory))
	flag.BoolVar(&cfg.debugMode, "debug", false, "デバッグモード。デバッグログが出力され、全てのログに出力箇所が追加されます。")
	flag.Parse()
	return cfg
}

func resolvePort(logger mlogger.LevelLogger) (int, error) {
	if p, err := mhttp.GetApiPort(serviceName); err != nil {
		logger.Warn("can't get port. use default port.", "detail", err)
		if defaultPort, exists := mhttp.DefaultApiPort(serviceName); exists {
			return defaultPort, nil
		}
		return 0, fmt.Errorf("can't get port: %s", serviceName)
	} else {
		logger.Info("set the port number from an environment variable.")
		return p, nil
	}
}

func setupServer(logger mlogger.LevelLogger, logCtx mlogger.ApiContext, port int) *echo.Echo {
	logger.Info("setup basic server settings")
	server := mecho.NewDefaultServer(port)
	mecho.SetupDefaultPreMiddleware(server)
	server.Use(middleware.RequestLogger(logCtx).Build())
	server.Use(middleware.UseCaseHandler(merr.HTTPStatusMapper(merr.ErrMap)).Build())
	return server
}

func setupRoutes(root mecho.RouteRegister, logger mlogger.LevelLogger, opts setupRoutesOptions) {
	setupRoutesWithOptions(root, logger, opts)
}

func setupRoutesWithOptions(root mecho.RouteRegister, logger mlogger.LevelLogger, opts setupRoutesOptions) {
	sharedFactory := opts.sharedFactory
	if sharedFactory == nil {
		sharedFactory = defaultSharedDependenciesFactory
	}
	mvGatewayFactory := opts.mvGatewayFactory
	if mvGatewayFactory == nil {
		mvGatewayFactory = defaultMVGatewayFactory
	}

	businessModuleFactory := opts.businessModuleFactory
	if businessModuleFactory == nil {
		businessModuleFactory = defaultBusinessModuleFactory
	}
	companyModuleFactory := opts.companyModuleFactory
	if companyModuleFactory == nil {
		companyModuleFactory = defaultCompanyModuleFactory
	}
	industryModuleFactory := opts.industryModuleFactory
	if industryModuleFactory == nil {
		industryModuleFactory = defaultIndustryModuleFactory
	}
	jobtypeModuleFactory := opts.jobtypeModuleFactory
	if jobtypeModuleFactory == nil {
		jobtypeModuleFactory = defaultJobtypeModuleFactory
	}
	locationModuleFactory := opts.locationModuleFactory
	if locationModuleFactory == nil {
		locationModuleFactory = defaultLocationModuleFactory
	}
	masterModuleFactory := opts.masterModuleFactory
	if masterModuleFactory == nil {
		masterModuleFactory = defaultMasterModuleFactory
	}
	positionModuleFactory := opts.positionModuleFactory
	if positionModuleFactory == nil {
		positionModuleFactory = defaultPositionModuleFactory
	}

	shared := sharedFactory(logger)

	masterProvider := master.Provider()

	miidasDBProvider := shared.MiidasDBProvider
	agentDBProvider := shared.AgentDBProvider
	providerRepositoryRegistry := shared.ProviderRepositoryRegistry
	if agentDBProvider == nil {
		logger.Error("shared dependencies missing agent db provider")
		os.Exit(mhttp.ExitStatusInit)
	}
	if miidasDBProvider == nil {
		logger.Error("shared dependencies missing miidas db provider")
		os.Exit(mhttp.ExitStatusInit)
	}
	if providerRepositoryRegistry == nil {
		logger.Error("shared dependencies missing provider repository registry")
		os.Exit(mhttp.ExitStatusInit)
	}

	miidasReadDB := miidasDBProvider()
	readPositionRepo := applyposition.NewReadPositionRepository(miidasReadDB)
	readBusinessRepo := applybusiness.NewReadBusinessRepository(miidasReadDB)
	readCompanyRepo := applycompany.NewReadCompanyRepository(miidasReadDB)

	agentWriteDB := agentDBProvider()
	commutingAreaRepo := commutingarea.NewCommutingAreaRepository(agentWriteDB)
	hydeHistoryRepo := hydehistory.NewHydeHistoryRepository(agentWriteDB)
	jobtypeRepo := djobtype.NewJobTypeRepository(agentWriteDB)
	industryRepo := dindustry.NewIndustrySmallRepository(agentWriteDB)

	businessModule, err := businessModuleFactory(business.Dependencies{
		NewGetDetailUseCase: func(l mlogger.LevelLogger) business.GetDetailUseCase {
			return businessUC.NewGetDetailUseCaseWithRepositories(l, readPositionRepo, readBusinessRepo, readCompanyRepo, masterProvider)
		},
	})
	if err != nil {
		logger.Error("setup business module failed", "detail", err)
		os.Exit(mhttp.ExitStatusInit)
	}
	if err := business.Setup(root, businessModule); err != nil {
		logger.Error("setup business routes failed", "detail", err)
		os.Exit(mhttp.ExitStatusInit)
	}

	companyModule, err := companyModuleFactory(company.Dependencies{
		NewGetDetailUseCase: func(l mlogger.LevelLogger) company.GetDetailUseCase {
			return companyUC.NewGetDetailUseCaseWithRepositories(l, readPositionRepo, readCompanyRepo, readBusinessRepo, masterProvider)
		},
	})
	if err != nil {
		logger.Error("setup company module failed", "detail", err)
		os.Exit(mhttp.ExitStatusInit)
	}
	if err := company.Setup(root, companyModule); err != nil {
		logger.Error("setup company routes failed", "detail", err)
		os.Exit(mhttp.ExitStatusInit)
	}

	industryModule, err := industryModuleFactory(industry.Dependencies{
		NewSemanticUseCase: func(l mlogger.LevelLogger) industry.SemanticIndustryUseCase {
			return industryUC.NewSearchUseCaseWithRepositoriesAndDependencies(
				l,
				hydeHistoryRepo,
				industryRepo,
				industryUC.SearchUseCaseDependencies{
					NewVectorizerRepository: func(p provider.Provider) (vectorizer.VectorizerRepository, error) {
						return providerRepositoryRegistry.GetVectorizerRepository(p)
					},
					NewHydeService: service.NewHydeService,
					NewHydeResolver: func(
						hydeService *service.HydeService,
						p provider.Provider,
					) (semantic.HyDETextResolver, error) {
						return semantic.NewHydeTextResolverWithProviderAndFactory(
							hydeService,
							p,
							func(pp provider.Provider) (hyde.HyDERepository, error) {
								return providerRepositoryRegistry.GetHyDERepository(pp)
							},
						), nil
					},
					NewSearcher: semantic.NewIndustrySemanticSearchService,
				},
			)
		},
	})
	if err != nil {
		logger.Error("setup industry module failed", "detail", err)
		os.Exit(mhttp.ExitStatusInit)
	}
	if err := industry.Setup(root, industryModule); err != nil {
		logger.Error("setup industry routes failed", "detail", err)
		os.Exit(mhttp.ExitStatusInit)
	}

	jobtypeModule, err := jobtypeModuleFactory(jobtype.Dependencies{
		NewSemanticUseCase: func(l mlogger.LevelLogger) jobtype.SemanticJobTypeUseCase {
			return jobtypeUC.NewSearchUseCaseWithRepositoriesAndDependencies(
				l,
				hydeHistoryRepo,
				jobtypeRepo,
				jobtypeUC.SearchUseCaseDependencies{
					NewVectorizerRepository: func(p provider.Provider) (vectorizer.VectorizerRepository, error) {
						return providerRepositoryRegistry.GetVectorizerRepository(p)
					},
					NewHydeService: service.NewHydeService,
					NewHydeResolver: func(
						hydeService *service.HydeService,
						p provider.Provider,
					) (semantic.HyDETextResolver, error) {
						return semantic.NewHydeTextResolverWithProviderAndFactory(
							hydeService,
							p,
							func(pp provider.Provider) (hyde.HyDERepository, error) {
								return providerRepositoryRegistry.GetHyDERepository(pp)
							},
						), nil
					},
					NewSearcher: semantic.NewJobTypeSemanticSearchService,
				},
			)
		},
		NewNatureUseCase: func(l mlogger.LevelLogger) jobtype.NatureJobTypeUseCase {
			return jobtypeUC.NewSearchJobTypesByNatureUseCaseWithRepository(l, jobtypeRepo)
		},
		NewNameUseCase: func(l mlogger.LevelLogger) jobtype.NameJobTypeUseCase {
			return jobtypeUC.NewSearchJobTypesByNameUseCaseWithRepository(l, jobtypeRepo)
		},
	})
	if err != nil {
		logger.Error("setup jobtype module failed", "detail", err)
		os.Exit(mhttp.ExitStatusInit)
	}
	if err := jobtype.Setup(root, jobtypeModule); err != nil {
		logger.Error("setup jobtype routes failed", "detail", err)
		os.Exit(mhttp.ExitStatusInit)
	}

	locationModule, err := locationModuleFactory(location.Dependencies{
		NewVerifyPrefectureCityUseCase: func(l mlogger.LevelLogger) location.VerifyPrefectureCityUseCase {
			return locationUC.NewVerifyPrefectureCityUseCase(masterProvider, l)
		},
		NewSearchCommutingAreasUseCase: func(l mlogger.LevelLogger) location.SearchCommutingAreasUseCase {
			return locationUC.NewSearchCommutingAreasUseCase(commutingAreaRepo, masterProvider, l)
		},
		NewSearchByKeywordUseCase: func(l mlogger.LevelLogger) location.SearchByKeywordUseCase {
			return locationUC.NewSearchByKeywordUseCase(masterProvider, l)
		},
	})
	if err != nil {
		logger.Error("setup location module failed", "detail", err)
		os.Exit(mhttp.ExitStatusInit)
	}
	if err := location.Setup(root, locationModule); err != nil {
		logger.Error("setup location routes failed", "detail", err)
		os.Exit(mhttp.ExitStatusInit)
	}

	masterModule, err := masterModuleFactory(masterRoute.Dependencies{
		NewGetMastersUseCase: func(l mlogger.LevelLogger) masterRoute.GetMastersUseCase {
			return masterUC.NewGetMasters(l, masterProvider)
		},
	})
	if err != nil {
		logger.Error("setup master module failed", "detail", err)
		os.Exit(mhttp.ExitStatusInit)
	}
	if err := masterRoute.Setup(root, masterModule); err != nil {
		logger.Error("setup master routes failed", "detail", err)
		os.Exit(mhttp.ExitStatusInit)
	}

	positionDeps := position.Dependencies{
		Logger:                     logger,
		CacheService:               shared.CacheService,
		ProviderRepositoryRegistry: providerRepositoryRegistry,
		LocationLookup:             shared.LocationLookupService,
		MVGateway:                  mvGatewayFactory(logger),
		AgentDBProvider:            agentDBProvider,
		MiidasDBProvider:           miidasDBProvider,
		VectorizerProvider:         provider.ProviderOpenAI,
	}

	positionModule, err := positionModuleFactory(positionDeps)
	if err != nil {
		logger.Error("setup position module failed", "detail", err)
		os.Exit(mhttp.ExitStatusInit)
	}

	if err := position.Setup(root, positionModule); err != nil {
		logger.Error("setup position routes failed", "detail", err)
		os.Exit(mhttp.ExitStatusInit)
	}
}

func defaultSharedDependenciesFactory(logger mlogger.LevelLogger) appSharedDependencies {
	return newSharedDependenciesFactory(logger)
}
func defaultMVGatewayFactory(logger mlogger.LevelLogger) mv2.MarketValueGateway {
	return mv2.NewMarketValueGateway(logger)
}

var defaultBusinessModuleFactory businessModuleFactory = business.NewModule
var defaultCompanyModuleFactory companyModuleFactory = company.NewModule
var defaultIndustryModuleFactory industryModuleFactory = industry.NewModule
var defaultJobtypeModuleFactory jobtypeModuleFactory = jobtype.NewModule
var defaultLocationModuleFactory locationModuleFactory = location.NewModule
var defaultMasterModuleFactory masterModuleFactory = masterRoute.NewModule
var defaultPositionModuleFactory positionModuleFactory = position.NewModule
