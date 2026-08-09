import { type MFC, type ReactNode } from "react";
import styles from "./AsteriskedParagraph.module.scss";

type Props = {
  children: ReactNode;
  className?: string;
};

/**
 * 前に※がつく段落
 */
const AsteriskedParagraph: MFC<Props> = ({ children, className = "" }) => {
  return <p className={`${styles.paragraph} ${className}`}>{children}</p>;
};

export default AsteriskedParagraph;
