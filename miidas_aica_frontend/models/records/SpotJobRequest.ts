import { Record } from "immutable";

type Props = {
  /** スポット依頼内容ID */
  ID: number | null;
  /** 依頼内容 */
  Name: string;
  /** 熟練度パターン（"a" | "b" | "c" | "d" | "e"） */
  SpotExpLevelPattern: string;
};

/**
 * SpotJobRequest
 * スポット依頼内容レコード
 */
export default class SpotJobRequest extends Record<Props>({
  ID: null,
  Name: "",
  SpotExpLevelPattern: "",
}) {}
