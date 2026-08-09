"use client";

import "./WorkflowInlineItem.scss";
import React, { useState, useMemo } from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import Checkbox from "@mui/material/Checkbox";
import TextField from "@mui/material/TextField";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import { ChatMessage } from "@/components/ChatMessage";

import { 
  ChatMessageRole,
  ChatRequestType,
  ScrollEventType,
  PageName,
  WorkflowStepSelectionType,
  SocketStatus
} from "@/constants/enum";
import {
  IWorkflowItem,
  IWorkflowOptionItem,
  IWorkflowCategoryOption,
  createNormalMessageItem,
} from "@/lib/common";
import { sendWebSocketMessage } from "@/lib/socket";
import { addOrUpdateMainChatMessageItem, updateScrollEventType, setInlineWorkflow } from "@/lib/store/features/websocket/websocketSlice";
import { useAppDispatch, useAppSelector } from "@/lib/store/hooks";

interface Props {
  item: IWorkflowItem;
}

export default function WorkflowInlineItem({ item }: Props) {
  const dispatch = useAppDispatch();
  const activeInlineWorkflow = useAppSelector((state) => state.websocket.inlineWorkflow);
  const socketStatus = useAppSelector((state) => state.websocket.socketStatus);
  const isActive = activeInlineWorkflow?.itemId === item.itemId;

  const workflow = item.workflowDefinition;
  const currentStep = workflow.steps[0]; // インラインは単一ステップ想定

  const [selectedValues, setSelectedValues] = useState<number[]>([]);
  const [freeTexts, setFreeTexts] = useState<Record<number, string>>({});
  const [infoDialogOpen, setInfoDialogOpen] = useState(false);
  const [selectedOptionInfo, setSelectedOptionInfo] = useState<IWorkflowOptionItem | null>(null);

  const isMultiple = currentStep.selectionType === WorkflowStepSelectionType.Multiple;
  const isSocketDisconnected = socketStatus < SocketStatus.Connected;

  // 選択肢をフラットなリストに変換
  const flatOptions = useMemo(() => {
    return currentStep.options.flatMap((opt) => {
      if ("items" in opt) {
        return (opt as IWorkflowCategoryOption).items;
      }
      return [opt as IWorkflowOptionItem];
    });
  }, [currentStep.options]);

  const handleToggle = (option: IWorkflowOptionItem) => {
    if (isSocketDisconnected) return;

    const value = option.value;
    if (isMultiple) {
      const currentIndex = selectedValues.indexOf(value);
      const newChecked = [...selectedValues];
      if (currentIndex === -1) {
        newChecked.push(value);
      } else {
        newChecked.splice(currentIndex, 1);
      }
      setSelectedValues(newChecked);
    } else {
      setSelectedValues([value]);
      // 自由入力不可の場合は即送信
      if (!option.allowFreeText) {
        submitAnswers([value], {});
      }
    }
  };

  const handleTextChange = (value: number, text: string) => {
    setFreeTexts((prev) => ({ ...prev, [value]: text.slice(0, 1000) }));
  };

  const showSubmitButton = useMemo(() => {
    if (isMultiple) return true;
    if (selectedValues.length > 0) {
      const selectedOption = flatOptions.find((o) => o.value === selectedValues[0]);
      return !!selectedOption?.allowFreeText;
    }
    return false;
  }, [isMultiple, selectedValues, flatOptions]);

  const isSubmitDisabled = useMemo(() => {
    if (isSocketDisconnected) return true;
    if (selectedValues.length === 0) return true;

    // 自由入力が選択されている場合、テキストが入力されているかチェック
    for (const val of selectedValues) {
      const option = flatOptions.find((o) => o.value === val);
      if (option?.allowFreeText && (!freeTexts[val] || freeTexts[val].trim() === "")) {
        return true;
      }
    }
    return false;
  }, [selectedValues, freeTexts, flatOptions]);

  const submitAnswers = (values: number[], texts: Record<number, string>) => {
    const structuredAnswers: Record<string, { label: string; value: number; text?: string }[]> = {
      [currentStep.id.toString()]: values.map((val) => {
        const opt = flatOptions.find((o) => o.value === val);
        return {
          label: opt?.label || "",
          value: val,
          ...(opt?.allowFreeText ? { text: texts[val] } : {}),
        };
      }),
    };

    const payload = JSON.stringify({
      workflow_id: workflow.id,
      answers: structuredAnswers,
    });

    const messageID = `input_${crypto.randomUUID()}`;
    sendWebSocketMessage(
      dispatch,
      ChatRequestType.WorkflowAnswersSubmitted,
      PageName.Chat,
      PageName.Chat,
      payload,
      null,
      messageID,
      false
    );

    // チャット履歴に反映
    dispatch(addOrUpdateMainChatMessageItem(
      createNormalMessageItem(ChatMessageRole.Agent, `q_${item.itemId}`, currentStep.questionPrompt)
    ));
    const answerLabels = structuredAnswers[currentStep.id.toString()].map(a =>
      a.text ? `${a.label}\n${a.text}` : a.label
    );
    dispatch(addOrUpdateMainChatMessageItem(
      createNormalMessageItem(ChatMessageRole.User, `a_${item.itemId}`, answerLabels.join("\n\n"))
    ));

    dispatch(setInlineWorkflow(null));
    dispatch(updateScrollEventType(ScrollEventType.NewUserMessage));
  };

  const handleOpenInfo = (e: React.MouseEvent<HTMLButtonElement>, option: IWorkflowOptionItem) => {
    e.stopPropagation();
    setSelectedOptionInfo(option);
    setInfoDialogOpen(true);
  };

  if (!isActive) {
    return null;
  }

  return (
    <Box className="workflow-inline-item">
      {currentStep.questionPrompt && (
        <Box className="chat-message-container message">
          <ChatMessage
            showIcon={true}
            role={ChatMessageRole.Agent}
            message={currentStep.questionPrompt}
          />
        </Box>
      )}

      <Box className={`options-list ${isSocketDisconnected ? "disabled" : ""}`}>
        {flatOptions.map((option) => {
          const isSelected = selectedValues.includes(option.value);
          return (
            <Box
              key={option.value}
              className={`option-row ${isSelected ? "selected" : ""}`}
              onClick={() => handleToggle(option)}
            >
              {isMultiple && (
                <Checkbox
                  checked={isSelected}
                  color="primary"
                  icon={
                    <span className="option-checkbox-icon" />
                  }
                  checkedIcon={
                    <span className="option-checkbox-icon selected" />
                  }
                />
              )}
              <Box component="span" className={`option-label ${isSelected ? "selected" : ""}`}>
                {option.label}
              </Box>
              {isSelected && option.allowFreeText && (
                <Box className="free-text-container" onClick={(e: React.MouseEvent<HTMLDivElement>) => e.stopPropagation()}>
                  <TextField
                    multiline
                    maxRows={4}
                    fullWidth
                    placeholder="詳細を入力"
                    value={freeTexts[option.value] || ""}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleTextChange(option.value, e.target.value)}
                    variant="outlined"
                    slotProps={{
                      root: { className: "workflow-free-text" },
                      htmlInput: { maxLength: 1000 },
                      input: { className: "workflow-free-text-input-root" },
                    }}
                  />
                </Box>
              )}
              {option.description && (
                <Box
                  component="button"
                  type="button"
                  aria-label={`${option.label} の詳細`}
                  onClick={(e: React.MouseEvent<HTMLButtonElement>) => {
                    handleOpenInfo(e, option);
                  }}
                  className="help-icon"
                >
                  ?
                </Box>
              )}
            </Box>
          );
        })}
      </Box>

      {showSubmitButton && (
        <Box className="action-footer">
          <Button
            variant="contained"
            fullWidth
            className="action-footer-button"
            disabled={isSubmitDisabled || isSocketDisconnected}
            onClick={() => submitAnswers(selectedValues, freeTexts)}
          >
            決定
          </Button>
        </Box>
      )}

      <Dialog open={infoDialogOpen} onClose={() => setInfoDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{selectedOptionInfo?.label}</DialogTitle>
        <DialogContent dividers>
          <Typography variant="body2">
            {selectedOptionInfo?.description}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInfoDialogOpen(false)}>閉じる</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
