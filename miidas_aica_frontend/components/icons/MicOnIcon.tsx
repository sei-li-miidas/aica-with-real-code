import micOnAsset from "@/app/assets/svg/mic_on.svg";
import SvgIcon from "@/components/icons/SvgIcon";
import { ReactNode } from "react";

type MicOnIconProps = {
  className?: string;
  fallback?: ReactNode;
};

const MicOnIcon = ({ className = "", fallback = null }: MicOnIconProps) => {
  return (
    <SvgIcon src={micOnAsset.src} className={className} fallback={fallback} />
  );
};

export default MicOnIcon;
