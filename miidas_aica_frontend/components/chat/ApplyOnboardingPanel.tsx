"use client";

import { RefObject, useMemo } from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Link from "@mui/material/Link";
import { ChatMessage } from "@/components/ChatMessage";
import Miibo from "@/components/icons/Miibo";
import Profile from "@/components/Profile";
import { ChatMessageRole } from "@/constants/enum";

type Props = {
  hasAgreedToTermsOfUse: boolean;
  onAgreeTerms: () => void;
  profileCompleted: boolean;
  profileRef: RefObject<HTMLDivElement | null>;
};

export default function ApplyOnboardingPanel({
  hasAgreedToTermsOfUse,
  onAgreeTerms,
  profileCompleted,
  profileRef,
}: Props) {
  const contents = useMemo(() => {
    const result = [];

    result.push(
      <div key={"user-profile-agreement"}>
        <Box className="chat-message-container">
          <Box className="role">
            <Miibo />
          </Box>
          <Box className="chat-message-content agent">
            承知しました！では、以下の情報をすべて教えてください。
            <br />
            「未入力あり」が全て「入力済み」になれば次のステップに進めます。
            <br />※ あらかじめ
            <Link href="/agreement?privacy=1" target="_blank">
              プライバシーポリシー
            </Link>
            と
            <Link href="/agreement?terms=1" target="_blank">
              利用規約
            </Link>
            を確認の上、入力画面に進んでください。
          </Box>
        </Box>
        {!hasAgreedToTermsOfUse && (
          <Button
            variant="contained"
            color="primary"
            fullWidth
            onClick={onAgreeTerms}
          >
            同意して登録へ進む
          </Button>
        )}
      </div>,
    );

    if (hasAgreedToTermsOfUse) {
      result.push(
        <div key={"user-profile"} ref={profileRef}>
          <Profile />
        </div>,
      );

      if (profileCompleted) {
        result.push(
          <div key={"user-profile-input-completed"}>
            <Box className="chat-message-container">
              <ChatMessage
                showIcon={false}
                role={ChatMessageRole.Agent}
                message="入力お疲れ様でした！"
              />
            </Box>
          </div>,
        );
      }
    }

    return result;
  }, [hasAgreedToTermsOfUse, onAgreeTerms, profileCompleted, profileRef]);

  return <>{contents}</>;
}
