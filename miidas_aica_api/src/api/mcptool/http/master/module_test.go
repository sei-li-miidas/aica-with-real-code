package master

import (
	dto "aica/api/api/mcptool/http/master/dto"
	uc "aica/api/api/mcptool/usecase/master"
	mectx "aica/api/sdk/echo/context"
	merr "aica/api/sdk/error"
	"aica/api/sdk/logger"
	"context"
	"errors"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/labstack/echo/v4"
	"github.com/stretchr/testify/assert"
)

type stubLevelLogger struct{}

func (l *stubLevelLogger) Info(string, ...any)  {}
func (l *stubLevelLogger) Warn(string, ...any)  {}
func (l *stubLevelLogger) Error(string, ...any) {}
func (l *stubLevelLogger) Fatal(string, ...any) {}

type stubGetMastersUseCase struct {
	execute func(ctx context.Context, request *uc.GetMastersRequest) (*uc.Masters, error)
}

func (s *stubGetMastersUseCase) Execute(ctx context.Context, request *uc.GetMastersRequest) (*uc.Masters, error) {
	return s.execute(ctx, request)
}

func TestNewModule(t *testing.T) {
	t.Run("GetMastersユースケースファクトリがnilならエラー", func(t *testing.T) {
		module, err := NewModule(Dependencies{})
		assert.Nil(t, module)
		assert.EqualError(t, err, "new get masters usecase factory is required")
	})

	t.Run("必須依存がそろっていれば生成成功", func(t *testing.T) {
		module, err := NewModule(Dependencies{
			NewGetMastersUseCase: func(_ logger.LevelLogger) GetMastersUseCase {
				return &stubGetMastersUseCase{
					execute: func(_ context.Context, _ *uc.GetMastersRequest) (*uc.Masters, error) { return &uc.Masters{}, nil },
				}
			},
		})
		assert.NoError(t, err)
		assert.NotNil(t, module)
		assert.NotNil(t, module.Handler())
	})
}

func TestModuleHandler_NilReceiver(t *testing.T) {
	t.Run("レシーバーがnilならnilを返す", func(t *testing.T) {
		var module *Module
		assert.Nil(t, module.Handler())
	})
}

func TestSetup(t *testing.T) {
	t.Run("モジュールがnilならエラー", func(t *testing.T) {
		e := echo.New()
		err := Setup(e, nil)
		assert.EqualError(t, err, "master module handler is nil")
	})

	t.Run("マスタールートを登録できる", func(t *testing.T) {
		e := echo.New()
		module, err := NewModule(Dependencies{
			NewGetMastersUseCase: func(_ logger.LevelLogger) GetMastersUseCase {
				return &stubGetMastersUseCase{
					execute: func(_ context.Context, _ *uc.GetMastersRequest) (*uc.Masters, error) { return &uc.Masters{}, nil },
				}
			},
		})
		assert.NoError(t, err)
		assert.NoError(t, Setup(e, module))

		found := false
		for _, r := range e.Routes() {
			if r.Method == http.MethodGet && r.Path == "/masters/" {
				found = true
				break
			}
		}
		assert.True(t, found)
	})
}

func TestHandlerMasters(t *testing.T) {
	t.Run("バインド済みパラメーターの型が不正ならエラー", func(t *testing.T) {
		e := echo.New()
		req := httptest.NewRequest(http.MethodGet, "/masters/", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)

		h := NewHandler(func(_ logger.LevelLogger) GetMastersUseCase {
			return &stubGetMastersUseCase{
				execute: func(_ context.Context, _ *uc.GetMastersRequest) (*uc.Masters, error) {
					t.Fatal("usecase should not be called when bound param is invalid")
					return nil, nil
				},
			}
		})
		err := h.masters(c)
		assert.Error(t, err)
		assert.Equal(t, merr.ErrBadParameter, err)
	})

	t.Run("ユースケースがエラーを返したらそのまま返す", func(t *testing.T) {
		e := echo.New()
		req := httptest.NewRequest(http.MethodGet, "/masters/", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)
		mectx.SetBoundParam(c, &dto.GetMastersRequest{Names: []string{"x"}})
		mectx.SetLogger(c, &stubLevelLogger{})

		h := NewHandler(func(_ logger.LevelLogger) GetMastersUseCase {
			return &stubGetMastersUseCase{
				execute: func(_ context.Context, _ *uc.GetMastersRequest) (*uc.Masters, error) {
					return nil, errors.New("failed")
				},
			}
		})
		err := h.masters(c)
		assert.EqualError(t, err, "failed")
	})

	t.Run("正常時は200でレスポンスを返す", func(t *testing.T) {
		e := echo.New()
		req := httptest.NewRequest(http.MethodGet, "/masters/", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)
		mectx.SetBoundParam(c, &dto.GetMastersRequest{Names: []string{"x"}})
		mectx.SetLogger(c, &stubLevelLogger{})

		h := NewHandler(func(_ logger.LevelLogger) GetMastersUseCase {
			return &stubGetMastersUseCase{
				execute: func(_ context.Context, _ *uc.GetMastersRequest) (*uc.Masters, error) {
					return &uc.Masters{
						List: []*uc.Master{
							{Name: "x", Values: []string{"v"}},
						},
					}, nil
				},
			}
		})

		err := h.masters(c)
		assert.NoError(t, err)
		assert.Equal(t, http.StatusOK, rec.Code)
		assert.True(t, strings.Contains(rec.Body.String(), "\"Name\":\"x\""))
	})
}
