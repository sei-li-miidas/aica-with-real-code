package master

import (
	dto "aica/api/api/mcptool/http/master/dto"
	"context"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"

	uc "aica/api/api/mcptool/usecase/master"
	mectx "aica/api/sdk/echo/context"
	merr "aica/api/sdk/error"
	"aica/api/sdk/logger"

	"github.com/labstack/echo/v4"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// MockGetMastersUseCase is a mock implementation of GetMastersUseCase
type MockGetMastersUseCase struct {
	mock.Mock
}

func (m *MockGetMastersUseCase) Execute(ctx context.Context, request *uc.GetMastersRequest) (*uc.Masters, error) {
	args := m.Called(ctx, request)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*uc.Masters), args.Error(1)
}

// MockLogger is a simple mock logger
type MockLogger struct {
	mock.Mock
}

// Ensure MockLogger implements logger.LevelLogger interface
func (m *MockLogger) Info(msg string, keyvals ...any)  {}
func (m *MockLogger) Warn(msg string, keyvals ...any)  {}
func (m *MockLogger) Error(msg string, keyvals ...any) {}
func (m *MockLogger) Fatal(msg string, keyvals ...any) {}

// TestHandler contains all handler tests
func TestHandler(t *testing.T) {
	t.Run("正常にマスターを取得", func(t *testing.T) {
		// Arrange
		expectedMasters := &uc.Masters{
			// Populate with test data based on Masters struct
		}

		mockUseCase := new(MockGetMastersUseCase)
		mockUseCase.On("Execute", mock.Anything, mock.Anything).Return(expectedMasters, nil)

		handler := NewHandler(func(l logger.LevelLogger) GetMastersUseCase {
			return mockUseCase
		})

		// Create echo context
		e := echo.New()
		req := httptest.NewRequest(http.MethodGet, "/masters", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)

		// Set logger and bound parameters
		mockLogger := &MockLogger{}
		mectx.SetLogger(c, mockLogger)
		mectx.SetBoundParam(c, &dto.GetMastersRequest{})

		// Act
		err := handler.masters(c)

		// Assert
		assert.NoError(t, err)
		assert.Equal(t, http.StatusOK, rec.Code)
		mockUseCase.AssertExpectations(t)
	})

	t.Run("無効なパラメータ型の場合エラー", func(t *testing.T) {
		handler := NewHandler(func(l logger.LevelLogger) GetMastersUseCase {
			return new(MockGetMastersUseCase)
		})

		// Create echo context
		e := echo.New()
		req := httptest.NewRequest(http.MethodGet, "/masters", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)

		// Set logger but with wrong parameter type
		mockLogger := &MockLogger{}
		mectx.SetLogger(c, mockLogger)
		mectx.SetBoundParam(c, "invalid_param")

		// Act
		err := handler.masters(c)

		// Assert
		assert.Error(t, err)
		assert.Equal(t, merr.ErrBadParameter, err)
	})

	t.Run("バインドされたパラメータがない場合エラー", func(t *testing.T) {
		handler := NewHandler(func(l logger.LevelLogger) GetMastersUseCase {
			return new(MockGetMastersUseCase)
		})

		// Create echo context
		e := echo.New()
		req := httptest.NewRequest(http.MethodGet, "/masters", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)

		// Set logger but no bound param
		mockLogger := &MockLogger{}
		mectx.SetLogger(c, mockLogger)

		// Act
		err := handler.masters(c)

		// Assert
		assert.Error(t, err)
		assert.Equal(t, merr.ErrBadParameter, err)
	})

	t.Run("ユースケースがエラーを返す場合", func(t *testing.T) {
		// Arrange
		expectedError := errors.New("use case error")

		mockUseCase := new(MockGetMastersUseCase)
		mockUseCase.On("Execute", mock.Anything, mock.Anything).Return(nil, expectedError)

		handler := NewHandler(func(l logger.LevelLogger) GetMastersUseCase {
			return mockUseCase
		})

		// Create echo context
		e := echo.New()
		req := httptest.NewRequest(http.MethodGet, "/masters", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)

		// Set logger and bound parameters
		mockLogger := &MockLogger{}
		mectx.SetLogger(c, mockLogger)
		mectx.SetBoundParam(c, &dto.GetMastersRequest{})

		// Act
		err := handler.masters(c)

		// Assert
		assert.Error(t, err)
		assert.Equal(t, expectedError, err)
		mockUseCase.AssertExpectations(t)
	})

	t.Run("コンテキストが正しく渡される", func(t *testing.T) {
		// Arrange
		mockUseCase := new(MockGetMastersUseCase)
		mockUseCase.On("Execute", mock.MatchedBy(func(ctx context.Context) bool {
			return ctx != nil
		}), mock.Anything).Return(&uc.Masters{}, nil)

		handler := NewHandler(func(l logger.LevelLogger) GetMastersUseCase {
			return mockUseCase
		})

		// Create echo context
		e := echo.New()
		req := httptest.NewRequest(http.MethodGet, "/masters", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)

		// Set logger and bound parameters
		mockLogger := &MockLogger{}
		mectx.SetLogger(c, mockLogger)
		mectx.SetBoundParam(c, &dto.GetMastersRequest{})

		// Act
		err := handler.masters(c)

		// Assert
		assert.NoError(t, err)
		mockUseCase.AssertExpectations(t)
	})
}
