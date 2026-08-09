import { type MFC } from "react";
import { clsx } from "@/utils/className";

import styles from "./ContentHorizontalList.module.scss";

type Props = {
  /** <li /> または <li /> のリスト */
  children?: React.ReactNode | React.ReactNode[];
  isNoLineBreak?: boolean;
};

/**
 * トレイトの値説明の横並べul要素
 */
const ContentHorizontalList: MFC<Props> = ({
  children = undefined,
  isNoLineBreak = false,
}) => {
  const cls = clsx(styles.contentList, isNoLineBreak && styles.noLineBreak);

  return <ul className={cls}>{children}</ul>;
};

export default ContentHorizontalList;
