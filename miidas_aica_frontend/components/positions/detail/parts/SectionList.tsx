import { type MFC, type ReactNode } from "react";

import styles from "./SectionList.module.scss";

type Props = {
  children?: ReactNode;
};

/**
 * セクションリスト
 */
const SectionList: MFC<Props> = ({ children }) => {
  return (
    <div className={styles.sectionInner}>
      <ul className={styles.verticalList}>{children}</ul>
    </div>
  );
};

export default SectionList;
