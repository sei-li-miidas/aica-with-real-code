import { type MFC } from "react";
import styles from "./SvgIcon.module.scss";

type Props = {
  icon: string;
  className?: string;
};

/**
 * SVGアイコンのコンポーネント
 */
const SvgIcon: MFC<Props> = ({ className = "", icon }) => {
  return (
    <svg className={`${styles.svg} ${className}`}>
      <use xlinkHref={icon} />
    </svg>
  );
};

export default SvgIcon;
