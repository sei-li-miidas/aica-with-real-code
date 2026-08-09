package service

import (
	"testing"

	"aica/api/domain/provider"
)

type stubServiceLogger struct{}

func (l *stubServiceLogger) Info(string, ...any)  {}
func (l *stubServiceLogger) Warn(string, ...any)  {}
func (l *stubServiceLogger) Error(string, ...any) {}
func (l *stubServiceLogger) Fatal(string, ...any) {}

func TestProviderRepositoryRegistry_VectorizerFallbackToOpenAI(t *testing.T) {
	r := NewProviderRepositoryRegistry(&stubServiceLogger{})

	openAIRepo, err := r.GetVectorizerRepository(provider.ProviderOpenAI)
	if err != nil {
		t.Fatalf("unexpected error for openai: %v", err)
	}
	geminiRepo, err := r.GetVectorizerRepository(provider.ProviderGemini)
	if err != nil {
		t.Fatalf("unexpected error for gemini fallback: %v", err)
	}
	unknownRepo, err := r.GetVectorizerRepository(provider.Provider("unknown"))
	if err != nil {
		t.Fatalf("unexpected error for unknown fallback: %v", err)
	}

	if openAIRepo != geminiRepo || openAIRepo != unknownRepo {
		t.Fatalf("expected fallback providers to reuse openai vectorizer repository")
	}
}

func TestProviderRepositoryRegistry_HyDEFallbackToOpenAI(t *testing.T) {
	r := NewProviderRepositoryRegistry(&stubServiceLogger{})

	openAIRepo, err := r.GetHyDERepository(provider.ProviderOpenAI)
	if err != nil {
		t.Fatalf("unexpected error for openai: %v", err)
	}
	geminiRepo, err := r.GetHyDERepository(provider.ProviderGemini)
	if err != nil {
		t.Fatalf("unexpected error for gemini fallback: %v", err)
	}
	bedrockRepo, err := r.GetHyDERepository(provider.ProviderBedrock)
	if err != nil {
		t.Fatalf("unexpected error for bedrock fallback: %v", err)
	}

	if openAIRepo != geminiRepo || openAIRepo != bedrockRepo {
		t.Fatalf("expected fallback providers to reuse openai HyDE repository")
	}
}
