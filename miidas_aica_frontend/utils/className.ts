/**
 * 引数で指定されたクラス名を文字列連結して返す
 * ex)
 *      clsx(
 *          styles.text, // 無条件指定
 *          hasError ? styles.textHasError : null, // 条件付き
 *          hasError ? styles.textHasError : '', // 条件付き
 *          hasError ? styles.textHasError : undefined, // 条件付き
 *          hasError && styles.textHasError, // 条件付き
 *      )
 */
export function clsx(...classNames: (string | false | null | undefined)[]) {
  return classNames.filter(Boolean).join(" ");
}
