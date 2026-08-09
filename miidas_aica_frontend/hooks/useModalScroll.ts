import { useEffect, useRef, useState } from "react";

/**
 * モーダルのスクロールを扱うためのhooks
 */
export const useModalScroll = () => {
  const bodyRef = useRef<HTMLDivElement>(null);
  const [isScrolling, setIsScrolling] = useState<boolean>(false); // ボディがスクロールすることで活性化（ヘッダー・フッターにボーダーを表示）
  const [bodyScrollTop, setBodyScrollTop] = useState<number>(0);

  useEffect(() => {
    if (!bodyRef.current) return undefined;
    if (!("ResizeObserver" in window)) return undefined;

    // ボディが動的に領域が変更されたことを監視する(アコーディオンなど)
    // 1. 要素が DOM に挿入または削除された場合
    // 2. display プロパティが none になった場合、または、none でなくなった場合（display プロパティが inline の要素を除く）
    const bodyObserver = new ResizeObserver((entries) => {
      // NOTE: ResizeObserver loop completed with undelivered notifications がおきるため、requestAnimationFrameを使用
      // browserStackの Edge version 132 で登録フロー経験職種選択で職種小がたくさんあるケースで再現する（画面上はエラーなし）
      requestAnimationFrame(() => {
        // ボディにスクロールがあるか判定する
        if (
          entries[0].target &&
          entries[0].target.scrollHeight > entries[0].target.clientHeight
        ) {
          // タイトル下のボーダーが被る場合（スクロールあり）は、リストの先頭のborderTopを非表示
          setIsScrolling(true);
        } else {
          // スクロールなしは、リストの先頭のborderTopを表示
          setIsScrolling(false);
        }
      });
    });
    bodyObserver.observe(bodyRef.current);

    return () => {
      bodyObserver.disconnect();
    };
  }, []);

  const handleBodyScroll = () => {
    if (!bodyRef.current) return;

    setBodyScrollTop(bodyRef.current.scrollTop);
  };

  return {
    bodyRef,
    isScrolling,
    bodyScrollTop,
    handleBodyScroll,
  };
};
