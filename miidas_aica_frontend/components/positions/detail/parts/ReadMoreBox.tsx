import {
  useRef,
  useEffect,
  type MFC,
  type ReactNode,
  type RefObject,
} from "react";

import { READ_MORE_BUTTON_CLS } from "@/constants/app";
import { clsx } from "@/utils/className";

import styles from "./ReadMoreBox.module.scss";

const READ_MORE_BUTTON_AREA_HEIGHT = 64; // ボタン高44px + 省略要素の下端から20px

type Props = {
  children: ReactNode;
  readMoreBoxRef?: RefObject<HTMLDivElement | null>;
  needReadMoreButton?: boolean;
  isExpanded: boolean;
  setIsExpanded: (isExpanded: boolean) => void;
  omittedHeight?: number;
  overLayClassName?: string;
  toggleBtnClassName?: string;
  /** Google Analytics用CSSクラス名 */
  gaClassName?: string;
};

/**
 * 省略表示と「続きを読む」ボタンの組み合わせ
 */
const ReadMoreBox: MFC<Props> = ({
  children,
  readMoreBoxRef = null,
  needReadMoreButton = true,
  isExpanded,
  setIsExpanded,
  omittedHeight = null,
  overLayClassName = "",
  toggleBtnClassName = "",
  gaClassName = "",
}) => {
  const wrapperRef = useRef<HTMLDivElement>(null);
  const localReadMoreBoxRef = useRef<HTMLDivElement>(null);
  const containerRef = readMoreBoxRef || localReadMoreBoxRef;
  const prevIsExpandedRef = useRef(isExpanded);

  useEffect(() => {
    if (containerRef.current) {
      // 省略時の高さ指定がある場合、省略時はその値を使用する
      const childrenHeight =
        omittedHeight && needReadMoreButton && !isExpanded
          ? omittedHeight
          : containerRef.current.scrollHeight;
      // アニメーションを有効にするために指定
      containerRef.current.style.maxHeight = `${childrenHeight + READ_MORE_BUTTON_AREA_HEIGHT}px`;

      // 閉じた場合
      if (prevIsExpandedRef.current && !isExpanded) {
        // overflow: hiddenに戻す
        containerRef.current.style.overflow = "hidden";
        // 続きを読む全体のTOPまでスクロールする
        // NOTE: containerRefは省略表現のためにoverflow: hiddenが必要なので、scroll-margin-topが効かない。
        //       回避策として、セクション全体を囲ったwrapperRefにscroll-margin-topをあてて、fixed・sticky要素を考慮。
        wrapperRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "nearest",
        });
      }
    }

    prevIsExpandedRef.current = isExpanded;
  }, [isExpanded, needReadMoreButton, omittedHeight, containerRef]);

  /**
   * 続きを読むボタンのトグル処理
   */
  const handleReadMoreToggle = () => {
    setIsExpanded(!isExpanded);
  };

  /**
   * 開閉アニメーション完了時の処理
   */
  const handleReadMoreBoxTransitionEnd = () => {
    // 展開した場合
    if (isExpanded && containerRef.current) {
      // 展開状態でchildrenの高さが増えた際、maxHeight指定が残っていると超えた部分が表示できないため外しておく
      // NOTE #68332: 企業側ポジションプレビューでの印刷時は、CSSで @media print { max-height: unset !important } を指定してこの処理を再現している
      containerRef.current.style.maxHeight = "";
      // children以下に別のreadMore要素がある場合、overflow: hiddenが影響を及ぼすため、展開完了時にはoverflow: visibleにする
      containerRef.current.style.overflow = "visible";
    }
  };

  const readMoreButton = renderReadMoreButton(
    needReadMoreButton,
    isExpanded,
    handleReadMoreToggle,
    overLayClassName,
    toggleBtnClassName,
    gaClassName,
  );

  const containerCls = clsx(
    styles.container,
    needReadMoreButton && styles.withReadMoreButton,
    isExpanded && styles.expanded,
  );

  return (
    <div className={styles.wrapper} ref={wrapperRef}>
      <div
        className={containerCls}
        ref={containerRef}
        onTransitionEnd={handleReadMoreBoxTransitionEnd}
      >
        {children}
        {readMoreButton}
      </div>
    </div>
  );
};

export default ReadMoreBox;

/**
 * トグルボタンを描画する
 */
function renderReadMoreButton(
  needReadMoreButton: boolean,
  isExpanded: boolean,
  handleReadMoreToggle: () => void,
  overLayClassName: string,
  toggleBtnClassName: string,
  gaClassName: string,
) {
  // 省略不必要の場合はボタンを表示しない
  if (!needReadMoreButton) return null;

  if (isExpanded) {
    return (
      <button
        type="button"
        className={clsx(styles.toggleBtn, styles.hide, toggleBtnClassName)}
        onClick={handleReadMoreToggle}
      >
        閉じる
      </button>
    );
  }

  const btnCls = clsx(
    styles.toggleBtn,
    READ_MORE_BUTTON_CLS,
    toggleBtnClassName,
    gaClassName ? `${gaClassName}-readMore` : "",
  );

  return (
    <>
      <div className={clsx(styles.overlay, overLayClassName)} />
      <button type="button" className={btnCls} onClick={handleReadMoreToggle}>
        続きを読む
      </button>
    </>
  );
}
