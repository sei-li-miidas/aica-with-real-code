"use client";

import planeAsset from "@/app/assets/svg/plane.svg";
import SvgIcon from "@/components/icons/SvgIcon";
import { ReactNode } from "react";

type PlaneProps = {
  className?: string;
  fallback?: ReactNode;
};

const Plane = ({ className = "", fallback = null }: PlaneProps) => {
  return (
    <SvgIcon src={planeAsset.src} className={className} fallback={fallback} />
  );
};

export default Plane;
