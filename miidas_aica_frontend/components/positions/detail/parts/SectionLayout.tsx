import { type MFC, type ReactNode } from "react";

import styles from "./SectionLayout.module.scss";

type Props = {
  children?: ReactNode;
};

/**
 * セクションレイアウト
 */
const SectionLayout: MFC<Props> = ({ children }) => {
  return <section className={styles.section}>{children}</section>;
};

export default SectionLayout;
