"use client";

import "./PositionChangeAnalyzeStep.scss";
import React, { useState } from "react";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { SocketStatus, WorkflowStepSelectionType } from "@/constants/enum";
import Miibo from "@/components/icons/Miibo";
import ReconnectingIndicator from "@/components/ReconnectingIndicator";
import { IWorkflowOptionItem, IWorkflowStep } from "@/lib/common";
import { useAppSelector } from "@/lib/store/hooks";
import SearchLineIcon from "@/components/icons/SearchLine";
import LightbulbLineLuminousIcon from "@/components/icons/LightbulbLineLuminous";
import UserFollowLineIcon from "@/components/icons/UserFollowLine";
import PencilLineIcon from "@/components/icons/PencilLine";

type StepAnswer = { value: number; text?: string };

interface Props {
  step: IWorkflowStep;
  answers: StepAnswer[];
  onNext: (answers: StepAnswer[]) => void | Promise<void>;
  onBack: () => void;
  onCancel: () => void;
  isFirstStep: boolean;
  isLastStep: boolean;
  summary: { summary: string; explanation: string; keywords: string[] } | null;
  isSummaryError: boolean;
}

const ACTION_ICONS: Record<number, React.ReactNode> = {
  1: <SearchLineIcon />,
  2: <LightbulbLineLuminousIcon />,
  3: <UserFollowLineIcon />,
  4: <PencilLineIcon />,
};

