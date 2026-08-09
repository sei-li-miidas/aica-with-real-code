import { useRef, useEffect, useState, type MFC, type ReactNode } from "react";

import ReadMoreBox from "@/components/positions/detail/parts/ReadMoreBox";
import { useWindowWidth } from "@/hooks/useWindowWidth";

type Props = {
  children: ReactNode;
  omittedHeight: number;
  overLayClassName?: string;
  toggleBtnClassName?: string;
  /** Google Analytics用CSSクラス名 */
  gaClassName?: string;
};

/**
 * 子ノードの表示を省略し「続きを読む」ボタンを表示
 */
const ReadMoreSection: MFC<Props> = ({
  children,
  omittedHeight,
  overLayClassName = "",
  toggleBtnClassName = "",
  gaClassName = "",
}) => {
  const readMoreBoxRef = useRef<HTMLDivElement>(null);
  const [needReadMoreButton, setNeedReadMoreButton] = useState(false); // true: 省略必要, false: 省略不必要
  const [isExpanded, setIsExpanded] = useState(false); // true: 全表示, false: 省略表示
  const windowWidth = useWindowWidth();

  useEffect(() => {
    // 子ノードの高さが省略高さより小さい場合は省略する必要がない
    if (
      readMoreBoxRef.current &&
      readMoreBoxRef.current.scrollHeight <= omittedHeight
    ) {
      setNeedReadMoreButton(false);
    } else {
      setNeedReadMoreButton(true);
    }
  }, [omittedHeight, windowWidth]);

  return (
    <ReadMoreBox
      readMoreBoxRef={readMoreBoxRef}
      needReadMoreButton={needReadMoreButton}
      isExpanded={isExpanded}
      setIsExpanded={setIsExpanded}
      omittedHeight={omittedHeight}
      overLayClassName={overLayClassName}
      toggleBtnClassName={toggleBtnClassName}
      gaClassName={gaClassName}
    >
      {children}
    </ReadMoreBox>
  );
};

export default ReadMoreSection;
