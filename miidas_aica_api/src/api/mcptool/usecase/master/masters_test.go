package master

import (
	"context"
	"errors"
	"testing"

	"github.com/stretchr/testify/assert"
)

type stubLogger struct{}

func (l *stubLogger) Info(string, ...any)  {}
func (l *stubLogger) Warn(string, ...any)  {}
func (l *stubLogger) Error(string, ...any) {}
func (l *stubLogger) Fatal(string, ...any) {}

type stubMasterProvider struct {
	getFn func(ctx context.Context, name string) (any, error)
}

func (s *stubMasterProvider) Get(ctx context.Context, name string) (any, error) {
	return s.getFn(ctx, name)
}

func TestNewGetMasters(t *testing.T) {
	t.Run("依存を注入してユースケースを生成できる", func(t *testing.T) {
		uc := NewGetMasters(&stubLogger{}, &stubMasterProvider{
			getFn: func(_ context.Context, _ string) (any, error) {
				return nil, nil
			},
		})
		assert.NotNil(t, uc)
	})
}

func TestGetMasters_Execute(t *testing.T) {
	t.Run("名前一覧が空なら空結果を返す", func(t *testing.T) {
		provider := &stubMasterProvider{
			getFn: func(_ context.Context, _ string) (any, error) {
				t.Fatal("should not be called")
				return nil, nil
			},
		}

		uc := newGetMasters(&stubLogger{}, provider)
		res, err := uc.Execute(context.Background(), &GetMastersRequest{Names: []string{}})
		assert.NoError(t, err)
		assert.NotNil(t, res)
		assert.Empty(t, res.List)
	})

	t.Run("取得失敗した名前をスキップして成功分のみ返す", func(t *testing.T) {
		provider := &stubMasterProvider{
			getFn: func(_ context.Context, name string) (any, error) {
				if name == "invalid" {
					return nil, errors.New("not found")
				}
				return []string{"ok-value"}, nil
			},
		}

		uc := newGetMasters(&stubLogger{}, provider)
		res, err := uc.Execute(context.Background(), &GetMastersRequest{Names: []string{"valid", "invalid"}})
		assert.NoError(t, err)
		assert.Len(t, res.List, 1)
		assert.Equal(t, "valid", res.List[0].Name)
		assert.Equal(t, []string{"ok-value"}, res.List[0].Values)
	})

	t.Run("注入したプロバイダーの結果を返す", func(t *testing.T) {
		provider := &stubMasterProvider{
			getFn: func(_ context.Context, name string) (any, error) {
				return "from-provider:" + name, nil
			},
		}

		uc := newGetMasters(&stubLogger{}, provider)
		res, err := uc.Execute(context.Background(), &GetMastersRequest{Names: []string{"fallback"}})
		assert.NoError(t, err)
		assert.Len(t, res.List, 1)
		assert.Equal(t, "fallback", res.List[0].Name)
		assert.Equal(t, "from-provider:fallback", res.List[0].Values)
	})
}
