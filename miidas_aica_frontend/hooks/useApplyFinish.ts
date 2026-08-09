"use client";

import { useCallback, useState } from "react";
import {
  ApplyResult,
  ApplyValidationError,
  PageName,
  SessionStatus,
} from "@/constants/enum";
import { fetchApiData } from "@/utils/fetch";
import { setSessionStatus } from "@/lib/store/features/websocket/websocketSlice";
import {
  updateBasicInfoApplyErrors,
  updateCareerApplyErrors,
  updateEducationApplyErrors,
  updateWillApplyErrors,
} from "@/lib/store/features/profile/profileSlice";
import type { AppDispatch } from "@/lib/store";
import type { FieldError } from "@/components/Profile";
import type { IPositionSummary } from "@/lib/common";
import {
  mapApplyResponseToNavigation,
  type ApplyNavigationTarget,
} from "@/hooks/applyFinishModel";

type Result = {
  apply: () => void;
  applyLoading: boolean;
  applyResult: ApplyResult;
  applyError: ApplyValidationError;
  positionsApplySucceeded: Array<IPositionSummary>;
  positionsApplyFailed: Array<IPositionSummary>;
};

function navigateAfterApply(target: ApplyNavigationTarget): void {
  if (target.kind === "employeeOffer") {
    window.location.href = "/offer/employee";
    return;
  }

  if (target.kind === "meetingComplete") {
    window.location.href = `/positions/${target.positionId}/meeting_complete`;
  }
}

export function useApplyFinish(
  dispatch: AppDispatch,
  sessionStatus: SessionStatus,
): Result {
  const [applyError, setApplyError] = useState(ApplyValidationError.None);
  const [applyResult, setApplyResult] = useState(ApplyResult.BeforeApply);
  const [positionsApplySucceeded, setPositionsApplySucceeded] = useState<
    Array<IPositionSummary>
  >([]);
  const [positionsApplyFailed, setPositionsApplyFailed] = useState<
    Array<IPositionSummary>
  >([]);
  const [applyLoading, setApplyLoading] = useState(false);

  const apply = useCallback(() => {
    setApplyLoading(true);

    const endpoint = "apply/finish";
    const errorMessage =
      sessionStatus == SessionStatus.Applying
        ? "応募が失敗しました"
        : "登録が失敗しました";
    try {
      fetchApiData(endpoint, errorMessage, {
        method: "POST",
      })
        .then((res) => {
          if (!res.data) {
            console.error(errorMessage, res.error);
          }
          if (res.data.SessionStatus) {
            dispatch(setSessionStatus(res.data.SessionStatus));
          }

          if (res.httpStatus === 200) {
            const detail = res.data.Detail;

            const navigationTarget = mapApplyResponseToNavigation({
              applyResult: res.data.ApplyResult,
              detail,
            });
            if (navigationTarget.kind !== "none") {
              if (
                navigationTarget.kind === "employeeOffer" &&
                res.data.ApplyResult === ApplyResult.MeetingApplicationSuccess
              ) {
                console.error("Invalid positionID:", detail?.PositionID);
              }

              navigateAfterApply(navigationTarget);
              return;
            }

            setPositionsApplySucceeded(detail.SuccessfulPositions ?? []);
            setPositionsApplyFailed(detail.FailedPositions ?? []);
          } else if (
            (res.httpStatus == 409 || res.httpStatus == 400) &&
            ApplyResult.RegisterFail === res.data.ApplyResult
          ) {
            const detail = res.data.Detail;
            if (!detail) {
              console.error(
                "Invalid detail of apply validation error:",
                detail,
              );

              setApplyResult(ApplyResult.Unknown);
              return;
            }

            if ((detail.Errors?.length ?? 0) === 0) {
              console.error("No apply errors found in detail:", detail);

              setApplyResult(ApplyResult.Unknown);
              return;
            }

            if (res.httpStatus == 409) {
              const basicInfoErrors = detail.Errors?.filter(
                (err: FieldError) => err.Page === PageName.ProfileBasicInfo,
              );
              if ((basicInfoErrors?.length ?? 0) > 0) {
                const duplicateEmailOrPhoneError = basicInfoErrors?.some(
                  (err: FieldError) =>
                    err.Field === "email" || err.Field === "phoneNo",
                );

                if (duplicateEmailOrPhoneError) {
                  dispatch(updateBasicInfoApplyErrors(basicInfoErrors));

                  setApplyError(ApplyValidationError.DuplicateEmailOrPhone);
                  setApplyResult(ApplyResult.RegisterFail);

                  return;
                } else {
                  console.error(
                    "Unexpected 409 apply validation error:",
                    basicInfoErrors,
                  );
                }
              }
            }

            const basicInfoErrors: FieldError[] = [];
            const educationErrors: FieldError[] = [];
            const careerErrors: FieldError[] = [];
            const willErrors: FieldError[] = [];

            for (const err of detail.Errors) {
              if (err.Page === PageName.ProfileBasicInfo) {
                basicInfoErrors.push(err);
              } else if (err.Page === PageName.ProfileEducation) {
                educationErrors.push(err);
              } else if (err.Page === PageName.ProfileCarrer) {
                careerErrors.push(err);
              } else if (err.Page === PageName.ProfileWill) {
                willErrors.push(err);
              }
            }

            if (basicInfoErrors.length > 0) {
              dispatch(updateBasicInfoApplyErrors(basicInfoErrors));
            }
            if (educationErrors.length > 0) {
              dispatch(updateEducationApplyErrors(educationErrors));
            }
            if (careerErrors.length > 0) {
              dispatch(updateCareerApplyErrors(careerErrors));
            }
            if (willErrors.length > 0) {
              dispatch(updateWillApplyErrors(willErrors));
            }
          }

          setApplyError(ApplyValidationError.Other);
          setApplyResult(res.data?.ApplyResult ?? ApplyResult.Unknown);
        })
        .catch((error) => {
          console.error(errorMessage, error);
          setApplyResult(ApplyResult.Unknown);
        })
        .finally(() => {
          setApplyLoading(false);
        });
    } catch (error) {
      console.error(errorMessage, error);
      setApplyLoading(false);
    }
  }, [dispatch, sessionStatus]);

  return {
    apply,
    applyLoading,
    applyResult,
    applyError,
    positionsApplySucceeded,
    positionsApplyFailed,
  };
}
