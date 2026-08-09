package mv2

import (
	tmock "aica/api/api/mcptool/testutil/mock"
	"errors"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestNewMarketValueGateway_ReturnsRealGateway(t *testing.T) {
	original := cliConn
	cliConn = nil
	t.Cleanup(func() {
		cliConn = original
	})

	ok := assert.PanicsWithError(t, errors.New("grpc connection is not initialized").Error(), func() {
		_ = NewMarketValueGateway(&tmock.MockLogger{})
	})
	if !ok {
		t.Fatal("expected panic when grpc connection is not initialized")
	}
}
