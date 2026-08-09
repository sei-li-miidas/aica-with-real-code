package service

import (
	"testing"

	"aica/api/domain/provider"
	"aica/api/domain/public/master"
)

func newTestCacheService() *MiidasCacheService {
	l := &stubServiceLogger{}
	return NewMiidasCacheService(
		l,
		master.NewCacheProviderWithCache(&master.Cache{}),
		NewProviderRepositoryRegistry(l),
	)
}

func TestMiidasCacheService_getVectorizerRepository_CachesPerProvider(t *testing.T) {
	svc := newTestCacheService()
	r1, err := svc.getVectorizerRepository(provider.ProviderOpenAI)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	r2, err := svc.getVectorizerRepository(provider.ProviderOpenAI)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	r3, err := svc.getVectorizerRepository(provider.ProviderBedrock)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if r1 != r2 {
		t.Fatalf("expected same cached repository for same provider")
	}
	if r1 == r3 {
		t.Fatalf("expected different repositories for different providers")
	}
}

func TestMiidasCacheService_getVectorizerRepository_UnknownProviderFallsBackToOpenAI(t *testing.T) {
	svc := newTestCacheService()
	openAIRepo, err := svc.getVectorizerRepository(provider.ProviderOpenAI)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	unknownRepo, err := svc.getVectorizerRepository(provider.Provider("unknown"))
	if err != nil {
		t.Fatalf("unexpected fallback error: %v", err)
	}
	if openAIRepo != unknownRepo {
		t.Fatalf("expected unknown provider to fallback to openai repository")
	}
}

func TestMiidasCacheService_getHydeRepository_CachesPerProvider(t *testing.T) {
	svc := newTestCacheService()
	r1, err := svc.getHydeRepository(provider.ProviderOpenAI)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	r2, err := svc.getHydeRepository(provider.ProviderOpenAI)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	_, err = svc.getHydeRepository(provider.ProviderBedrock)
	if err != nil {
		t.Fatalf("unexpected fallback error: %v", err)
	}

	if r1 != r2 {
		t.Fatalf("expected same cached repository for same provider")
	}
}
