"use client";

import SvgIcon from "@/components/icons/SvgIcon";

import pencilLineAsset from "@/app/assets/svg/pencilLine.svg";
import { ReactNode } from "react";

type PencilLineIconProps = {
  className?: string;
  fallback?: ReactNode;
};

const PencilLineIcon = ({ className = "", fallback = null }: PencilLineIconProps) => {
  return (
    <SvgIcon src={pencilLineAsset.src} className={className} fallback={fallback} />
  );
};

export default PencilLineIcon;
