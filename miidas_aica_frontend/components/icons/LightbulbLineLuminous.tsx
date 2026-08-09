"use client";

import SvgIcon from "@/components/icons/SvgIcon";

import lightbulbLineLuminousAsset from "@/app/assets/svg/lightbulbLineLuminous.svg";
import { ReactNode } from "react";

type LightbulbLineLuminousIconProps = {
  className?: string;
  fallback?: ReactNode;
};

const LightbulbLineLuminousIcon = ({ className = "", fallback = null }: LightbulbLineLuminousIconProps) => {
  return (
    <SvgIcon src={lightbulbLineLuminousAsset.src} className={className} fallback={fallback} />
  );
};

export default LightbulbLineLuminousIcon;
