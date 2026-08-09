"use client";

import "./page.scss";
import InitToast from "@/components/InitToast";
import SurveyLink from "@/components/SurveyLink";
import { useAppDispatch, useAppSelector } from "@/lib/store/hooks";
import Chat from "@/components/Chat";
import Box from "@mui/material/Box";
import { closeInitToast } from "@/lib/store/features/global_state/globalStateSlice";
import { PageName } from "@/constants/enum";

export default function ChatPage() {
  const dispatch = useAppDispatch();
  const initToastClosed = useAppSelector(
    (state) => state.globalState.initToastClosed,
  );
  const sessionID = useAppSelector((state) => state.websocket.sessionID);

  if (!initToastClosed) {
    return <InitToast onClose={() => dispatch(closeInitToast())} />;
  }

  return (
    <>
      {sessionID?.length > 0 && (
        <Box className="chat-survey-bar">
          <SurveyLink sessionId={sessionID} />
        </Box>
      )}
      <Box
        className={`main-container chat-main ${sessionID?.length > 0 ? "pt-60" : ""}`}
      >
        <Chat currentPage={PageName.Chat} />
      </Box>
    </>
  );
}
