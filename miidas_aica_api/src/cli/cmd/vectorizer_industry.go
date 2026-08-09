package cmd

import (
	"aica/api/cli/internal"
	"aica/api/cli/sdk/cli"
	"aica/api/cli/usecase/industry"
	"aica/api/domain/provider"

	"github.com/spf13/cobra"
)

func init() {
	rootCmd.AddCommand(VectorizerIndustry())
}

func VectorizerIndustry() *cobra.Command {
	var providerStr string

	cmd := &cobra.Command{
		Use:     "VectorizerIndustry",
		Short:   "業界説明をベクトル作成して、意味検索DBに登録します。",
		Example: "./cli VectorizerIndustry --provider=bedrock",
		Run: func(cmd *cobra.Command, args []string) {
			// Validate the provider value
			if providerStr != string(provider.ProviderBedrock) && providerStr != string(provider.ProviderOpenAI) {
				cmd.PrintErrf("Error: invalid vectorizer provider: %s\n", providerStr)
				_ = cmd.Usage()
				return
			}

			err := industry.NewVectorizerUseCase(cli.GetBatchLogger(), internal.SemanticDBWriter(), provider.Provider(providerStr)).Execute()
			if err != nil {
				panic(err)
			}
		},
	}

	cmd.Flags().StringVarP(&providerStr, "provider", "p", "", "ベクトル化プロバイダを指定します。")
	_ = cmd.MarkFlagRequired("provider")

	return cmd
}
