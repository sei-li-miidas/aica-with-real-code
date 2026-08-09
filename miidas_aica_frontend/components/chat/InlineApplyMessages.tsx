"use client";

import { ReactNode } from "react";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Plane from "@/components/icons/Plane";
import {
  ApplyResult,
  ApplyValidationError,
  PageName,
  SessionStatus,
} from "@/constants/enum";

type Props = {
  currentPage: string;
  isApplying: boolean;
  applyLoading: boolean;
  applyResult: ApplyResult;
  applyError: ApplyValidationError;
  profileCompleted: boolean;
  sessionStatus: SessionStatus;
  applyResultDetail: ReactNode;
};

export default function InlineApplyMessages({
  currentPage,
  isApplying,
  applyLoading,
  applyResult,
  applyError,
  profileCompleted,
  sessionStatus,
  applyResultDetail,
}: Props) {
  if (currentPage !== PageName.Chat) return null;

  if (isApplying) {
    if (applyLoading) {
      return (
        <div className="apply-progress">
          <Plane className="apply-progress__plane" />
        </div>
      );
    }

    if (ApplyResult.RegisterFail === applyResult) {
      if (applyError === ApplyValidationError.DuplicateEmailOrPhone) {
        return (
          <div className="apply-error">
            <Typography variant="body2" color="text.secondary">
              ⚠️ メールアドレスまたは電話番号が既に登録されてます。
              <Box component="span" className="apply-error__highlight">
                別のメールアドレスまたは電話番号を登録してください。
              </Box>
            </Typography>
          </div>
        );
      }

      if (applyError === ApplyValidationError.Other && !profileCompleted) {
        return (
          <div className="apply-error">
            <Typography variant="body2" color="text.secondary">
              ⚠️ 入力内容に不備があります。
              <Box component="span" className="apply-error__highlight">
                赤字
              </Box>
              で表示された項目をご確認ください。
            </Typography>
          </div>
        );
      }

      return (
        <Typography
          variant="body2"
          color="text.secondary"
          className="apply-actions__message"
        >
          申し訳ありません、アカウント登録に失敗しました。しばらく時間をおいて、再度「ミイダスに登録する」を押してください。
        </Typography>
      );
    }

    if (
      ApplyResult.Unknown === applyResult ||
      ApplyResult.InvalidSessionStatus === applyResult
    ) {
      return (
        <Typography
          variant="body2"
          color="text.secondary"
          className="apply-actions__message"
        >
          申し訳ありません、アカウント登録に失敗しました。しばらく時間をおいて、再度「ミイダスに登録する」を押してください。
        </Typography>
      );
    }

    return null;
  }

  if (
    sessionStatus == SessionStatus.Applied ||
    sessionStatus == SessionStatus.Registered
  ) {
    if (ApplyResult.MeetingApplicationFail === applyResult) {
      return applyResultDetail;
    }
  }

  return null;
}
