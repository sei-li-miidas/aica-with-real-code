import React, {
  RefObject,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type HTMLAttributes,
  type ReactNode,
} from "react";
import { CircularProgress, Button } from "@mui/material";

import { clsx } from "@/utils/className";

import "./PullToRefresh.scss";

const INDICATOR_HEIGHT = 60;
const DEFAULT_THRESHOLD = 60;
const DEFAULT_MAX_PULL = 120;
/**
 * プル距離でpull-to-refreshの感度を制御します。
 * この値を調整することで、プルをより敏感にしたり鈍感にしたりできます。
 */
const DAMPING_FACTOR = 0.5;

type DivProps = Omit<
  HTMLAttributes<HTMLDivElement>,
  "onTouchStart" | "onTouchMove" | "onTouchEnd" | "onTouchCancel"
>;

type PullToRefreshProps = DivProps & {
  /** 表示する子要素 */
  children: ReactNode;
  /** リフレッシュ時の実行処理 */
  onRefresh: () => void | Promise<void>;
  /** 親からの読み込み状態 */
  isLoading: boolean;
  /** pull スワイプを無効化するかどうか */
  disabled?: boolean;
  /** コンテンツラッパーへ追加するクラス名 */
  contentClassName?: string;
  /** コンテンツラッパーへ適用する追加スタイル */
  contentStyle?: CSSProperties;
  /** pull 開始時に表示するテキスト */
  refreshText?: string;
  /** 閾値を超えた時に表示するテキスト */
  releaseText?: string;
  /** 読み込み中に表示するテキスト */
  loadingText?: string;
  /** ルート要素に付与するクラス名 */
  className?: string;
  /** リフレッシュ発火までに必要な距離(px) */
  threshold?: number;
  /** 引っ張り距離の上限(px) */
  maxPullDistance?: number;
  /** スクロールコンテナへの外部参照 */
  containerRef?: RefObject<HTMLDivElement | null>;
};

