import { JSX, type MFC } from "react";
import { List } from "immutable";

import type MasterV2Record from "@/models/records/MasterV2";
import type TraitRecord from "@/models/position/records/Trait";
import CollapsibleOptionList from "@/components/positions/detail/parts/CollapsibleOptionList";
import { getLabelFromMasterRecord } from "@/helpers/positionDetail";

import ContentHorizontalList from "./ContentHorizontalList";

type Props = {
  valueImtList: List<TraitRecord | MasterV2Record>;
  hasNotApplicable: boolean;
  /** hasNotApplicableがtrueの場合は必要 */
  notApplicableValue?: number;
  /** hasNotApplicableがtrueの場合は必要 */
  optionImtList?: List<TraitRecord | MasterV2Record>;
  /** ラベルの生成をカスタマイズしたい場合は必要 */
  itemRenderer?: (masterImtRecord: TraitRecord | MasterV2Record) => JSX.Element;
};

/**
 * 横並べのラベル生成（デフォルト）
 */
const itemDefaultRenderer = (masterImtRecord: TraitRecord | MasterV2Record) => {
  const label = getLabelFromMasterRecord(masterImtRecord);

  // ラベルに対する補足無し
  return <li key={masterImtRecord.Name}>{label}</li>;
};

/**
 * 複数の設定値を横並べで表示
 *
 * - 「該当なし」選択時 ... 「該当なし」をラベルで表示し、その下に選択肢一覧を折りたたみ表示
 * - それ以外 ... 設定値を横並べで表示
 *
 * ラベルの生成をカスタマイズする場合、 itemRenderer(masterImtRecord) => {} をpropで渡す
 */
const ContentMultipleValue: MFC<Props> = ({
  valueImtList,
  hasNotApplicable,
  notApplicableValue = undefined,
  optionImtList = undefined,
  itemRenderer = undefined,
}) => {
  // 横並べのラベルを生成するメソッド
  const renderer = itemRenderer || itemDefaultRenderer;

  // 設定値のラベルのリストを生成
  const values = valueImtList.map((masterImtRecord) => {
    return renderer(masterImtRecord);
  });

  // ラベルを横並べにする
  const valueList = <ContentHorizontalList>{values}</ContentHorizontalList>;

  let collapsibleOptionList = null;

  // 「該当なし」が選択されている場合
  if (hasNotApplicable) {
    // オプション一覧のラベルのリストを生成
    const options = (optionImtList || List([]))
      .filter((masterImtRecord) => {
        // 「該当なし」は除外
        return masterImtRecord.ID !== notApplicableValue;
      })
      .map((masterImtRecord) => {
        return renderer(masterImtRecord);
      });

    // ラベルを横並べにする
    const optionList = <ContentHorizontalList>{options}</ContentHorizontalList>;

    // 折りたたみ表示にする
    collapsibleOptionList = <CollapsibleOptionList content={optionList} />;
  }

  return (
    <>
      {valueList}
      {collapsibleOptionList}
    </>
  );
};

export default ContentMultipleValue;
