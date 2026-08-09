import { type MFC, type ReactNode } from "react";

import styles from "./SectionHeader.module.scss";

type Props = {
  children?: ReactNode;
};

/**
 * セクション見出し
 */
const SectionHeader: MFC<Props> = ({ children }) => {
  return <h2 className={styles.sectionHeader}>{children}</h2>;
};

export default SectionHeader;
