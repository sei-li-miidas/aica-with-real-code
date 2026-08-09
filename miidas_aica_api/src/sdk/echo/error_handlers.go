package echo

import (
	"errors"
	"net/http"

	"github.com/labstack/echo/v4"
	perr "github.com/pkg/errors"

	mectx "aica/api/sdk/echo/context"
	merr "aica/api/sdk/error"
	mhttp "aica/api/sdk/http"
)

// ErrorHandler は各エラーをハンドリンクしproblem detailを返します。
func ErrorHandler(err error, c echo.Context) {
	he := &echo.HTTPError{}
	var ee merr.Error
	if errors.As(err, &he) {
		httpErrorHandler(err, he, c)
	} else if errors.As(err, &ee) {
		var sve merr.StructValidationError
		if errors.As(err, &sve) {
			structValidationErrorHandler(err, sve, c)
		} else {
			generalErrorHandler(err, ee, c)
		}
	} else {
		unknownErrorHandler(err, c)
	}
}

func structValidationErrorHandler(err error, sve merr.StructValidationError, c echo.Context) {
	code := determineStatusCode(c)
	loggingIfServerError(err, code, sve, c, "structValidationErrorHandler")

	msg := mhttp.NewStructValidationProblem(sve)
	setJSONResponse(c, code, msg)
}

func generalErrorHandler(err error, ee merr.Error, c echo.Context) {
	switch ee.Type() {
	case merr.FieldValidationErrorType:
		code := determineStatusCode(c)
		loggingIfServerError(err, code, ee, c, "generalErrorHandler FieldValidationErrorType")

		msg := mhttp.NewFieldValidationProblem(ee)
		setJSONResponse(c, code, msg)

	case merr.AppErrorType:
		code := determineStatusCode(c)
		loggingIfServerError(err, code, ee, c, "generalErrorHandler AppErrorType")

		msg := mhttp.NewAppErrorProblem(ee)
		setJSONResponse(c, code, msg)
	}
}

func httpErrorHandler(err error, he *echo.HTTPError, c echo.Context) {
	loggingIfServerError(err, he.Code, he, c, "httpErrorHandler")

	msg := mhttp.NewEchoHTTPProblem(he)
	setJSONResponse(c, he.Code, msg)
}

func unknownErrorHandler(err error, c echo.Context) {
	code := determineStatusCode(c)
	loggingIfServerError(err, code, err, c, "unknownErrorHandler")

	msg := mhttp.NewUnknownProblem()
	setJSONResponse(c, code, msg)
}

func loggingIfServerError(err error, code int, msg error, c echo.Context, via string) {
	if code >= http.StatusInternalServerError { // 5xx系のエラーはロギングする。
		if reason, isContinuable := merr.IsContinuable(err); isContinuable {
			mectx.Logger(c).Error(msg.Error(), merr.ContinuableErrLogKey, reason, "at", "loggingIfServerError", "via", via, "code", code, "error", perr.WithStack(err))
		} else if when, isFixLater := merr.IsFixLater(err); isFixLater {
			mectx.Logger(c).Error(msg.Error(), merr.FixLaterLogKey, when, "at", "loggingIfServerError", "via", via, "code", code, "error", perr.WithStack(err))
		} else {
			mectx.Logger(c).Error(msg.Error(), "at", "loggingIfServerError", "via", via, "code", code, "error", perr.WithStack(err))
		}
	}
}

func setJSONResponse(c echo.Context, code int, msg any) {
	c.Response().Header().Add("Content-Type", "application/problem+json")

	if err := c.JSON(code, msg); err != nil {
		mectx.Logger(c).Error("JSON encoding failed", "error", err, "code", code, "msg", msg)
	}
}

func determineStatusCode(c echo.Context) int {
	code, found := mectx.ErrorStatusCode(c)
	if !found {
		code = http.StatusNotImplemented // TODO: 599 に変更
	}
	return code
}
