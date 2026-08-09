import { useState } from "react";
import { useEventListener } from "@/hooks/useEventListener";
import { useDebounce } from "@/hooks/useDebounce";

/**
 * ウィンドウ横幅のリサイズを検知して何かをするカスタムフック
 */
export const useWindowWidth = () => {
  const [width, setWidth] = useState(window.innerWidth);

  const setWindowWidth = () => {
    setWidth(window.innerWidth);
  };
  const debouncedSetWidth = useDebounce(setWindowWidth, 150);

  useEventListener("resize", debouncedSetWidth);

  return width;
};
