/* eslint-disable max-classes-per-file */
import { List, RecordOf } from "immutable";

/**
 * ImmutableListの要素検索
 */
export class ImmutableListFinder {
  /* eslint-disable @typescript-eslint/no-explicit-any */
  /**
   * 指定されたキーと値を持つ要素を取得する
   */
  static findItem<R extends RecordOf<any>, K extends keyof R>(
    list: List<R>,
    key: K,
    value: R[K],
  ): R | undefined {
    return list.find((item) => {
      return item[key] === value;
    });
  }

  /**
   * 指定されたIDを持つ要素を取得する
   */
  static findById<R extends { ID: unknown } & RecordOf<any>>(
    list: List<R>,
    id: R["ID"],
  ): R | undefined {
    return this.findItem(list, "ID", id);
  }

  /**
   * 指定されたリストに含まれるIDを持つ要素をすべて取得する
   */
  static findByIds<R extends { ID: unknown } & RecordOf<any>>(
    list: List<R>,
    ids: R["ID"][],
  ) {
    return list.filter((item) => {
      return ids.includes(item.ID);
    });
  }

  /**
   * 指定されたIDを持つ要素のNameを取得する
   */
  static findNameById<R extends { ID: unknown; Name: unknown } & RecordOf<any>>(
    list: List<R>,
    id: R["ID"],
  ): R["Name"] | undefined {
    const item = this.findById(list, id);
    return item?.Name;
  }

  /**
   * 指定されたリストに含まれるIDを持つ要素のNameをすべて取得する
   */
  static findNamesByIds<
    R extends { ID: unknown; Name: unknown } & RecordOf<any>,
  >(list: List<R>, ids: R["ID"][]) {
    return ids.map((id) => {
      return this.findNameById(list, id);
    });
  }

  /**
   * 指定されたキーと値を持つ要素のインデックスを取得する
   */
  static findIndex<R extends RecordOf<any>, K extends keyof R>(
    list: List<R>,
    key: K,
    value: R[K],
  ) {
    return list.findIndex((item) => {
      return item[key] === value;
    });
  }

  /**
   * 指定されたIDを持つ要素のインデックスを取得する
   */
  static findIndexById<R extends { ID: unknown } & RecordOf<any>>(
    list: List<R>,
    id: R["ID"],
  ) {
    return this.findIndex(list, "ID", id);
  }
  /* eslint-enable @typescript-eslint/no-explicit-any */
}

/**
 * arrayの要素検索
 */
export class ArrayFinder {
  /**
   * 指定されたキーと値を持つ要素を取得する
   */
  static findItem<R extends Record<string, unknown>>(
    list: R[],
    key: keyof R,
    value: unknown,
  ) {
    return list.find((item) => {
      return item[key] === value;
    });
  }

  /**
   * 指定されたIDを持つ要素を取得する
   */
  static findById<R extends Record<"ID", unknown>, I extends R["ID"]>(
    list: R[],
    id: I,
  ) {
    return this.findItem(list, "ID", id);
  }

  /**
   * 指定されたIDを持つ要素のNameを取得する
   */
  static findNameById<
    R extends Record<"ID" | "Name", unknown>,
    I extends R["ID"],
  >(list: R[], id: I): R["Name"] | undefined {
    const item = this.findById(list, id);
    return item?.Name;
  }

  /**
   * 指定されたリストに含まれるIDを持つ要素のNameをすべて取得する
   */
  static findNamesByIds<
    R extends Record<"ID" | "Name", unknown>,
    I extends R["ID"],
  >(list: R[], ids: I[]) {
    return ids.map((id) => {
      return this.findNameById(list, id);
    });
  }
}
