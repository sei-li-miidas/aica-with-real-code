package master

import (
	dto "aica/api/api/mcptool/http/master/dto"
	uc "aica/api/api/mcptool/usecase/master"
	mectx "aica/api/sdk/echo/context"
	merr "aica/api/sdk/error"
	"aica/api/sdk/logger"
	"context"
	"net/http"

	"github.com/labstack/echo/v4"
)

type GetMastersUseCase interface {
	Execute(ctx context.Context, request *uc.GetMastersRequest) (*uc.Masters, error)
}

type NewGetMastersUseCaseFunc func(l logger.LevelLogger) GetMastersUseCase

type Handler struct {
	newGetMastersUseCase NewGetMastersUseCaseFunc
}

func NewHandler(newGetMastersUseCase NewGetMastersUseCaseFunc) *Handler {
	return &Handler{newGetMastersUseCase: newGetMastersUseCase}
}

func (h *Handler) masters(c echo.Context) error {
	param, ok := mectx.BoundParam(c).(*dto.GetMastersRequest)
	if !ok {
		return merr.ErrBadParameter
	}
	request := &uc.GetMastersRequest{
		Names: param.Names,
	}
	if ret, err := h.newGetMastersUseCase(mectx.Logger(c)).Execute(c.Request().Context(), request); err != nil {
		return err
	} else {
		return c.JSON(http.StatusOK, ret)
	}
}
