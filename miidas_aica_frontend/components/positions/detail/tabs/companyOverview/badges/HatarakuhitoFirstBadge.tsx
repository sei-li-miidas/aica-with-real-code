import { type MFC } from "react";
import Image from "@/components/utils/Image";

import styles from "./HatarakuhitoFirstBadge.module.scss";

type Props = {
  className?: string;
  helpTip?: React.ReactNode;
  width?: number;
  height?: number;
};

/**
 * はたらく人ファースト宣言バッジ
 */
const HatarakuhitoFirstBadge: MFC<Props> = ({
  className = "",
  helpTip = null,
  width,
  height,
}) => {
  const badge = (
    <Image
      src="/assets/next/img/offers/img_hatarakuhito_first_badge.svg"
      alt="はたらく人ファースト宣言バッジ"
      width={width}
      height={height}
    />
  );

  if (helpTip) {
    return (
      <div className={`${styles.hfbWrapper} ${className}`}>
        {badge}
        {helpTip}
      </div>
    );
  }

  return badge;
};

export default HatarakuhitoFirstBadge;
