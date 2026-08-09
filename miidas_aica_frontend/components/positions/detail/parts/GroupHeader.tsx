import { type MFC } from "react";
import styles from "./GroupHeader.module.scss";

type Props = {
  children?: React.ReactNode;
};

/**
 * グループ見出し
 */
const GroupHeader: MFC<Props> = ({ children = undefined }) => {
  return <h3 className={styles.groupHeader}>{children}</h3>;
};

export default GroupHeader;
