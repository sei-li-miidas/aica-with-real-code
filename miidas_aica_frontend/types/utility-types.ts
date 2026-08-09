import { List, RecordOf } from "immutable";

/**
 * 空のobject。`{}`
 */
export type EmptyObject = Record<string, never>;

/**
 * 空のobject
 */
export type EmptyProps = {};

/**
 * 何らかのobject({[key: string]: unknown})
 */
export type AnyObject = Record<string, unknown>;

/**
 * Objectのvalue union type
 *
 * @example
 * type Obj =  {
 *   x: string;
 *   y: number;
 * };
 * ValuesType<Obj>; // string | number
 */
export type ValuesType<T extends AnyObject> = T[keyof T];

/**
 * {@link List}のflatten処理を行なう型ガード
 * @param aImtList 処理対象
 * @returns flatten結果
 * @example
 * const hogeImtRecord = flattenImmutableList(aImtList) {
 *   // hogeImtRecord型はaImtList中のリストの中のデータの型になる
 * }
 */
export const flattenImmutableList = <T>(aImtList: List<List<T>>): List<T> => {
  // eslint-disable-next-line @typescript-eslint/consistent-type-assertions
  return aImtList.flatten(1) as List<T>;
};

/**
 * {@link List}のdeep flatten処理を行なう型ガード
 * @param aImtList 処理対象
 * @returns flatten結果
 * @example
 * const hogeImtRecord = flattenImmutableListDeeply<HogeRecord>(aImtList) {
 *   // hogeImtRecord型はaImtList中のリストの中のデータの型になる
 * }
 */
export const flattenImmutableListDeeply = <T>(
  aImtList: List<unknown>,
): List<T> => {
  // eslint-disable-next-line @typescript-eslint/consistent-type-assertions
  return aImtList.flatten() as List<T>;
};

/**
 * DefaultPropsとTのunion typeを返す
 *
 * @example
 * type Props = ClassComponentProps<typeof SomeComponent.defaultProps, {
 *   param1: number | null;
 * }>;
 * class SomeComponent extends React.Component<Props, State> {
 *   static defaultProps = {
 *     param1: null;
 *   };
 * }
 * // param1 is number | null
 */
export type ClassComponentProps<DefaultProps, T = {}> = {
  [K in keyof DefaultProps]: K extends keyof T
    ? Exclude<DefaultProps[K] | T[K], undefined>
    : DefaultProps[K];
} & T;

/**
 * Arrayのelementの型を返す
 * @example
 * type Element = ArrayElement<string[]>;
 * // string
 */
export type ArrayElement<ArrayType extends readonly unknown[]> =
  ArrayType extends readonly (infer ElementType)[] ? ElementType : never;

/**
 * keyがobjのキーであるかを判定する型ガード
 *
 * @example
 * const obj =  {
 *   x: 1;
 *   y: 2;
 * } as const;
 * const key: string = '';
 * if (isKeyOf(key, obj)) {
 *   key is "x" | "y"
 * }
 * key is string
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const isKeyOf = <T extends object>(
  key: keyof any,
  obj: T,
): key is keyof T => {
  return key in obj;
};
/**
 * reduxのDeepPartialを拡張
 * DeepPartialに渡すarrayの要素がoptionalな場合にundefinedを含まないようにする
 */
type DeepPartial<T> = {
  [K in keyof T]?: T[K] extends (infer U)[]
    ? DeepPartial<U>[]
    : T[K] extends object
      ? DeepPartial<T[K]>
      : T[K];
};

/**
 * ImmutableレコードのConstructorの引数の型を返す
 * @example
 * constructor(data: RecordConstructorParameter<HogeRecord>) {
 * // HogeRecordはImmutable.Recordクラス名
 */
// Utility type to convert an Immutable Record to its JS representation
type RecordToJS<T> = T extends RecordOf<infer S> ? S : never;
export type RecordConstructorParameter<R> = DeepPartial<RecordToJS<R>>;

/**
 * stylesの型
 */
export type Styles = {
  [key: string]: string;
};

/**
 * Mapのnull keyを削除する
 */
export const removeImmutableMapNullKey = <K, V>(
  aImtMap: Map<K | null, V>,
): Map<K, V> => {
  // eslint-disable-next-line @typescript-eslint/consistent-type-assertions
  // @ts-expect-error: 型エラーが起きないよう後で修正する
  return aImtMap.filter((_, key) => key !== null) as Map<K, V>;
};

/**
 * プロパティにNullableを適用する
 */
export type NonNullableProperties<T> = {
  [K in keyof T]: NonNullable<T[K]>;
};

/**
 * オブジェクトの一部プロパティをオプショナルに変更する
 */
export type MarkOptional<T, K extends keyof T> = Omit<T, K> &
  Partial<Pick<T, K>>;

/**
 * オブジェクトの一部プロパティをNonNullableに変更する
 */
export type MarkNonNullable<T, K extends keyof T> = Omit<T, K> &
  NonNullableProperties<Pick<T, K>>;

/**
 * オブジェクト（Record<string, unknown>）型かどうかを判定する
 */
export const isObject = (value: unknown): value is Record<string, unknown> => {
  return !!(Object.prototype.toString.call(value).slice(8, -1) === "Object");
};

/**
 * オブジェクトのキーを取得する
 */
export const getKeys = <T extends { [key: string]: unknown }>(
  obj: T,
): `${Exclude<keyof T, symbol>}`[] => {
  // eslint-disable-next-line @typescript-eslint/consistent-type-assertions
  return Object.keys(obj) as `${Exclude<keyof T, symbol>}`[];
};

/**
 * 配列の要素かどうかを判定する
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const isArrayElement = <T>(array: T[], value: any): value is T => {
  // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
  return array.includes(value);
};

/**
 * Recordのproperties
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type RecordProps<T extends RecordOf<any>> =
  T extends RecordOf<infer S> ? S : never;

/**
 * Recordの指定されたキーの値にNonNullableを適用する
 */
export type MarkRecordNonNullable<
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  T extends RecordOf<any>,
  K extends keyof RecordProps<T>,
> = RecordOf<MarkNonNullable<RecordProps<T>, K>>;

export type IDName<K, V> = {
  ID: K;
  Name: V;
};

export type KeyValue = IDName<string, string>;

export type MasterType = IDName<number, string>;

export type SortedMasterType = MasterType & {
  // 画面表示順
  SortOrder: number;
};

export type Address = {
  prefecture: MasterType;
  city: MasterType;
};

export type School = MasterType & {
  Kana: string;
  SchoolTypeID: number;
};

export type JobType = MasterType & {
  Description: string;
};
