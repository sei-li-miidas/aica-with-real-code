/**
 * 文字列がnull、undefined、または空文字列かどうかをチェックします
 * @param str - チェックする文字列
 * @param trim - チェック前に空白文字をトリムするかどうか (デフォルト: true)
 * @returns 文字列がnull、undefined、または空文字列の場合はtrue (トリムが有効な場合はトリム後)
 */
export function isNullOrEmpty(
  str: string | null | undefined,
  trim: boolean = true,
): boolean {
  if (str == null) {
    return true;
  }

  const stringValue = String(str);
  const stringToCheck = trim ? stringValue.trim() : stringValue;
  return stringToCheck === "";
}

/**
 * 文字列に内容があるかどうかをチェックします (null、undefined、空文字列ではない)
 * @param str - チェックする文字列
 * @param trim - チェック前に空白文字をトリムするかどうか (デフォルト: true)
 * @returns 文字列に意味のある内容がある場合はtrue
 */
export function hasContent(
  str: string | null | undefined,
  trim: boolean = true,
): boolean {
  return !isNullOrEmpty(str, trim);
}
