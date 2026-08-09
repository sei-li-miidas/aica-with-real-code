import { Record } from "immutable";

/**
 * 事業のレコード
 */
export default class Business extends Record<{
  /** 業種小ID */
  SmallID: number | null;
  /** 業種小名 */
  Name: string;
  /** メイン業種フラグ */
  IsMain: boolean;
}>({
  SmallID: null,
  Name: "",
  IsMain: false,
}) {}
