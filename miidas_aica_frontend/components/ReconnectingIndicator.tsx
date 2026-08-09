import React, { useEffect, useRef, useState } from "react";
import "./ReconnectingIndicator.scss";

export default function ReconnectingIndicator() {
  const [dots, setDots] = useState<string>("");
  const intervalIdRef = useRef<NodeJS.Timeout | undefined>(undefined);

  useEffect(() => {
    if (!intervalIdRef.current) {
      intervalIdRef.current = setInterval(
        () => setDots((prev) => (prev === "..." ? "." : prev + ".")),
        1000,
      );
    }

    return () => {
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = undefined;
      }
    };
  }, []);

  return (
    <div className="reconnecting-indicator">
      <span>ネット接続中</span>
      {dots}
      <p>
        時間が経過しても接続できない場合、この画面を閉じて、再度開いてみてください
      </p>
    </div>
  );
}
