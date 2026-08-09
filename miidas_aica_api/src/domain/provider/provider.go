package provider

// Provider はAIプロバイダーを表す型
// HyDE、Vectorizer、HTTPのプロバイダー定数を統一する
type Provider string

const (
	ProviderOpenAI  Provider = "openai"
	ProviderGemini  Provider = "gemini"
	ProviderBedrock Provider = "bedrock"
)

// DefaultProvider はembeddingのデフォルトプロバイダー
const DefaultProvider = ProviderOpenAI
