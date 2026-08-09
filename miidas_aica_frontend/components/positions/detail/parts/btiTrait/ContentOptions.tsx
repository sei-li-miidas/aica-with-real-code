import { type MFC } from "react";

import ContentHorizontalList from "@/components/positions/detail/parts/trait/ContentHorizontalList";

type Props = {
  optionImtMap: Immutable.Map<string, string>;
  notApplicableValue: number;
};

/**
 * 「該当なし」以外のオプション一覧を表示
 */
const ContentOptions: MFC<Props> = ({ optionImtMap, notApplicableValue }) => {
  // オプション一覧のラベルのリストを生成
  const options = optionImtMap
    .filter((label, value) => {
      // valueはMapのキー文字列なので、notApplicableValueをStringに変換
      return value !== String(notApplicableValue);
    })
    .valueSeq() // Immutable.MapからImmutable.Listに変換
    .map((label) => {
      return <li key={label}>{label}</li>;
    });

  // ラベルを横並べにする
  return <ContentHorizontalList>{options}</ContentHorizontalList>;
};

export default ContentOptions;
