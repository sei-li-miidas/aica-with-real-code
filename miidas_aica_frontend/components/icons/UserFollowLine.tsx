"use client";

import SvgIcon from "@/components/icons/SvgIcon";

import userFollowLineAsset from "@/app/assets/svg/userFollowLine.svg";
import { ReactNode } from "react";

type UserFollowLineIconProps = {
  className?: string;
  fallback?: ReactNode;
};

const UserFollowLineIcon = ({ className = "", fallback = null }: UserFollowLineIconProps) => {
  return (
    <SvgIcon src={userFollowLineAsset.src} className={className} fallback={fallback} />
  );
};

export default UserFollowLineIcon;
