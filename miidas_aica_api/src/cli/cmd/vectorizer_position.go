package cmd

import (
	"aica/api/cli/domain/aica"
	"aica/api/cli/internal"
	"aica/api/cli/sdk/cli"
	"aica/api/cli/usecase/position"
	positionVector "aica/api/domain/position"
	"aica/api/domain/provider"
	miidasPosition "aica/api/domain/user/apply/position"
	"aica/api/domain/vectorizer"

	"github.com/spf13/cobra"
)

func init() {
	rootCmd.AddCommand(VectorizerPosition())
}

func VectorizerPosition() *cobra.Command {
	const batchSize = 500
	var providerStr string

	cmd := &cobra.Command{
		Use:     "VectorizerPosition",
		Short:   "user_apply.position.detailのポジションタイトルと説明をベクトル作成して、意味検索DBに登録します。",
		Example: "./cli VectorizerPosition",
		Run: func(cmd *cobra.Command, args []string) {
			// Validate the provider value
			if providerStr != string(provider.ProviderBedrock) && providerStr != string(provider.ProviderOpenAI) {
				cmd.PrintErrf("Error: invalid vectorizer provider: %s\n", providerStr)
				_ = cmd.Usage()
				return
			}

			err := position.NewVectorizerUseCase(
				cli.GetBatchLogger(),
				aica.NewMigrationsRepository(internal.SemanticDBWriter()),
				miidasPosition.NewReadPositionRepository(internal.MiidasDBReader()),
				positionVector.NewPositionRepository(internal.SemanticDBWriter()),
				vectorizer.NewVectorizerRepository,
				provider.Provider(providerStr),
				batchSize,
			).Execute()
			if err != nil {
				panic(err)
			}
		},
	}

	cmd.Flags().StringVarP(&providerStr, "provider", "p", "", "ベクトル化プロバイダを指定します。")
	_ = cmd.MarkFlagRequired("provider")

	return cmd
}
