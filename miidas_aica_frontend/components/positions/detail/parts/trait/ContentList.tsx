import { type MFC } from "react";
import styles from "./ContentList.module.scss";

type Props = {
  /** <li /> または <li /> のリスト */
  children?: React.ReactNode | React.ReactNode[];
};

/**
 * トレイトの値説明用のul要素
 */
const ContentList: MFC<Props> = ({ children = undefined }) => {
  return <ul className={styles.contentList}>{children}</ul>;
};

export default ContentList;
