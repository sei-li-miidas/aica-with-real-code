package mock

// MockLogger logger.LevelLoggerのモック
type MockLogger struct{}

func (m *MockLogger) Info(message string, fields ...any)  {}
func (m *MockLogger) Error(message string, fields ...any) {}
func (m *MockLogger) Warn(message string, fields ...any)  {}
func (m *MockLogger) Fatal(message string, fields ...any) {}
