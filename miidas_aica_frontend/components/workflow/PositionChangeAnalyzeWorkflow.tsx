"use client";

import { ChatMessageRole, ChatRequestType, ScrollEventType, PageName, WorkflowStepSelectionType } from "@/constants/enum";
import { IWorkflowItem, IWorkflowStep, IWorkflowOptionItem, createNormalMessageItem } from "@/lib/common";
import { sendWebSocketMessage } from "@/lib/socket";
import { addOrUpdateMainChatMessageItem, updateScrollEventType } from "@/lib/store/features/websocket/websocketSlice";
import { useAppDispatch } from "@/lib/store/hooks";
import { useState } from "react";
import PositionChangeAnalyzeStep from "./PositionChangeAnalyzeStep";
import { fetchApiData } from "@/utils/fetch";

type StepAnswer = { value: number; text?: string };

interface Props {
  workflow: IWorkflowItem;
  onClose: () => void;
}

export default function PositionChangeAnalyzeWorkflow({ workflow, onClose }: Props) {
  const dispatch = useAppDispatch();
  const steps = workflow.workflowDefinition?.steps || [];
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [allAnswers, setAllAnswers] = useState<Record<string, StepAnswer[]>>({});
  const [summaryData, setSummaryData] = useState<{ summary: string; explanation: string; keywords: string[] } | null>(null);
  const [isSummaryError, setIsSummaryError] = useState(false);

  const currentStep = steps[currentStepIndex];

  if (!currentStep) {
    return null;
  }

  const getStructuredPayload = (answers: Record<string, StepAnswer[]>) => {
    const payload: Record<string, { label: string; value: number; text?: string }[]> = {};
    steps.forEach((step: IWorkflowStep) => {
      const stepId = step.id.toString();
      const stepAnswers = answers[stepId];
      if (stepAnswers) {
        // position_change_analyze ワークフローのステップは常にフラット形式（IWorkflowOptionItem[]）で提供される
        const flatOptions = step.options as IWorkflowOptionItem[];
        payload[stepId] = stepAnswers.map((ans) => {
          const option = flatOptions.find((item) => item.value === ans.value);
          return {
            label: option?.label ?? "",
            value: ans.value,
            ...(ans.text ? { text: ans.text } : {}),
          };
        });
      }
    });
    return payload;
  };

  const handleNext = async (stepAnswers: StepAnswer[]) => {
    const updatedAnswers = {
      ...allAnswers,
      [currentStep.id.toString()]: stepAnswers
    };
    setAllAnswers(updatedAnswers);

    // ステップ4完了時にサマリーを生成APIを呼び出す
    if (currentStep.id === 4) {
      setIsSummaryError(false);
      try {
        const result = await fetchApiData(
          "workflow/position_change_analyze/generate_summary",
          "転職軸の生成に失敗しました",
          {
            method: "POST",
            data: { answers: getStructuredPayload(updatedAnswers) },
          }
        );
        if (result.error || result.data?.summary == null || result.data?.explanation == null || !Array.isArray(result.data?.keywords)) {
          console.error("転職軸の生成に失敗しました:", result.error);
          setIsSummaryError(true);
          setSummaryData(null);
        } else {
          setSummaryData({
            summary: result.data.summary,
            explanation: result.data.explanation,
            keywords: result.data.keywords,
          });
        }
      } catch (error) {
        console.error("転職軸の生成に失敗しました:", error);
        setIsSummaryError(true);
        setSummaryData(null);
      }
    }

    if (currentStepIndex < steps.length - 1) {
      setCurrentStepIndex(currentStepIndex + 1);
    } else {
      submitAnswers(updatedAnswers);
    }
  };

  const handleBack = () => {
    setIsSummaryError(false);
    if (currentStepIndex > 0) {
      setCurrentStepIndex(currentStepIndex - 1);
    } else {
      handleCancel();
    }
  };

  const handleCancel = () => {
    const payload = JSON.stringify({
      workflow_id: workflow.workflowDefinition?.id,
    });

    const messageID = `developer_${crypto.randomUUID()}`;

    sendWebSocketMessage(
      dispatch,
      ChatRequestType.WorkflowCancelled,
      PageName.Chat,
      PageName.Chat,
      payload,
      null,
      messageID,
      false
    );

    onClose();
  };

  const formatKeywords = (keywords: string[]): string | null => {
    if (keywords.length === 0) return null;
    return `この転職軸に合った求人を探すには、${keywords.map((kw) => `「${kw}」`).join("、")}などのキーワードが参考になりそうです。`;
  };

  const submitAnswers = (answers: Record<string, StepAnswer[]>) => {
    const structuredPayload = getStructuredPayload(answers);

    const payload = JSON.stringify({
      workflow_id: workflow.workflowDefinition?.id,
      answers: structuredPayload,
      extra: {
        summary: summaryData?.summary ?? null,
        explanation: summaryData?.explanation ?? null,
        keyword_suggestion: summaryData ? formatKeywords(summaryData.keywords) : null,
      },
    });

    const messageID = `developer_${crypto.randomUUID()}`;

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

    steps.forEach((step: IWorkflowStep) => {
      const stepAnswers = structuredPayload[step.id.toString()] ?? [];
      const isMultiple = step.selectionType === WorkflowStepSelectionType.Multiple;

      const questionMessageID = `q_${step.id}_${crypto.randomUUID()}`;
      const keywordsText = (step.id === 5 && summaryData) ? formatKeywords(summaryData.keywords) : null;
      const questionText = (step.id === 5 && summaryData)
        ? `${step.questionPrompt}\n\n【あなたの転職軸】\n${summaryData.summary}\n\n【解説】\n${summaryData.explanation}${keywordsText ? `\n\n【求人を探すポイント】\n${keywordsText}` : ""}`
        : step.questionPrompt;
      dispatch(addOrUpdateMainChatMessageItem(
        createNormalMessageItem(ChatMessageRole.Agent, questionMessageID, questionText)
      ));

      const answerMessageID = `a_${step.id}_${crypto.randomUUID()}`;
      const answerTexts = stepAnswers
        .map((ans: { label: string; value: number; text?: string }, idx: number) => {
          if (!ans.label) return "";
          const prefix = isMultiple ? `${idx + 1}. ` : "";
          const mainText = `${prefix}${ans.label}`;
          return ans.text ? `${mainText}\n${ans.text}` : mainText;
        })
        .filter((text) => text !== "");

      dispatch(addOrUpdateMainChatMessageItem(
        createNormalMessageItem(ChatMessageRole.User, answerMessageID, answerTexts.join("\n\n") || "選択なし")
      ));
    });

    dispatch(updateScrollEventType(ScrollEventType.NewUserMessage));
    onClose();
  };

  return (
    <PositionChangeAnalyzeStep
      key={currentStep.id}
      step={currentStep as IWorkflowStep}
      answers={allAnswers[currentStep.id.toString()] ?? []}
      onNext={handleNext}
      onBack={handleBack}
      onCancel={handleCancel}
      isFirstStep={currentStepIndex === 0}
      isLastStep={currentStepIndex === steps.length - 1}
      summary={summaryData}
      isSummaryError={isSummaryError}
    />
  );
}