export default function PositionChangeAnalyzeStep({
  step,
  answers,
  onNext,
  onBack,
  onCancel,
  isFirstStep,
  isLastStep,
  summary,
  isSummaryError,
}: Props) {
  const [selectedAnswers, setSelectedAnswers] = useState<StepAnswer[]>(answers);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const socketStatus = useAppSelector((state) => state.websocket.socketStatus);
  const isSocketDisconnected = socketStatus < SocketStatus.Connected;

  // position_change_analyze ワークフローのステップは常にフラット形式（IWorkflowOptionItem[]）で提供される
  const flatOptions = step.options as IWorkflowOptionItem[];
  const isMultiple = step.selectionType === WorkflowStepSelectionType.Multiple;
  const selectedValues = selectedAnswers.map((a) => a.value);

  const handleToggle = (value: number) => {
    if (isMultiple) {
      if (selectedValues.includes(value)) {
        setSelectedAnswers((prev) => prev.filter((a) => a.value !== value));
      } else {
        setSelectedAnswers((prev) => [...prev, { value }]);
      }
    } else {
      setSelectedAnswers([{ value }]);
    }
  };

  const handleTextChange = (value: number, text: string) => {
    setSelectedAnswers((prev) =>
      prev.map((a) => (a.value === value ? { ...a, text: text.slice(0, 1000) } : a))
    );
  };

  const getRank = (value: number): number => {
    return selectedValues.indexOf(value) + 1;
  };

  const isSubmitDisabled = (() => {
    if (isSocketDisconnected || isSubmitting) return true;
    if (selectedAnswers.length === 0) return true;

    for (const ans of selectedAnswers) {
      const option = flatOptions.find((o) => o.value === ans.value);
      if (option?.allowFreeText && (!ans.text || ans.text.trim() === "")) {
        return true;
      }
    }
    return false;
  })();

  const handleNext = async () => {
    if (isSocketDisconnected || isSubmitting) return;
    setIsSubmitting(true);
    try {
      await Promise.resolve(onNext(selectedAnswers));
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderQuestionContent = () => {
    switch (step.id) {
      case 1:
        return (
          <Box className="question-container step-trigger">
            <Box className="question-icon"><Miibo /></Box>
            <Typography variant="h6" className="question-title">
              <span className="title-highlight">転職を考えたきっかけ</span>を教えてください
            </Typography>
            <Typography variant="body2" className="question-subtitle">
              ※ <span className="subtitle-highlight">優先度の高いもの</span>から順に選択してください
            </Typography>
          </Box>
        );
      case 2:
        return (
          <Box className="question-container step-fulfillment">
            <Box className="question-icon"><Miibo /></Box>
            <Typography variant="h6" className="question-title">
              今の仕事の中で<span className="title-highlight">やりがいや充実感</span>を感じる瞬間を教えてください
            </Typography>
            <Typography variant="body2" className="question-subtitle">
              ※ <span className="subtitle-highlight">優先度の高いもの</span>から順に選択してください
            </Typography>
          </Box>
        );
      case 3:
        return (
          <Box className="question-container step-career">
            <Box className="question-icon"><Miibo /></Box>
            <Typography variant="h6" className="question-title">
              今後のキャリアで<span className="title-highlight">重要視すること</span>を教えてください
            </Typography>
            <Typography variant="body2" className="question-subtitle">
              ※ <span className="subtitle-highlight">優先度の高いもの</span>から順に選択してください
            </Typography>
          </Box>
        );
      case 4:
        return (
          <Box className="question-container step-score">
            <Box className="question-icon"><Miibo /></Box>
            <Typography variant="h6" className="question-title">
              現在の環境の<span className="title-highlight">満足度</span>はどのくらいですか？
            </Typography>
          </Box>
        );
      case 5:
        if (isSummaryError) {
          return (
            <Box className="no-options-container">
              <Box>
                <Box className="no-options-icon"><Miibo /></Box>
                <Typography variant="h6" className="no-options-title">
                  転職軸の生成に失敗しました
                </Typography>
                <Typography variant="body2" className="no-options-message">
                  大変お手数ですが、前の画面に戻ってやり直してください。
                </Typography>
              </Box>
            </Box>
          );
        }
        return (
          <Box className="question-container step-next-action">
            <Box className="question-icon"><Miibo /></Box>
            <Typography variant="h6" className="question-title">
              ありがとうございます！
            </Typography>
            <Typography variant="h6" className="question-title">
              これまでの内容を整理して<span className="title-highlight">転職軸</span>をまとめました
            </Typography>
          </Box>
        );
      default:
        return null;
    }
  };

  const renderMultipleOptions = () => (
    <Box className="rank-option-list">
      {flatOptions.map((option) => {
        const rank = getRank(option.value);
        const isSelected = rank > 0;
        return (
          <Button
            key={option.value}
            className={`rank-option-row ${isSelected ? "selected" : ""}`}
            onClick={() => handleToggle(option.value)}
          >
            <Box className={`rank-badge ${rank > 0 ? "ranked" : ""}`}>
              {rank > 0 ? rank : ""}
            </Box>
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
                  value={selectedAnswers.find((a) => a.value === option.value)?.text || ""}
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
          </Button>
        );
      })}
    </Box>
  );

  const renderScoreOptions = () => (
    <Box className="card-option-list">
      {flatOptions.map((option) => {
        const isSelected = selectedValues.includes(option.value);
        return (
          <Button
            key={option.value}
            className={`card-option-row score-option score-value-${option.value} ${isSelected ? "selected" : ""}`}
            onClick={() => handleToggle(option.value)}
          >
            <Box component="span" className={`option-label ${isSelected ? "selected" : ""}`}>
              {option.label}
            </Box>
          </Button>
        );
      })}
    </Box>
  );

  const renderActionOptions = () => (
    <Box className="card-option-list">
      {flatOptions.map((option) => {
        const isSelected = selectedValues.includes(option.value);
        return (
          <Button
            key={option.value}
            className={`card-option-row ${isSelected ? "selected" : ""}`}
            onClick={() => handleToggle(option.value)}
          >
            <Box className="card-option-icon">
              {ACTION_ICONS[option.value] ?? <PencilLineIcon />}
            </Box>
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
                  value={selectedAnswers.find((a) => a.value === option.value)?.text || ""}
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
          </Button>
        );
      })}
    </Box>
  );

  const renderOptions = () => {
    if (isMultiple) return renderMultipleOptions();
    if (step.id === 4) return renderScoreOptions();
    return renderActionOptions();
  };

  const renderFooter = () => {
    if (isSocketDisconnected) {
      return <ReconnectingIndicator />;
    }

    if (step.id === 5 && isSummaryError) {
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
      <Box className="buttons-container">
        <Button
          variant="contained"
          className={`action-button back-button ${isFirstStep ? "cancel-button" : ""}`}
          onClick={isFirstStep ? onCancel : onBack}
          disabled={isSubmitting}
          startIcon={isFirstStep ? null : <ArrowBackIcon />}
        >
          {isFirstStep ? "中断する" : "戻る"}
        </Button>
        <Button
          variant="contained"
          className={`action-button next-button main-button ${isSubmitDisabled ? "disabled" : ""}`}
          onClick={handleNext}
          disabled={isSubmitDisabled}
        >
          {isLastStep ? "決定する" : "次へすすむ"}
        </Button>
      </Box>
    );
  };

  return (
    <Box className="position-change-analyze-step">
      {renderQuestionContent()}

      {!(step.id === 5 && isSummaryError) && (
        <Box className="step-options-container">
          {step.id === 5 && summary && (
            <>
              <Box className="summary-container">
                <Box className="summary-content">
                  <Typography variant="h6" className="summary-title">あなたの転職軸</Typography>
                  <Typography className="summary-text summary-text-primary">{summary.summary}</Typography>
                </Box>
                <Box className="summary-content">
                  <Typography variant="h6" className="summary-title">解説</Typography>
                  <Typography className="summary-text">{summary.explanation}</Typography>
                </Box>
                {summary.keywords.length > 0 && (
                  <Box className="summary-content">
                    <Typography variant="h6" className="summary-title">求人を探すポイント</Typography>
                    <Typography className="summary-text">
                      この転職軸に合った求人を探すには、
                      {summary.keywords.map((kw, i) => (
                        <React.Fragment key={i}>
                          <strong>「{kw}」</strong>
                          {i < summary.keywords.length - 1 ? "、" : ""}
                        </React.Fragment>
                      ))}
                      などのキーワードが参考になりそうです。
                    </Typography>
                  </Box>
                )}
              </Box>
              <Box className="next-action-container">
                <Typography variant="h6" className="next-action-title">
                  この転職軸を踏まえて、次はどのように進めていきましょうか？
                </Typography>
              </Box>
            </>
          )}
          {renderOptions()}
        </Box>
      )}

      <Box className="step-footer">
        {renderFooter()}
      </Box>
    </Box>
  );
}
