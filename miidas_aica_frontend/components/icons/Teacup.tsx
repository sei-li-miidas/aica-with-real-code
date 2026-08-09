"use client";

import SvgIcon from "@/components/icons/SvgIcon";

import teacupAsset from "@/app/assets/svg/teacup.svg";
import { ReactNode } from "react";

type TeacupIconProps = {
  className?: string;
  fallback?: ReactNode;
};

const TeacupIcon = ({ className = "", fallback = null }: TeacupIconProps) => {
  return (
    <SvgIcon src={teacupAsset.src} className={className} fallback={fallback} />
  );
};

export default TeacupIcon;
