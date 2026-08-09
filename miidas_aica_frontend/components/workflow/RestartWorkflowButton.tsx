"use client";

import { useCallback } from "react";
import AutorenewRoundedIcon from "@mui/icons-material/AutorenewRounded";
import "./RestartWorkflowButton.scss";
import { createWorkflowItem, IRestartWorkflowButtonItem } from "@/lib/common";
import {
  dismissRestartWorkflowButton,
  setModalWorkflow,
} from "@/lib/store/features/websocket/websocketSlice";
import { useAppDispatch, useAppSelector } from "@/lib/store/hooks";
import { WORKFLOW_REGISTRY } from "./registry";

interface Props {
  item: IRestartWorkflowButtonItem;
}

export default function RestartWorkflowButton({ item }: Props) {
  const dispatch = useAppDispatch();
  const dismissedRestartWorkflowIds = useAppSelector(
    (state) => state.websocket.dismissedRestartWorkflowIds,
  );

  const handleClick = useCallback(() => {
    dispatch(
      setModalWorkflow(
        createWorkflowItem(item.itemId, item.workflowDefinition),
      ),
    );
    dispatch(dismissRestartWorkflowButton(item.itemId));
  }, [dispatch, item.itemId, item.workflowDefinition]);

  if (dismissedRestartWorkflowIds.includes(item.itemId)) {
    return null;
  }

  // 未登録ワークフローはモーダルが開いた瞬間に閉じてしまうため表示しない
  if (!WORKFLOW_REGISTRY[item.workflowDefinition.id]) {
    return null;
  }

  return (
    <div className="restart-workflow-button">
      <p className="restart-workflow-button__heading">
        {item.workflowDefinition.name}を開始しますか？
      </p>
      <button
        type="button"
        className="restart-workflow-button__button"
        onClick={handleClick}
      >
        <AutorenewRoundedIcon className="restart-workflow-button__icon" />
        <span className="restart-workflow-button__button-label">開始する</span>
      </button>
    </div>
  );
}
