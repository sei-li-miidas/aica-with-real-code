import { interpolateColor } from "../utils/colorUtils";
import { useRef, useEffect, useState } from "react";
import {
  COLOR_TIMEOUT_100,
  COLOR_TIMEOUT_75,
  COLOR_TIMEOUT_50,
  COLOR_TIMEOUT_25,
  COLOR_TIMEOUT_0,
  VOICE_INPUT_SILENCE_THRESHOLD,
} from "../constants/app";
import "./TimeoutBar.scss";

const TimeoutBar = () => {
  const selfRef = useRef<HTMLDivElement>(null);
  const [parentWidth, setParentWidth] = useState(0);
  const [backgroundColor, setBackgroundColor] = useState(COLOR_TIMEOUT_100);
  const [currentWidth, setCurrentWidth] = useState(0);

  const [progressPercent, setProgressPercent] = useState(100); // 100%からスタート

  useEffect(() => {
    let animationFrameId: number;
    let startTime: DOMHighResTimeStamp;

    const animate = (currentTime: DOMHighResTimeStamp) => {
      if (!startTime) startTime = currentTime;
      const elapsedTime = currentTime - startTime;

      if (elapsedTime < VOICE_INPUT_SILENCE_THRESHOLD) {
        const newProgress =
          100 - (elapsedTime / VOICE_INPUT_SILENCE_THRESHOLD) * 100;
        setProgressPercent(newProgress);
        animationFrameId = requestAnimationFrame(animate);
      } else {
        setProgressPercent(0);
        cancelAnimationFrame(animationFrameId);
      }
    };

    setProgressPercent(100); // 表示する場合は100%にリセットする
    animationFrameId = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  useEffect(() => {
    const calculateCurrentColor = (progress: number): string => {
      if (progress >= 75) {
        // 75-100% range
        const factor = (progress - 75) / 25;
        return interpolateColor(COLOR_TIMEOUT_75, COLOR_TIMEOUT_100, factor);
      } else if (progress >= 50) {
        // 50-75% range
        const factor = (progress - 50) / 25;
        return interpolateColor(COLOR_TIMEOUT_50, COLOR_TIMEOUT_75, factor);
      } else if (progress >= 25) {
        // 25-50% range
        const factor = (progress - 25) / 25;
        return interpolateColor(COLOR_TIMEOUT_25, COLOR_TIMEOUT_50, factor);
      } else {
        // 0-25% range
        const factor = progress / 25;
        return interpolateColor(COLOR_TIMEOUT_0, COLOR_TIMEOUT_25, factor);
      }
    };

    const newColor = calculateCurrentColor(progressPercent);
    setBackgroundColor(newColor);
  }, [progressPercent]);

  useEffect(() => {
    if (parentWidth === 0 || progressPercent === 0) return;
    const curWidth = parentWidth * (progressPercent / 100);
    setCurrentWidth(curWidth);
  }, [parentWidth, progressPercent]);

  useEffect(() => {
    const parentElement = selfRef.current?.parentElement;
    if (parentElement) {
      const parentWidth = parentElement.offsetWidth;
      setParentWidth(parentWidth);
    }
  }, []);

  return (
    <div
      ref={selfRef}
      className={"timeout-bar"}
      style={{
        width: `${currentWidth}px`,
        backgroundColor: backgroundColor,
      }}
    />
  );
};

export default TimeoutBar;
