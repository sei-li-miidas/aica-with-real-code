import { type MFC, type ReactNode } from "react";

import styles from "./ContentTable.module.scss";

type Props = {
  children: ReactNode;
};

/**
 * トレイトの値の表
 */
const ContentTable: MFC<Props> = ({ children }) => {
  return (
    <table className={styles.table}>
      <tbody>{children}</tbody>
    </table>
  );
};

export default ContentTable;
