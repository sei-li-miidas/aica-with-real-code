"use client";

import { useEffect } from "react";
import { VirtualKeyboardGeometryChangeEvent } from "@/types/virtual-keyboard.d";

type Options = {
  cssVarName?: string;
};

const DEFAULT_CSS_VAR_NAME = "--vk-height";

export function useVirtualKeyboardHeightCssVar(options: Options = {}) {
  const cssVarName = options.cssVarName ?? DEFAULT_CSS_VAR_NAME;

  useEffect(() => {
    if (navigator.virtualKeyboard) {
      navigator.virtualKeyboard.overlaysContent = true;

      const geometryChangeHandler = (
        event: VirtualKeyboardGeometryChangeEvent,
      ) => {
        const vkHeight = event.target?.boundingRect.height;
        document.documentElement.style.setProperty(
          cssVarName,
          `${vkHeight}px`,
        );
      };

      navigator.virtualKeyboard.addEventListener(
        "geometrychange",
        geometryChangeHandler,
      );
      return () => {
        navigator.virtualKeyboard?.removeEventListener(
          "geometrychange",
          geometryChangeHandler,
        );
      };
    }

    if (window.visualViewport) {
      const resizeHandler = () => {
        const layoutHeight = window.innerHeight;
        const visualHeight = window.visualViewport?.height || 0;
        const keyboardHeight = Math.max(0, layoutHeight - visualHeight);

        document.documentElement.style.setProperty(
          cssVarName,
          `${keyboardHeight}px`,
        );
      };

      resizeHandler();
      window.visualViewport.addEventListener("resize", resizeHandler);
      return () => {
        window.visualViewport?.removeEventListener("resize", resizeHandler);
      };
    }
  }, [cssVarName]);
}
