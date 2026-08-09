//go:build mock

package main

import (
	"aica/api/api/mcptool/domain/mv2"
	"aica/api/api/mcptool/http/business"
	"aica/api/api/mcptool/http/company"
	"aica/api/api/mcptool/http/industry"
	"aica/api/api/mcptool/http/jobtype"
	"aica/api/api/mcptool/http/location"
	"aica/api/api/mcptool/http/master"
	"aica/api/api/mcptool/http/position"
)

func setupRoutesOptionsForBuild() setupRoutesOptions {
	return setupRoutesOptions{
		sharedFactory:         newMockSharedDependenciesFactory,
		mvGatewayFactory:      mv2.NewMockMarketValueGateway,
		positionModuleFactory: position.NewMockModule,
		businessModuleFactory: business.NewMockModule,
		companyModuleFactory:  company.NewMockModule,
		industryModuleFactory: industry.NewMockModule,
		jobtypeModuleFactory:  jobtype.NewMockModule,
		locationModuleFactory: location.NewMockModule,
		masterModuleFactory:   master.NewMockModule,
	}
}
