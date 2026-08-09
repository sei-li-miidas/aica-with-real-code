/**
 * PCの画面幅かどうかを判定する
 */
export const isPCWidth = () => {
  return window.matchMedia("(min-width: 1024px)").matches;
};

/**
 * SPの画面幅かどうかを判定する
 */
export const isSPWidth = () => {
  return window.matchMedia("(max-width: 1023px)").matches;
};
