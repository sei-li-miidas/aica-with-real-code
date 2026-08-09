package semantic

import (
	mservice "aica/api/api/mcptool/service"
	"aica/api/domain/hyde"
	hydehistory "aica/api/domain/hyde_history"
	"aica/api/domain/provider"
)

type HydeTextResolver struct {
	hydeService *mservice.HydeService
	provider    provider.Provider
	newHyDERepo func(provider.Provider) (hyde.HyDERepository, error)
}

func NewHydeTextResolverWithProviderAndFactory(
	hydeService *mservice.HydeService,
	hydeProvider provider.Provider,
	newHyDERepo func(provider.Provider) (hyde.HyDERepository, error),
) HyDETextResolver {
	if newHyDERepo == nil {
		panic("hyde repository factory is required")
	}
	return &HydeTextResolver{
		hydeService: hydeService,
		provider:    hydeProvider,
		newHyDERepo: newHyDERepo,
	}
}

func (r *HydeTextResolver) ResolveJobTypeText(keyword string, useHistory bool) (string, error) {
	return r.hydeService.GetOrGenerateHydeText(
		hydehistory.HydeTypeJobType,
		keyword,
		useHistory,
		func(k string) (string, error) {
			hydeProvider, err := r.newHyDERepo(r.provider)
			if err != nil {
				return "", err
			}
			return hydeProvider.GenerateJobTypeHyDEText(k)
		},
	)
}

func (r *HydeTextResolver) ResolveIndustryText(keyword string, useHistory bool) (string, error) {
	return r.hydeService.GetOrGenerateHydeText(
		hydehistory.HydeTypeIndustry,
		keyword,
		useHistory,
		func(k string) (string, error) {
			hydeProvider, err := r.newHyDERepo(r.provider)
			if err != nil {
				return "", err
			}
			return hydeProvider.GenerateIndustryHyDEText(k)
		},
	)
}
