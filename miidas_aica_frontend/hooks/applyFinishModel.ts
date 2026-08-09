import { ApplyResult } from "@/constants/enum";

export type ApplyNavigationTarget =
  | { kind: "none" }
  | { kind: "employeeOffer" }
  | { kind: "meetingComplete"; positionId: string };

type ApplyResponseSubset = {
  applyResult?: ApplyResult;
  detail?: {
    PositionID?: string | null;
  } | null;
};

export function mapApplyResponseToNavigation(
  response: ApplyResponseSubset,
): ApplyNavigationTarget {
  if (
    response.applyResult === ApplyResult.RegisterSuccess ||
    response.applyResult === ApplyResult.RegisterAlready ||
    response.applyResult === ApplyResult.MeetingApplicationAlready
  ) {
    return { kind: "employeeOffer" };
  }

  if (response.applyResult === ApplyResult.MeetingApplicationSuccess) {
    const positionId = response.detail?.PositionID;
    if (positionId) {
      return { kind: "meetingComplete", positionId };
    }

    return { kind: "employeeOffer" };
  }

  return { kind: "none" };
}
