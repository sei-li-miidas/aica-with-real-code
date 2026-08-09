"use client";

import SvgIcon from "@/components/icons/SvgIcon";

import searchLineAsset from "@/app/assets/svg/searchLine.svg";
import { ReactNode } from "react";

type SearchLineIconProps = {
  className?: string;
  fallback?: ReactNode;
};

const SearchLineIcon = ({ className = "", fallback = null }: SearchLineIconProps) => {
  return (
    <SvgIcon src={searchLineAsset.src} className={className} fallback={fallback} />
  );
};

export default SearchLineIcon;
