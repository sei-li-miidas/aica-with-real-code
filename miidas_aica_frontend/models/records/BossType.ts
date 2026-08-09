import { Record } from "immutable";
import { type RecordConstructorParameter } from "@/types/utility-types";

type Props = {
  Directive: number | null;
  Delegation: number | null;
  Listening: number | null;
  Dialogue: number | null;
  Negotiation: number | null;
};

/**
 * BossType
 * 上司との相性レコード
 */
export default class BossType extends Record<Props>({
  Directive: null,
  Delegation: null,
  Listening: null,
  Dialogue: null,
  Negotiation: null,
}) {
  constructor(bossType: RecordConstructorParameter<BossType>) {
    super({
      Directive: bossType.Directive || null,
      Delegation: bossType.Delegation || null,
      Listening: bossType.Listening || null,
      Dialogue: bossType.Dialogue || null,
      Negotiation: bossType.Negotiation || null,
    });
  }
}
