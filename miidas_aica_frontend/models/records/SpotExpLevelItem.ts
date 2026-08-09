import { Record } from "immutable";

type Props = {
  /** 熟練度ID */
  ID: number | null;
  /** 熟練度の文言 */
  Name: string | null;
};

/**
 * SpotExpLevelItem
 * スポット応募時の熟練度回答の各選択肢用レコード
 */
export default class SpotExpLevelItem extends Record<Props>({
  ID: null,
  Name: null,
}) {}
