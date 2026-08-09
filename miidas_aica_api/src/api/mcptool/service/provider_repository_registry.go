package service

import (
	"aica/api/domain/hyde"
	"aica/api/domain/provider"
	"aica/api/domain/vectorizer"
	"aica/api/sdk/logger"
	"sync"
)

// ProviderRepositoryRegistry keeps app-lifetime repositories keyed by provider.
type ProviderRepositoryRegistry struct {
	logger logger.LevelLogger

	vectorizerRepositories map[provider.Provider]vectorizer.VectorizerRepository
	vectorizerMu           sync.RWMutex

	hydeRepositories map[provider.Provider]hyde.HyDERepository
	hydeMu           sync.RWMutex
}

func NewProviderRepositoryRegistry(l logger.LevelLogger) *ProviderRepositoryRegistry {
	return &ProviderRepositoryRegistry{
		logger:                 l,
		vectorizerRepositories: map[provider.Provider]vectorizer.VectorizerRepository{},
		hydeRepositories:       map[provider.Provider]hyde.HyDERepository{},
	}
}

func (r *ProviderRepositoryRegistry) GetVectorizerRepository(p provider.Provider) (vectorizer.VectorizerRepository, error) {
	p = r.normalizeVectorizerProvider(p)

	r.vectorizerMu.RLock()
	repo, ok := r.vectorizerRepositories[p]
	r.vectorizerMu.RUnlock()
	if ok {
		return repo, nil
	}

	r.vectorizerMu.Lock()
	defer r.vectorizerMu.Unlock()

	if repo, ok = r.vectorizerRepositories[p]; ok {
		return repo, nil
	}

	created, err := vectorizer.NewVectorizerRepository(p, r.logger)
	if err != nil {
		return nil, err
	}
	r.vectorizerRepositories[p] = created
	return created, nil
}

func (r *ProviderRepositoryRegistry) GetHyDERepository(p provider.Provider) (hyde.HyDERepository, error) {
	p = r.normalizeHyDEProvider(p)

	r.hydeMu.RLock()
	repo, ok := r.hydeRepositories[p]
	r.hydeMu.RUnlock()
	if ok {
		return repo, nil
	}

	r.hydeMu.Lock()
	defer r.hydeMu.Unlock()

	if repo, ok = r.hydeRepositories[p]; ok {
		return repo, nil
	}

	created, err := hyde.NewHyDERepository(p, r.logger)
	if err != nil {
		return nil, err
	}
	r.hydeRepositories[p] = created
	return created, nil
}

func (r *ProviderRepositoryRegistry) normalizeVectorizerProvider(p provider.Provider) provider.Provider {
	switch p {
	case provider.ProviderOpenAI, provider.ProviderBedrock:
		return p
	default:
		r.logger.Warn("Fallback vectorizer provider to openai", "requestedProvider", p)
		return provider.ProviderOpenAI
	}
}

func (r *ProviderRepositoryRegistry) normalizeHyDEProvider(p provider.Provider) provider.Provider {
	switch p {
	case provider.ProviderOpenAI:
		return p
	default:
		r.logger.Warn("Fallback HyDE provider to openai", "requestedProvider", p)
		return provider.ProviderOpenAI
	}
}
