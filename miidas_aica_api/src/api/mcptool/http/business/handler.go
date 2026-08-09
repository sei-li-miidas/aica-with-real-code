package business

import (
	businessUC "aica/api/api/mcptool/usecase/business"
	"aica/api/domain/user/apply/position"
	mecho "aica/api/sdk/echo"
	mectx "aica/api/sdk/echo/context"
	merr "aica/api/sdk/error"
	"aica/api/sdk/logger"
	"net/http"

	"github.com/labstack/echo/v4"
)

type (
	GetDetailUseCase interface {
		Execute(positionID position.ID) (*businessUC.GetDetailResponse, error)
	}

	NewGetDetailUseCaseFunc func(l logger.LevelLogger) GetDetailUseCase
)

type Handler struct {
	newGetDetailUseCase NewGetDetailUseCaseFunc
}

func NewHandler(newGetDetailUseCase NewGetDetailUseCaseFunc) *Handler {
	return &Handler{
		newGetDetailUseCase: newGetDetailUseCase,
	}
}

func (h *Handler) getDetail(c echo.Context) error {
	positionID, err := mecho.GetFromParam[position.ID](c, "position_id")
	if err != nil || positionID <= 0 {
		return merr.ErrInvalidRequest.WithStack()
	}

	res, err := h.newGetDetailUseCase(
		mectx.Logger(c),
	).Execute(positionID)
	if err != nil {
		return err
	}
	return c.JSON(http.StatusOK, res)
}
