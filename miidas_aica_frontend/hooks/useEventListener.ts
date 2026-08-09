import { useRef, useEffect } from "react";

type Handler = (event: HTMLElementEventMap[keyof HTMLElementEventMap]) => void;

/**
 * イベントリスナーの登録・削除をするHooks
 * @param {string} eventName
 * @param {function} handler
 * @param {Element} element
 */
// NOTE: https://usehooks.com/useEventListener/
export const useEventListener = (
  eventName: keyof HTMLElementEventMap,
  handler: Handler,
  element?: HTMLElement,
) => {
  // Create a ref that stores handler
  const savedHandler = useRef<Handler>(null);

  // Update ref.current value if handler changes.
  // This allows our effect below to always get latest handler ...
  // ... without us needing to pass it in effect deps array ...
  // ... and potentially cause effect to re-run every render.
  useEffect(() => {
    savedHandler.current = handler;
  }, [handler]);

  useEffect(
    () => {
      // Make sure element supports addEventListener
      // On
      const elm = element || window;
      const isSupported = elm && elm.addEventListener;
      if (!isSupported) return;

      // Create event listener that calls handler function stored in ref
      const eventListener = (
        event: HTMLElementEventMap[keyof HTMLElementEventMap],
      ) => {
        if (savedHandler.current) {
          savedHandler.current(event);
        }
      };
      // Add event listener
      elm.addEventListener(eventName, eventListener);

      // Remove event listener on cleanup
      // eslint-disable-next-line consistent-return
      return () => {
        elm.removeEventListener(eventName, eventListener);
      };
    },
    [eventName, element], // Re-run if eventName or element changes
  );
};
