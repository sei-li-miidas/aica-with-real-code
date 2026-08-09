package echo

import (
	"errors"
	"strconv"

	"github.com/labstack/echo/v4"
	"golang.org/x/exp/constraints"
)

func GetFromParam[T constraints.Integer](c echo.Context, path string) (T, error) {
	id, err := strconv.Atoi(c.Param(path))
	if err != nil {
		return 0, errors.New("invalid request")
	}
	return T(id), nil
}
