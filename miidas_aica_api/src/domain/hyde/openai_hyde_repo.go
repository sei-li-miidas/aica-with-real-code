package hyde

import (
	"aica/api/sdk/logger"
	"context"
	"os"

	openai "github.com/sashabaranov/go-openai"
)

const (
	// GPT4.1
	defaultOpenAIModel = openai.GPT4Dot1
)

var (
	openAIApiKey         = os.Getenv("OPENAI_API_KEY")
	openAIHyDERepository *OpenAIHyDERepository
)

type OpenAIHyDERepository struct {
	logger logger.LevelLogger
	client *openai.Client
}

func NewOpenAIHyDERepository(logger logger.LevelLogger) OpenAIHyDERepository {
	if openAIHyDERepository != nil {
		return *openAIHyDERepository
	}
	client := openai.NewClient(openAIApiKey)
	rep := OpenAIHyDERepository{
		logger: logger,
		client: client,
	}
	openAIHyDERepository = &rep
	return rep
}

func (o OpenAIHyDERepository) generateHyDEText(text, prompt string) (string, error) {
	resp, err := o.client.CreateChatCompletion(
		context.Background(),
		openai.ChatCompletionRequest{
			Model: defaultOpenAIModel,
			Messages: []openai.ChatCompletionMessage{
				{
					Role:    openai.ChatMessageRoleDeveloper,
					Content: prompt,
				},
				{
					Role:    openai.ChatMessageRoleUser,
					Content: text,
				},
			},
		},
	)

	if err != nil {
		o.logger.Error("Generating OpenAI HyDE failed", "error", err)
		return "", err
	}

	hydeText := resp.Choices[0].Message.Content
	// o.logger.Info("OpenAI", "HyDE", hydeText)

	return hydeText, nil
}

// 職種のHyDE生成
func (o OpenAIHyDERepository) GenerateJobTypeHyDEText(text string) (string, error) {
	return o.generateHyDEText(text, defaultOpenAIJobTypeHyDEPrompt)
}

// 業種のHyDE生成
func (o OpenAIHyDERepository) GenerateIndustryHyDEText(text string) (string, error) {
	return o.generateHyDEText(text, defaultOpenAIIndustryHyDEPrompt)
}