// pull-to-refreshコンポーネント。
// touchstartで開始位置を保持し、touchmove中に距離を計算してインジケーターと子要素の
// translateYを制御し、閾値を超えたらonRefreshを呼び出す。
const PullToRefresh: React.FC<PullToRefreshProps> = ({
  children,
  onRefresh,
  isLoading,
  disabled = false,
  contentClassName,
  contentStyle,
  refreshText = "Pull to refresh",
  releaseText = "Release to refresh",
  loadingText = "Refreshing...",
  className,
  threshold = DEFAULT_THRESHOLD,
  maxPullDistance = DEFAULT_MAX_PULL,
  containerRef: containerRefProp,
  ...rest
}) => {
  // 内部でスクロールコンテナを持つが、親からの参照がある場合はそれを優先
  const fallbackContainerRef = useRef<HTMLDivElement>(null);
  const effectiveContainerRef: RefObject<HTMLDivElement | null> =
    containerRefProp ?? fallbackContainerRef;
  const startYRef = useRef<number | null>(null);
  const isLoadingRef = useRef(isLoading);
  const autoTriggerRef = useRef(false);

  const [pullDistance, setPullDistance] = useState(0);
  const [isPulling, setIsPulling] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isReadyToRefresh, setIsReadyToRefresh] = useState(false);

  /** 親からの読み込み状態監視 */
  useEffect(() => {
    isLoadingRef.current = isLoading;

    if (!isLoading) {
      setIsRefreshing(false);
      autoTriggerRef.current = false;
    }
  }, [isLoading]);

  /** disabled になったら pull 状態をクリア */
  useEffect(() => {
    if (disabled) {
      startYRef.current = null;
      setIsPulling(false);
      setIsRefreshing(false);
      setIsReadyToRefresh(false);
      setPullDistance(0);
      autoTriggerRef.current = false;
    }
  }, [disabled]);

  /** pull 操作中の状態を初期化 */
  const resetPullState = useCallback(() => {
    startYRef.current = null;
    setIsPulling(false);
    setIsReadyToRefresh(false);
    setPullDistance(0);
  }, []);

  /** 閾値を満たした際にリフレッシュ処理を実行 */
  const triggerRefresh = useCallback(async () => {
    if (disabled || isLoading || isRefreshing) return;

    setIsRefreshing(true);

    try {
      await onRefresh();
    } finally {
      if (!isLoadingRef.current) {
        setIsRefreshing(false);
      }
    }
  }, [disabled, isLoading, isRefreshing, onRefresh]);

  const [isTouchMode, setIsTouchMode] = useState(() => {
    if (typeof window === "undefined") return false;
    return (
      window.matchMedia("(pointer: coarse)").matches ||
      "ontouchstart" in window ||
      (typeof navigator !== "undefined" && navigator.maxTouchPoints > 0)
    );
  });

  const beginPull = useCallback(
    (startClientY: number) => {
      if (disabled || isLoading || isRefreshing) return false;
      const container = effectiveContainerRef.current;
      if (!container || container.scrollTop > 0) return false;
      startYRef.current = startClientY;
      setIsPulling(false);
      setIsReadyToRefresh(false);
      setIsTouchMode(true);
      return true;
    },
    [effectiveContainerRef, disabled, isLoading, isRefreshing],
  );

  const updatePullDistance = useCallback(
    (currentClientY: number) => {
      if (!isPulling || disabled || isLoading || isRefreshing) return;
      if (startYRef.current === null) return;
      const container = effectiveContainerRef.current;
      if (!container) return;
      const distance = currentClientY - startYRef.current;
      if (container.scrollTop > 0 || distance <= 0) {
        setPullDistance(0);
        setIsReadyToRefresh(false);
        return;
      }
      const adjustedDistance = Math.min(
        distance * DAMPING_FACTOR,
        maxPullDistance,
      );
      setPullDistance(adjustedDistance);
      setIsReadyToRefresh(adjustedDistance >= threshold);
    },
    [
      isPulling,
      disabled,
      isLoading,
      isRefreshing,
      effectiveContainerRef,
      maxPullDistance,
      threshold,
    ],
  );

  const finishPull = useCallback(
    (shouldRefresh: boolean) => {
      if (shouldRefresh && !disabled && !isLoading) {
        triggerRefresh();
      }
      resetPullState();
    },
    [disabled, isLoading, resetPullState, triggerRefresh],
  );

  const handleScroll = useCallback(() => {
    const container = effectiveContainerRef.current;
    if (!container) return;
    if (
      container.scrollTop <= 0 &&
      !autoTriggerRef.current &&
      !disabled &&
      !isLoading &&
      !isRefreshing
    ) {
      autoTriggerRef.current = true;
      triggerRefresh();
    }
  }, [
    effectiveContainerRef,
    disabled,
    isLoading,
    isRefreshing,
    triggerRefresh,
  ]);

  /** タッチ開始位置を記録し、先頭までスクロールされている時のみ pull を許可 */
  const handleTouchStart = useCallback(
    (event: TouchEvent) => {
      if (event.touches.length !== 1) return;
      beginPull(event.touches[0].clientY);
    },
    [beginPull],
  );

  /** タッチ移動距離から pull 量を算出し、必要に応じてデフォルトスクロールを抑制 */
  const handleTouchMove = useCallback(
    (event: TouchEvent) => {
      if (event.touches.length !== 1) return;
      const container = effectiveContainerRef.current;
      if (!container) return;
      const distance =
        event.touches[0].clientY -
        (startYRef.current ?? event.touches[0].clientY);
      if (distance <= 0 || container.scrollTop > 0) {
        resetPullState();
        return;
      }

      if (!isPulling) {
        setIsPulling(true);
      }

      updatePullDistance(event.touches[0].clientY);
      event.preventDefault();
    },
    [effectiveContainerRef, isPulling, updatePullDistance, resetPullState],
  );

  /** 指を離したタイミングで閾値を超えていればリフレッシュ */
  const handleTouchEnd = useCallback(() => {
    if (!isPulling) return;
    finishPull(isReadyToRefresh);
  }, [finishPull, isPulling, isReadyToRefresh]);

  /** タッチがキャンセルされた場合は pull 状態を破棄 */
  const handleTouchCancel = useCallback(() => {
    if (!isPulling) return;
    resetPullState();
  }, [isPulling, resetPullState]);

  /** タッチ／スクロールイベントリスナーを登録／解除 */
  useEffect(() => {
    const container = effectiveContainerRef.current;
    if (!container) return;

    const handleTouchStartWithDetect = (event: TouchEvent) => {
      setIsTouchMode(true);
      handleTouchStart(event);
    };

    container.addEventListener("touchstart", handleTouchStartWithDetect, {
      passive: true,
    });
    container.addEventListener("touchmove", handleTouchMove, {
      passive: false,
    });
    container.addEventListener("touchend", handleTouchEnd, { passive: true });
    container.addEventListener("touchcancel", handleTouchCancel, {
      passive: true,
    });
    if (!isTouchMode) {
      container.addEventListener("scroll", handleScroll, { passive: true });
    }

    return () => {
      container.removeEventListener("touchstart", handleTouchStartWithDetect);
      container.removeEventListener("touchmove", handleTouchMove);
      container.removeEventListener("touchend", handleTouchEnd);
      container.removeEventListener("touchcancel", handleTouchCancel);
      if (!isTouchMode) {
        container.removeEventListener("scroll", handleScroll);
      }
    };
  }, [
    isTouchMode,
    handleScroll,
    handleTouchCancel,
    handleTouchEnd,
    handleTouchMove,
    handleTouchStart,
    effectiveContainerRef,
  ]);

  /** indicatorの表示位置を算出 */
  const indicatorTranslate = useMemo(() => {
    if (isRefreshing || isLoading) return 0;
    return Math.min(pullDistance, INDICATOR_HEIGHT) - INDICATOR_HEIGHT;
  }, [isLoading, isRefreshing, pullDistance]);

  /** コンテンツ全体のoffset量を算出 */
  const contentTranslate = useMemo(() => {
    if (isRefreshing || isLoading) return INDICATOR_HEIGHT;
    return Math.max(pullDistance, 0);
  }, [isLoading, isRefreshing, pullDistance]);

  const shouldAnimate = !isPulling;

  const indicatorText = useMemo(() => {
    if (isRefreshing || isLoading) return loadingText;
    if (isReadyToRefresh) return releaseText;
    return refreshText;
  }, [
    isLoading,
    isReadyToRefresh,
    isRefreshing,
    loadingText,
    refreshText,
    releaseText,
  ]);

  const showSpinner = isRefreshing || isLoading;

  const showManualButton = !isTouchMode && !showSpinner && !disabled;

  return (
    <div
      ref={effectiveContainerRef}
      className={clsx("pull-to-refresh-container", className)}
      {...rest}
    >
      {showManualButton && (
        <Button
          variant="text"
          size="small"
          className="pull-refresh-manual-button"
          disabled={isLoading || isRefreshing || disabled}
          onClick={() => {
            if (!isLoading && !isRefreshing && !disabled) {
              autoTriggerRef.current = true;
              triggerRefresh();
            }
          }}
        >
          過去のメッセージを読み込み
        </Button>
      )}
      <div
        className="pull-refresh-indicator"
        style={{
          transform: `translateY(${indicatorTranslate}px)`,
          transition: shouldAnimate ? "transform 0.2s ease-out" : "none",
        }}
      >
        {showSpinner && (
          <CircularProgress size={20} className="pull-refresh-spinner" />
        )}
        <span className="pull-refresh-text">{indicatorText}</span>
      </div>
      <div
        className={contentClassName}
        style={{
          transform: `translateY(${contentTranslate}px)`,
          transition: shouldAnimate ? "transform 0.2s ease-out" : "none",
          ...contentStyle,
        }}
      >
        {children}
      </div>
    </div>
  );
};

export default PullToRefresh;
