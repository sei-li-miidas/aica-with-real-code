"use client";

import { ChatMessageRole, ChatRequestType, ScrollEventType, PageName } from "@/constants/enum";
import { IWorkflowItem, IWorkflowStep, createNormalMessageItem, IWorkflowOptionItem, IWorkflowCategoryOption } from "@/lib/common";
import { sendWebSocketMessage } from "@/lib/socket";
import { addOrUpdateMainChatMessageItem, updateScrollEventType } from "@/lib/store/features/websocket/websocketSlice";
import { useAppDispatch } from "@/lib/store/hooks";
import { useState } from "react";
import JobMatchDiagnosisStep from "./JobMatchDiagnosisStep";
import { fetchApiData } from "@/utils/fetch";

interface Props {
  workflow: IWorkflowItem;
  onClose: () => void;
}

export default function JobMatchDiagnosisWorkflow({
  workflow,
  onClose,
}: Props) {
  const dispatch = useAppDispatch();
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [allAnswers, setAllAnswers] = useState<Record<string, number[]>>({});
  const [dynamicSteps, setDynamicSteps] = useState<IWorkflowStep[]>(workflow.workflowDefinition?.steps || []);
  const [isSearchError, setIsSearchError] = useState(false);

  const currentStep = dynamicSteps[currentStepIndex];

  if (!currentStep) {
    return null;
  }

  // 前のステップの回答を取得（Step2でStep1の回答を除外するため）
  const previousStepAnswers = currentStepIndex === 1
    ? allAnswers[dynamicSteps[currentStepIndex - 1]?.id?.toString()]
    : undefined;

  // 回答データを { label, value } の形式に構造化する共通関数
  const getStructuredPayload = (answers: Record<string, number[]>) => {
    const payload: Record<string, { label: string; value: number }[]> = {};
    dynamicSteps.forEach((step: IWorkflowStep) => {
      const stepId = step.id.toString();
      const stepAnswers = answers[stepId];
      if (stepAnswers) {
        payload[stepId] = stepAnswers.map((val) => {
          const flatOptions: IWorkflowOptionItem[] = step.options.flatMap((opt) => {
            // このワークフローの全stepのoptionsの型は`IWorkflowCategoryOption`の配列
            return (opt as IWorkflowCategoryOption).items;
          });
          const option = flatOptions.find((item) => item.value === val);
          return {
            label: option ? option.label : "",
            value: val,
          };
        });
      }
    });
    return payload;
  };

  const handleNext = async (stepAnswers: number[]) => {
    let updatedAnswers = {
      ...allAnswers,
      [currentStep.id.toString()]: stepAnswers,
    };

    // Step3まで進んだ後にStep1に戻って回答を更新した際、Step2の回答からStep1と重複する値を除外する
    if (currentStep.id === 1 && updatedAnswers["2"]) {
      updatedAnswers = {
        ...updatedAnswers,
        "2": updatedAnswers["2"].filter((val) => !stepAnswers.includes(val)),
      };
    }

    setAllAnswers(updatedAnswers);

    // ステップ2完了時に職種検索APIを呼び出し、ステップ3の選択肢を生成する
    if (currentStep.id === 2) {
      setIsSearchError(false);
      const emptyOptions = [{ id: "recommended", name: "", items: [] }];
      try {
        const result = await fetchApiData(
          "workflow/job_match_diagnosis/search_occupations",
          "職種の検索に失敗しました",
          {
            method: "POST",
            data: { answers: getStructuredPayload(updatedAnswers) },
          },
        );

        if (result.error) {
          console.error("職種の検索に失敗しました:", result.error);
          setIsSearchError(true);
          setDynamicSteps((prevSteps: IWorkflowStep[]) =>
            prevSteps.map(step => step.id === 3 ? { ...step, options: emptyOptions } : step)
          );
        } else {
          const jobTypes = result.data;
          setDynamicSteps((prevSteps: IWorkflowStep[]) => {
            return prevSteps.map(step => {
              if (step.id === 3) {
                if (!jobTypes || jobTypes.length === 0) {
                  return { ...step, options: emptyOptions };
                }
                return {
                  ...step,
                  options: [
                    {
                      id: "recommended",
                      name: "",
                      items: jobTypes.map((res: { 職種名: string; ID: number; 職種説明: string }) => ({
                        label: res["職種名"],
                        value: res["ID"],
                        description: res["職種説明"],
                        allowFreeText: false,
                      })),
                    },
                  ]
                };
              }
              return step;
            });
          });
        }
      } catch (error) {
        console.error("職種の検索に失敗しました:", error);
        setIsSearchError(true);
        setDynamicSteps((prevSteps: IWorkflowStep[]) =>
          prevSteps.map(step => step.id === 3 ? { ...step, options: emptyOptions } : step)
        );
      }
    }

    if (currentStepIndex < dynamicSteps.length - 1) {
      setCurrentStepIndex(currentStepIndex + 1);
    } else {
      // 完了時の処理
      submitAnswers(updatedAnswers);
    }
  };

  const handleBack = () => {
    setIsSearchError(false);
    if (currentStepIndex > 0) {
      setCurrentStepIndex(currentStepIndex - 1);
    } else {
      // ステップ1の場合は中断
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

  const submitAnswers = (answers: Record<string, number[]>) => {
    const structuredPayload = getStructuredPayload(answers);

    const payload = JSON.stringify({
      workflow_id: workflow.workflowDefinition?.id,
      answers: structuredPayload,
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

    // 回答をチャット履歴に表示するためにローカルに追加
    dynamicSteps.forEach((step: IWorkflowStep) => {
      const stepAnswers = structuredPayload[step.id.toString()] ?? [];

      // 質問をAIメッセージとして追加
      const questionMessageID = `q_${step.id}_${crypto.randomUUID()}`;
      dispatch(addOrUpdateMainChatMessageItem(
        createNormalMessageItem(ChatMessageRole.Agent, questionMessageID, step.questionPrompt)
      ));

      // 回答をユーザーメッセージとして追加
      const answerMessageID = `a_${step.id}_${crypto.randomUUID()}`;
      const answerTexts = stepAnswers.map((ans: { label: string }) => ans.label).filter(text => text !== "");
      dispatch(addOrUpdateMainChatMessageItem(
        createNormalMessageItem(ChatMessageRole.User, answerMessageID, answerTexts.join("、") || "選択なし")
      ));
    });

    dispatch(updateScrollEventType(ScrollEventType.NewUserMessage));
    onClose();
  };

  return (
    <JobMatchDiagnosisStep
      key={currentStep.id}
      step={currentStep as IWorkflowStep}
      answers={allAnswers[currentStep.id.toString()] ?? []}
      onNext={handleNext}
      onBack={handleBack}
      onCancel={handleCancel}
      isFirstStep={currentStepIndex === 0}
      isLastStep={currentStepIndex === dynamicSteps.length - 1}
      previousStepAnswers={previousStepAnswers}
      isSearchError={isSearchError}
    />
  );
}
