package cobra

import (
	"github.com/google/uuid"
	"github.com/spf13/cobra"
)

// MultiHook はPreE/PostE を複数まとめて実行するためのもの
func MultiHook(runs ...func(*cobra.Command, []string) error) func(*cobra.Command, []string) error {
	return func(cmd *cobra.Command, args []string) error {
		for _, run := range runs {
			if err := run(cmd, args); err != nil {
				return err
			}
		}
		return nil
	}
}

// CreateJobID ジョブIDを作成します。
//
// ジョブIDはジョブ実行毎に付与されるユニークなIDです。
// uuid version4で作成しています。
func CreateJobID() string {
	u := uuid.New()
	return u.String()
}
