import { Record } from "immutable";

/**
 * マスタデータV2のレコード
 * IDとNameのみを持つ設計です。
 * そのため、新規プロパティを追加しないでください。
 */
export default class MasterV2 extends Record<{
  /** ID */
  ID: number | null;
  /** 名前 */
  Name: string;
}>({
  ID: null,
  Name: "",
}) {}
