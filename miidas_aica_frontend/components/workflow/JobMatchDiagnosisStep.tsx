"use client";

import "./JobMatchDiagnosisStep.scss";
import React, { useState } from "react";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Checkbox from "@mui/material/Checkbox";
import Typography from "@mui/material/Typography";
import { SocketStatus } from "@/constants/enum";
import JobtypeHelpDialog from "@/components/chat/jobSearchFilterDialog/JobtypeHelpDialog";
import Miibo from "@/components/icons/Miibo";
import ReconnectingIndicator from "@/components/ReconnectingIndicator";
import { IWorkflowCategoryOption, IWorkflowOptionItem, IWorkflowStep } from "@/lib/common";
import { useAppSelector } from "@/lib/store/hooks";

interface Props {
  step: IWorkflowStep;
  answers: number[];
  onNext: (stepAnswers: number[]) => void | Promise<void>;
  onBack: () => void;
  onCancel: () => void;
  isFirstStep: boolean;
  isLastStep: boolean;
  previousStepAnswers?: number[];
  isSearchError: boolean;
}

export default function JobMatchDiagnosisStep({
  step,
  answers,
  onNext,
  onBack,
  onCancel,
  isFirstStep,
  isLastStep,
  previousStepAnswers,
  isSearchError,
}: Props) {
  const [selectedValues, setSelectedValues] = useState<number[]>(() => {
    if (answers.length > 0) {
      return answers;
    }
    if (step.id === 3) {
      // Step3は初期状態で全選択
      const options = step.options as IWorkflowCategoryOption[];
      return options.flatMap((category) => category.items.map((item) => item.value));
    }
    return [];
  });
  const [expandedCategoryIds, setExpandedCategoryIds] = useState<string[]>(() => {
    // Step2、3はすべて展開
    if (step.id === 2 || step.id === 3) {
      return (step.options as IWorkflowCategoryOption[]).map((c) => c.id);
    }
    // Step1で選択がある場合は、選択されているカテゴリを展開
    if (step.id === 1 && answers.length > 0) {
      const options = step.options as IWorkflowCategoryOption[];
      return options
        .filter((category) => category.items.some((item) => answers.includes(item.value)))
        .map((c) => c.id);
    }
    return [];
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [infoDialogOpen, setInfoDialogOpen] = useState(false);
  const [selectedOptionInfo, setSelectedOptionInfo] = useState<IWorkflowOptionItem | null>(null);
  const socketStatus = useAppSelector((state) => state.websocket.socketStatus);
  const isSocketDisconnected = socketStatus < SocketStatus.Connected;

  const handleExpandCategory = (categoryId: string) => {
    if (!expandedCategoryIds.includes(categoryId)) {
      setExpandedCategoryIds((prev) => [...prev, categoryId]);
    }
  };

  const handleToggle = (value: number, categoryId: string) => {
    // Step1で選択したカテゴリを展開
    if (step.id === 1) {
      handleExpandCategory(categoryId);
    }

    // Step2で選択した値がStep1で選択済みの場合は何もしない
    if (step.id === 2 && previousStepAnswers?.includes(value)) {
      return;
    }

    const currentIndex = selectedValues.indexOf(value);
    const newChecked = [...selectedValues];

    if (currentIndex === -1) {
      newChecked.push(value);
    } else {
      newChecked.splice(currentIndex, 1);
    }

    setSelectedValues(newChecked);
  };

  const handleNext = async () => {
    if (isSocketDisconnected || isSubmitting) return;

    setIsSubmitting(true);
    try {
      await Promise.resolve(onNext(selectedValues));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenInfo = (e: React.MouseEvent, option: IWorkflowOptionItem) => {
    e.stopPropagation();
    setSelectedOptionInfo(option);
    setInfoDialogOpen(true);
  };

  const getValidationState = () => {
    switch (step.id) {
      case 1: {
        const minSelection = 3;
        const maxSelection = 5;
        const isUnder = selectedValues.length < minSelection;
        const remainingSelection = minSelection - selectedValues.length;
        const isOver = selectedValues.length > maxSelection;
        return {
          isInvalid: isUnder || isOver,
          errorMessage: isUnder
            ? `あと${remainingSelection}つ選択してください`
            : isOver
              ? `${maxSelection}つまで選択可能です`
              : null,
        };
      }
      case 2: {
        const maxSelection = 5;
        const isOver = selectedValues.length > maxSelection;
        return {
          isInvalid: isOver,
          errorMessage: isOver ? `${maxSelection}つまで選択可能です` : null,
        };
      }
      case 3: {
        const minSelection = 1;
        const isUnder = selectedValues.length < minSelection;
        return {
          isInvalid: isUnder,
          errorMessage: null, // Step3はエラーメッセージを表示しない
        };
      }
      default:
        return { isInvalid: false, errorMessage: null };
    }
  };

  const { isInvalid, errorMessage } = getValidationState();

  const hasNoOptions = (step.options as IWorkflowCategoryOption[]).every(
    (category) => category.items.length === 0
  );

  const renderQuestionContent = () => {
    switch (step.id) {
      case 1:
        return (
          <Box className="question-container wanted">
            <Box className="question-icon">
              <Miibo />
            </Box>
            <Typography variant="h6" className="question-title">
              <span className="title-highlight">やりたい仕事</span>を教えてください
            </Typography>
          </Box>
        );
      case 2:
        return (
          <Box className="question-container unwanted">
            <Box className="question-icon">
              <Miibo />
            </Box>
            <Typography variant="h6" className="question-title">
              <span className="title-highlight">やりたくない仕事</span>を教えてください
            </Typography>
          </Box>
        );
      case 3: {
        if (isSearchError) {
          return (
            <Box className="no-options-container">
              <Box>
                <Box className="no-options-icon">
                  <Miibo />
                </Box>
                <Typography variant="h6" className="no-options-title">
                  職種情報の取得に失敗しました
                </Typography>
                <Typography variant="body2" className="no-options-message">
                  大変お手数ですが、前の画面に戻ってやり直してください。
                </Typography>
              </Box>
            </Box>
          );
        }
        if (hasNoOptions) {
          return (
            <Box className="no-options-container">
              <Box>
                <Box className="no-options-icon">
                  <Miibo />
                </Box>
                <Typography variant="h6" className="no-options-title">
                  あなたの選択に合った<span className="title-highlight">職種がありませんでした</span>
                </Typography>
                <Typography variant="body2" className="no-options-message">
                  大変お手数ですが、前の画面に戻って別の選択をしてください。
                </Typography>
              </Box>
            </Box>
          );
        }

        return (
          <Box className="question-container recommendation">
            <Box className="question-icon">
              <Miibo />
            </Box>
            <Typography variant="h6" className="question-title">
              ありがとうございます！
            </Typography>
            <Typography variant="h6" className="question-title">
              あなたの<span className="title-highlight">選択に合った職種</span>を提案します。
            </Typography>
            <Typography variant="body2" className="question-subtitle">
              ※ 右の？を押すと説明が表示されます
            </Typography>
            <Typography variant="body2" className="question-subtitle">
              自分に合わないと思ったら<span className="subtitle-highlight">チェックを外して</span>ください
            </Typography>
          </Box>
        );
      }
      default:
        return null;
    }
  };

  const renderFooter = () => {
    if (isSocketDisconnected) {
      return <ReconnectingIndicator />;
    }

    if (isSearchError || hasNoOptions) {
      return (
        <Box className="buttons-container">
          <Button
            variant="contained"
            className="action-button back-button"
            onClick={onBack}
            startIcon={<ArrowBackIcon />}
          >
            戻る
          </Button>
          <Button
            variant="contained"
            className="action-button cancel-button main-button"
            onClick={onCancel}
          >
            中断する
          </Button>
        </Box>
      );
    }

    return (
      <>
        {errorMessage && (
          <Box>
            <Typography variant="body2" className="error-message">
              {errorMessage}
            </Typography>
          </Box>
        )}

        <Box className="buttons-container">
          <Button
            variant="contained"
            className={`action-button back-button ${isFirstStep ? "cancel-button" : ""}`}
            onClick={onBack}
            disabled={isSubmitting}
            startIcon={isFirstStep ? null : <ArrowBackIcon />}
          >
            {isFirstStep ? "中断する" : "戻る"}
          </Button>
          <Button
            variant="contained"
            className={`action-button next-button main-button ${isInvalid || isSubmitting ? "disabled" : ""}`}
            onClick={handleNext}
            disabled={isInvalid || isSubmitting}
          >
            {isLastStep ? `${selectedValues.length}件の職種で決定する` : "次へすすむ"}
          </Button>
        </Box>
      </>
    );
  };

  return (
    <Box className="job-match-diagnosis-step">
      {renderQuestionContent()}

      {!isSearchError && !hasNoOptions && (
        <Box className="step-options-container">
          {(step.options as IWorkflowCategoryOption[]).map((category) => {
            return (
              <Box key={category.id} className={`category-section category-${category.id}`}>
                {category.name && (
                  <Box className="category-header">
                    <Typography variant="subtitle1" className="category-title">
                      {category.name}
                    </Typography>
                    {step.id === 1 && !expandedCategoryIds.includes(category.id) && category.items.length > 4 && (
                      <Button
                        variant="contained"
                        className="expand-button"
                        onClick={() => handleExpandCategory(category.id)}
                      >
                        すべて表示
                      </Button>
                    )}
                  </Box>
                )}

                <Box className={`${step.id === 3 ? "jobtype-option-list" : "nature-option-list"}`}>
                  {category.items
                    .filter((_, idx) => expandedCategoryIds.includes(category.id) || idx < 4)
                    .map((option) => {
                      const isSelected = selectedValues.includes(option.value);

                      if (step.id === 3) {
                        return (
                          <Box
                            key={option.value}
                            className={`option-checkbox ${isSelected ? "selected" : ""}`}
                            onClick={() => handleToggle(option.value, category.id)}
                          >
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
                            <Box component="span" className={`option-label ${isSelected ? "selected" : ""}`}>
                              {option.label}
                            </Box>
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
                      }
                      const isDisabled = previousStepAnswers?.includes(option.value);

                      return (
                        <Button
                          key={option.value}
                          disableRipple={!!isDisabled}
                          className={`option-button ${step.id === 2 ? "unwanted" : ""}
                          ${isSelected ? "selected" : ""} ${isDisabled ? "disabled" : ""}`}
                          onClick={() => !isDisabled && handleToggle(option.value, category.id)}
                        >
                          {option.label}
                        </Button>
                      );
                    })
                  }
                </Box>
              </Box>
            );
          })}
        </Box>
      )}

      <Box className="step-footer">
        {renderFooter()}
      </Box>

      <JobtypeHelpDialog
        open={infoDialogOpen}
        target={selectedOptionInfo?.label ?? ""}
        description={selectedOptionInfo?.description}
        onClose={() => setInfoDialogOpen(false)}
      />
    </Box>
  );
}
