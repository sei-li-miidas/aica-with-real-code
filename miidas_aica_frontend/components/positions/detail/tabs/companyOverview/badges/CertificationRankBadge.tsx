import { type MFC, type MouseEventHandler } from "react";

import { CERTIFICATION_RANK } from "@/constants/companies";
import Image from "@/components/utils/Image";

import { NOP } from "@/constants/app";
import styles from "./CertificationRankBadge.module.scss";

type Props = {
  className?: string;
  certificationRank: number;
  width?: number;
  height?: number;
  helpTip?: React.ReactNode;
  onClick?: MouseEventHandler<HTMLButtonElement>;
};

/**
 * 認定バッジ（求人一覧カード等で使用）
 */

const CertificationRankBadge: MFC<Props> = ({
  className = "",
  certificationRank,
  width,
  height,
  helpTip = null,
  onClick = NOP,
}) => {
  const certificationMap = {
    [CERTIFICATION_RANK.GOLD]: {
      src: "/assets/next/img/offers/img_certification_gold.svg",
      alt: "認定ゴールド",
    },
    [CERTIFICATION_RANK.SILVER]: {
      src: "/assets/next/img/offers/img_certification_silver.svg",
      alt: "認定シルバー",
    },
    [CERTIFICATION_RANK.BRONZE]: {
      src: "/assets/next/img/offers/img_certification_bronze.svg",
      alt: "認定ブロンズ",
    },
  };
  const certification = certificationMap[certificationRank];

  if (!certification) return null;

  const certificationBadge = (
    <Image
      src={certification.src}
      alt={certification.alt}
      width={width}
      height={height}
    />
  );

  if (helpTip) {
    return (
      <button
        type="button"
        onClick={onClick}
        className={`${styles.certificationBtn} ${className}`}
      >
        {certificationBadge}
        {helpTip}
      </button>
    );
  }

  return certificationBadge;
};

export default CertificationRankBadge;
