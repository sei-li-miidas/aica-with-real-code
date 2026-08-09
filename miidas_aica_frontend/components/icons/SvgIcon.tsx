"use client";

import { useEffect, useState, type ReactNode } from "react";

export type SvgIconProps = {
  src: string;
  className?: string;
  fallback?: ReactNode;
};

const SvgIcon = ({ src, className = "", fallback = null }: SvgIconProps) => {
  const [svgMarkup, setSvgMarkup] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    console.log("SvgIcon isMounted =", isMounted);

    const loadSvg = async () => {
      try {
        console.log("SvgIcon going to load", src);
        const response = await fetch(src);
        if (!response.ok) {
          throw new Error(`Failed to load svg: ${response.status}`);
        }
        const svgText = await response.text();
        if (isMounted) {
          setSvgMarkup(svgText);
        }
      } catch (error) {
        console.error("Could not fetch svg", error);
      }
    };

    void loadSvg();

    return () => {
      isMounted = false;
    };
  }, [src]);

  if (!svgMarkup) {
    if (fallback) {
      console.log("SvgIcon fallback", fallback);
      return <>{fallback}</>;
    } else {
      console.log("SvgIcon null");
      return null;
    }
  }

  console.log("SvgIcon span");
  return (
    <span
      className={className}
      aria-hidden
      dangerouslySetInnerHTML={{
        __html: svgMarkup,
      }}
    />
  );
};

export default SvgIcon;
