/**
 * arrayを保証して空を除く。
 * NodeListのような配列ライクなオブジェクトを引数に渡すときは、Array.from()で変換してから渡すこと。
 */
export function assureArray<T>(values: T | T[]): T[] {
  const array = Array.isArray(values) ? values : [values];
  return array.filter((value) => {
    return value || value === 0;
  });
}
