import { useState, type MFC, type ReactNode } from "react";

import { assureArray } from "@/utils/collection";

import styles from "./ReadMoreItems.module.scss";
import ReadMoreBox from "./ReadMoreBox";

type Props = {
  children: ReactNode;
  maxCount: number;
};

/**
 * 表示を省略し「続きを読む」ボタンを表示（折りたたみ時の最大表示数に応じてprops.childrenを操作）
 */
const ReadMoreItems: MFC<Props> = ({ children, maxCount }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // 配列を保証して、maxCountまで切り取る
  const displayList = isExpanded
    ? children
    : assureArray(children).slice(0, maxCount);

  return (
    <ReadMoreBox isExpanded={isExpanded} setIsExpanded={setIsExpanded}>
      <ul className={styles.displayList}>{displayList}</ul>
    </ReadMoreBox>
  );
};

export default ReadMoreItems;
