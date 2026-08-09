import { Record } from "immutable";

/**
 * 空のトレイト値レコード
 */
export default class EmptyTraitValue extends Record({}) {
  hasSomeValue() {
    return false;
  }
}
