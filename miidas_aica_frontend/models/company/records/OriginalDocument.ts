import { Record } from "immutable";

type Props = {
  /** オリジナル資料ID */
  ID: number | null;
  /** ラベル */
  Label: string;
};

/**
 * OriginalDocument
 * オリジナル資料のレコード
 */
export default class OriginalDocument extends Record<Props>({
  ID: null,
  Label: "",
}) {}
