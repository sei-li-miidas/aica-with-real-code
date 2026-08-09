import { Record } from "immutable";

/**
 * トレイトマスタデータのレコード
 */
export default class Trait extends Record<{
  /** ID */
  ID: number | null;
  /** 名前 */
  Name: string;
  /** 補足事項 */
  Note: string;
}>({
  ID: null,
  Name: "",
  Note: "",
}) {}
