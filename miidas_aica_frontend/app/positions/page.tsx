"use client";

import { useCallback, useEffect, useState, Suspense, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Box,
  Typography,
  Fab,
  CircularProgress,
  IconButton,
  Button,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import { POSITION_DETAIL_TABS } from "@/constants/talks/detail";
import PositionRecord from "@/models/records/Position";
import ApplyCompanyRecord from "@/models/records/ApplyCompany";
import BusinessRecord from "@/models/records/Business";
import InterviewRecord from "@/models/records/Interview";
import PositionTop from "@/components/positions/detail/tabs/PositionTop.jsx";
import JobDescription from "@/components/positions/detail/tabs/JobDescription.jsx";
// import InterviewSettings from "@/components/positions/detail/tabs/InterviewSettings.jsx";
import CompanyOverview from "@/components/positions/detail/tabs/CompanyOverview.jsx";
import Image from "@/components/utils/Image";
import styles from "./page.module.scss";
import ModalBadgeDescription from "@/components/app/shared/ModalBadgeDescription";
import ModalHPMCertificationDescription from "@/components/positions/detail/tabs/ModalHPMCertificationDescription";
import ErrorModal from "@/components/app/shared/ErrorModal";
import Chat from "@/components/Chat";
import { sendWebSocketMessage } from "@/lib/socket";
import { useAppDispatch, useAppSelector } from "@/lib/store/hooks";
import {
  setSessionStatus,
  updateScrollEventType,
} from "@/lib/store/features/websocket/websocketSlice";
import {
  Asset,
  ChatRequestType,
  PageName,
  PagePath,
  ScrollEventType,
  SessionStatus,
} from "@/constants/enum";
import {
  addPosition,
  applyPosition,
  applyStart,
  getBusinessData,
  getCompanyData,
  getPositionData,
} from "./apiRequest";
import { LOCALSTORAGE_SOURCE_COMPONENT_KEY } from "@/constants/localStorage";
import {
  addAppliedPosition,
  markSavedProfileRetrieved,
} from "@/lib/store/features/profile/profileSlice";
import { closePositionDetailChatSpeechBubble } from "@/lib/store/features/global_state/globalStateSlice";
import TeacupIcon from "@/components/icons/Teacup";

const APPLY_ERROR_MESSAGE =
  "面談の申し込みに失敗しました、申し訳ありません。\n\nしばらく時間をおいて再度試みてください。";

function PositionDetail() {
  const dispatch = useAppDispatch();
  const router = useRouter();
  const searchParams = useSearchParams();
  const positionId = searchParams.get("positionId");

  // ローディング
  const [isPositionLoading, setIsPositionLoading] = useState(true);
  const [isCompanyLoading, setIsCompanyLoading] = useState(true);
  const [isBusinessLoading, setIsBusinessLoading] = useState(true);

  // エラー
  const [error, setError] = useState<string | null>(null);

  // チャットモーダルダイアログ
  const [isChatOpen, setIsChatOpen] = useState(false);

  // 応募済みかどうか
  const [applied, setApplied] = useState(false);

  // 吹き出し表示状態
  const positionDetailChatSpeechBubbleClosed = useAppSelector(
    (state) => state.globalState.positionDetailChatSpeechBubbleClosed,
  );

  // データ
  const [positionImtRecord, setPositionImtRecord] =
    useState<PositionRecord | null>(null);
  const [companyImtRecord, setCompanyImtRecord] =
    useState<ApplyCompanyRecord | null>(null);
  const [businessImtRecord, setBusinessImtRecord] =
    useState<BusinessRecord | null>(null);
  const [interviewImtRecord, setInterviewImtRecord] = useState<InterviewRecord>(
    new InterviewRecord({}),
  );
  const [isOutsourcingPosition, setIsOutsourcingPosition] = useState(false);
  const [isRegularOutsourcingPosition, setIsRegularOutsourcingPosition] =
    useState(false);
  const [isSpotOutsourcingPosition, setIsSpotOutsourcingPosition] =
    useState(false);
  const [isCommissionOutsourcingPosition, setIsCommissionOutsourcingPosition] =
    useState(false);

  const [isBadgeDescriptionModalDisplay, setIsBadgeDescriptionModalDisplay] =
    useState(false);
  const [
    isHPMCertificationDescriptionModalDisplay,
    setIsHPMCertificationDescriptionModalDisplay,
  ] = useState(false);

  // エラーモーダル
  const [isErrorModalDisplay, setIsErrorModalDisplay] = useState(false);
  const [errorModalMessage, setErrorModalMessage] = useState("");

  const showErrorModal = (message: string) => {
    setErrorModalMessage(message);
    setIsErrorModalDisplay(true);
  };

  const hideErrorModal = () => {
    setIsErrorModalDisplay(false);
    setErrorModalMessage("");
  };

  const previousPage = useAppSelector((state) => state.websocket.currentPage);

  const backToMainChat = useCallback(() => {
    router.push(PagePath.Chat);
  }, [router]);

  useEffect(() => {
    if (!previousPage) {
      router.push(PagePath.Chat);
      return;
    }

    const fetchData = async () => {
      if (!positionId) {
        setError("求人が見つかりませんでした");
        setIsPositionLoading(false);
        setIsCompanyLoading(false);
        setIsBusinessLoading(false);
        return;
      }

      // ポジションデータ取得
      setIsPositionLoading(true);
      getPositionData(positionId).then((positionResult) => {
        localStorage.removeItem(LOCALSTORAGE_SOURCE_COMPONENT_KEY);
        if (positionResult.httpStatus === 429) {
          backToMainChat();
          return;
        } else if (positionResult.error) {
          setError(positionResult.error.message);
        } else if (positionResult.data) {
          const record = new PositionRecord(positionResult.data.Position);
          setPositionImtRecord(record);
          setInterviewImtRecord(record.Interview || new InterviewRecord({}));
          setIsOutsourcingPosition(!record.isTraitEmploymentTypeEmployee());
          setIsRegularOutsourcingPosition(
            record.isTraitEmploymentTypeRegularOutsourcing(),
          );
          setIsSpotOutsourcingPosition(
            record.isTraitEmploymentTypeSpotOutsourcing(),
          );
          setIsCommissionOutsourcingPosition(
            record.isTraitEmploymentTypeCommissionOutsourcing(),
          );

          // 応募済みかどうか
          setApplied(positionResult.data.Applied);
        }
        setIsPositionLoading(false);
      });

      // 会社データ取得
      setIsCompanyLoading(true);
      getCompanyData(positionId).then((companyResult) => {
        if (companyResult.error) {
          setError(companyResult.error.message);
        } else if (companyResult.data) {
          setCompanyImtRecord(new ApplyCompanyRecord(companyResult.data));
        }
        setIsCompanyLoading(false);
      });

      // 業界データ取得
      setIsBusinessLoading(true);
      getBusinessData(positionId).then((businessResult) => {
        if (businessResult.error) {
          setError(businessResult.error.message);
        } else if (businessResult.data) {
          const record = new BusinessRecord(businessResult.data.Business);
          setBusinessImtRecord(record);
        }
        setIsBusinessLoading(false);
      });
    };

    fetchData();
  }, [router, previousPage, positionId, backToMainChat]);

  const isLoading = isPositionLoading || isCompanyLoading || isBusinessLoading;

  const handleChatOpen = () => setIsChatOpen(true);
  const handleChatClose = () => setIsChatOpen(false);
  const handleSpeechBubbleClose = useCallback(() => {
    dispatch(closePositionDetailChatSpeechBubble());
  }, [dispatch]);

  /**
   * 「求人TOP」セクションを返す
   */
  const renderPositionTop = useCallback(() => {
    if (isLoading || error != null) {
      return;
    }

    return (
      <div className={styles.positionTopSection}>
        <PositionTop
          positionImtRecord={positionImtRecord}
          companyImtRecord={companyImtRecord}
          interviewImtRecord={interviewImtRecord}
          isOutsourcingPosition={isOutsourcingPosition}
          isSpotOutsourcingPosition={isSpotOutsourcingPosition}
          isCommissionOutsourcingPosition={isCommissionOutsourcingPosition}
        />
      </div>
    );
  }, [
    isLoading,
    error,
    positionImtRecord,
    companyImtRecord,
    interviewImtRecord,
    isOutsourcingPosition,
    isSpotOutsourcingPosition,
    isCommissionOutsourcingPosition,
  ]);

  /**
   * 「募集要項」セクションを返す
   */
  const renderJobDescription = useCallback(() => {
    if (isLoading || error != null) {
      return;
    }

    return (
      <li
        key={POSITION_DETAIL_TABS.JOB_DESCRIPTION}
        className={styles.sectionItem}
      >
        <JobDescription
          positionImtRecord={positionImtRecord}
          companyImtRecord={companyImtRecord}
          isOutsourcingPosition={isOutsourcingPosition}
          isRegularOutsourcingPosition={isRegularOutsourcingPosition}
          isSpotOutsourcingPosition={isSpotOutsourcingPosition}
          isCommissionOutsourcingPosition={isCommissionOutsourcingPosition}
        />
      </li>
    );
  }, [
    isLoading,
    error,
    positionImtRecord,
    companyImtRecord,
    isOutsourcingPosition,
    isRegularOutsourcingPosition,
    isSpotOutsourcingPosition,
    isCommissionOutsourcingPosition,
  ]);

  /**
   * 「選考方法」セクションを返す
   */
  // const renderInterviewSettings = useCallback(() => {
  //   const isNoInterviewForDisplay =
  //     !interviewImtRecord || interviewImtRecord.isNoInterviewForDisplay();

  //   // 業務委託求人（「ミイダス相性判定」「書類選考」は表示しない）かつ、面接情報が何もない
  //   // または
  //   // 業務委託スポット求人は選考方法の情報が何もないため表示しない
  //   if (
  //     (isOutsourcingPosition && isNoInterviewForDisplay) ||
  //     isSpotOutsourcingPosition
  //   ) {
  //     return null;
  //   }

  //   return (
  //     <li
  //       key={POSITION_DETAIL_TABS.INTERVIEW_SETTINGS}
  //       className={styles.sectionItem}
  //     >
  //       <InterviewSettings
  //         positionDetailImtRecord={positionImtRecord}
  //         interviewImtRecord={interviewImtRecord}
  //       />
  //     </li>
  //   );
  // }, [isLoading, error]);

  /**
   * 「企業情報」セクションを返す
   */
  const renderCompanyOverview = useCallback(() => {
    if (isLoading || error != null) {
      return;
    }

    return (
      <li
        key={POSITION_DETAIL_TABS.COMPANY_OVERVIEW}
        className={styles.sectionItem}
      >
        <CompanyOverview
          businessImtRecord={businessImtRecord}
          positionImtRecord={positionImtRecord}
          companyImtRecord={companyImtRecord}
          showModalBadgeDescription={() =>
            setIsBadgeDescriptionModalDisplay(true)
          }
          showModalHPMCertificationDescription={() =>
            setIsHPMCertificationDescriptionModalDisplay(true)
          }
          isOutsourcingPosition={isOutsourcingPosition}
        />
      </li>
    );
  }, [
    isLoading,
    error,
    businessImtRecord,
    positionImtRecord,
    companyImtRecord,
    isOutsourcingPosition,
  ]);

  /**
   * 「業界研究」セクションを返す
   * TODO: 日経データが必要なので、非表示
   */
  // const renderIndustryResearch = useCallback(() => {
  //   if (!this.props.isDisplayNikkeiReport) {
  //     return null;
  //   }

  //   const companyName = this.props.offerDetailCompanyImtRecord.get('Name');

  //   return (
  //     <li
  //       key={POSITION_DETAIL_TABS.INDUSTRY_RESEARCH}
  //       ref={this.industryResearchSectionRef}
  //       className={styles.sectionItem}
  //     >
  //       <IndustryResearchTab
  //         nikkeiListImtList={this.props.nikkeiListImtList}
  //         positionId={this.props.positionId}
  //         companyName={companyName}
  //       />
  //     </li>
  //   );
  // }, [isLoading, error]);

  /**
   * 求人詳細内容を返す
   */
  const renderContent = useCallback(() => {
    if (isLoading || error != null) {
      return;
    }

    const jobDescriptionSection = renderJobDescription();
    // const interviewSettings = renderInterviewSettings();
    const companyOverview = renderCompanyOverview();
    // const industryResearch = renderIndustryResearch();

    return (
      <div className="js-VisibleMeasureRoot">
        <ul className={styles.content}>
          {jobDescriptionSection}
          {/* {interviewSettings} */}
          {companyOverview}
          {/* {industryResearch} */}
        </ul>
      </div>
    );
  }, [isLoading, error, renderJobDescription, renderCompanyOverview]);

  const sessionStatus = useAppSelector(
    (state) => state.websocket.sessionStatus,
  );
  const appliedPositions = useAppSelector(
    (state) => state.profile.appliedPositions,
  );

  const close = useCallback(() => {
    // ポジションチャットサマリ作成リクエスト
    // TODO: チャットした場合のみ実施すべき
    sendWebSocketMessage(
      dispatch,
      ChatRequestType.SummarizePosition,
      PageName.PositionDetail,
      PageName.Chat,
      null,
      positionId,
    );

    backToMainChat();
  }, [dispatch, backToMainChat, positionId]);

  const apply = useCallback(async () => {
    if (sessionStatus === SessionStatus.Chatting) {
      // 会話中
      // 初めて応募の場合
      const result = await applyStart(positionId!);
      if (result.data?.session_status == SessionStatus.Applying) {
        // セッションステータス変更
        dispatch(setSessionStatus(SessionStatus.Applying));
        // 応募ポジション追加
        dispatch(addAppliedPosition(positionId!));
        // いま保存されたプロフィールがないはずので、サーバーから取得する必要がない
        dispatch(markSavedProfileRetrieved());
        // メインチャットへ戻る
        close();
        // このときに、メインチャット画面の底部にスクロールすべき
        dispatch(
          updateScrollEventType(ScrollEventType.JobSearchFilterRetrieving),
        );
      } else {
        showErrorModal(APPLY_ERROR_MESSAGE);
      }
    } else if (
      sessionStatus === SessionStatus.Applying ||
      sessionStatus === SessionStatus.Registering
    ) {
      // 面談応募・登録中
      // 応募ポジション追加
      const result = await addPosition(positionId!);
      if (result.data?.session_status === SessionStatus.Applying) {
        dispatch(addAppliedPosition(positionId!));
      } else {
        showErrorModal(APPLY_ERROR_MESSAGE);
      }
    } else {
      // 面談応募・登録済み
      const result = await applyPosition(positionId!);
      if (result.httpStatus === 200) {
        if (result.data?.PositionID) {
          window.location.href = `/positions/${result.data.PositionID}/meeting_complete`;
        } else {
          showErrorModal(APPLY_ERROR_MESSAGE);
        }
      } else {
        showErrorModal(APPLY_ERROR_MESSAGE);
      }
    }
  }, [dispatch, close, positionId, sessionStatus]);

  const applyButton = useMemo(() => {
    if (isLoading || error) {
      // 画面ロード中かエラーの場合、ボタン表示しない
      return null;
    }

    if (
      sessionStatus === SessionStatus.Registering ||
      sessionStatus === SessionStatus.Applying
    ) {
      if (appliedPositions.includes(positionId!) || applied) {
        // 会員登録／面談応募中、かつ、応募ポジションに追加済の場合、ボタン表示しない
        return null;
      }
    }

    return (
      <Box className={styles.applyButtonArea}>
        <Button
          variant="contained"
          fullWidth
          onClick={apply}
          disabled={appliedPositions.includes(positionId!) || applied}
          className={styles.applyButton}
        >
          <TeacupIcon className={styles["teacup-icon"]} />
          {applied ? "応募済み" : "会員登録後カジュアルに話を聞く"}
        </Button>
      </Box>
    );
  }, [
    isLoading,
    error,
    sessionStatus,
    applied,
    appliedPositions,
    apply,
    positionId,
  ]);

  return (
    <>
      <Box className={styles.positionHeader}>
        <IconButton
          onClick={() => {
            close();
            dispatch(
              updateScrollEventType(ScrollEventType.BackFromPositionDetail),
            );
          }}
          className={styles.closeButton}
          aria-label="close"
        >
          <ChevronLeftIcon />
        </IconButton>
        <Typography variant="h6" align="center" noWrap aria-busy={isLoading}>
          {!isLoading && companyImtRecord
            ? companyImtRecord.get("Name")
            : "求人詳細"}
          {isLoading && (
            <span
              style={{ position: "absolute", left: "-9999px" }}
              aria-live="polite"
            >
              読み込み中...
            </span>
          )}
        </Typography>
      </Box>
      <Box className={styles.positionDetail}>
        {/* ポジション詳細取得中 */}
        {isLoading && (
          <Box className={styles.loading}>
            <CircularProgress size={60} />
          </Box>
        )}

        {error && (
          <Box className={styles.error}>
            <Typography color="error">{error}</Typography>
          </Box>
        )}

        {renderPositionTop()}
        {renderContent()}

        {!isLoading && !error && (
          <>
            <Box className={styles.chatButtonArea}>
              {/* 左下のチャットボタン */}
              <Fab
                aria-label="chat"
                onClick={handleChatOpen}
                className={styles.chatButton}
              >
                <Image src={Asset.MIIBO} alt="MIIBO Assistant" />
              </Fab>
              {/* 吹き出し */}
              {!positionDetailChatSpeechBubbleClosed && (
                <Box className={styles.speechBubble}>
                  <IconButton
                    aria-label="close speech bubble"
                    onClick={handleSpeechBubbleClose}
                    size="small"
                    className={styles.closeButton}
                  >
                    <CloseIcon fontSize="small" />
                  </IconButton>
                  この求人について質問があれば、私のアイコンを押してください。
                  <br />
                  <br />
                  仕事内容や職場環境などもっと詳しく知りたいときは、画面一番下の「話を聞いてみたい」ボタンを押してみてください。電話やビデオ通話で企業の担当者と話せるかもしれません！
                </Box>
              )}
            </Box>

            {/* チャットモーダル */}
            {isChatOpen && (
              <div
                className={styles.chatModalBackdrop}
                onClick={handleChatClose}
              >
                <div
                  className={styles.chatModal}
                  onClick={(e) => e.stopPropagation()}
                >
                  <IconButton
                    aria-label="close chat"
                    onClick={handleChatClose}
                    className={styles.chatModalClose}
                    size="small"
                  >
                    <CloseIcon fontSize="small" />
                  </IconButton>
                  <Chat
                    currentPage={PageName.PositionDetail}
                    positionID={positionId}
                  />
                </div>
              </div>
            )}
          </>
        )}
      </Box>

      {/* 応募ボタン */}
      {applyButton}

      <ModalBadgeDescription
        isDisplay={isBadgeDescriptionModalDisplay}
        hideModal={() => setIsBadgeDescriptionModalDisplay(false)}
      />
      <ModalHPMCertificationDescription
        isDisplay={isHPMCertificationDescriptionModalDisplay}
        hideModal={() => setIsHPMCertificationDescriptionModalDisplay(false)}
      />
      <ErrorModal
        isDisplay={isErrorModalDisplay}
        hideModal={hideErrorModal}
        message={errorModalMessage}
      />
    </>
  );
}

export default function PositionDetailPage() {
  return (
    <Suspense fallback={<CircularProgress />}>
      <PositionDetail />
    </Suspense>
  );
}
