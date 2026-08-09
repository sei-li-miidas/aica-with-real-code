import { type MFC } from "react";
import { List } from "immutable";

import Image from "@/components/utils/Image";
import type AppealPointTagRecord from "@/models/offers/records/AppealPointTag";

import styles from "./AppealPointTags.module.scss";

type TagImtList = List<AppealPointTagRecord>;

type Props = {
  tagImtList: TagImtList;
};

// ジャンルとSVGアイコン画像のマッピング
const GENRE_SVG_ICON_MAP = {
  work_time: "/assets/next/img/offers/ico_clock.svg",
  remote: "/assets/next/img/offers/ico_home.svg",
  income: "/assets/next/img/offers/ico_jpy.svg",
  inexperienced_welcome: "/assets/next/img/offers/ico_beginner.svg",
} as const;

const AppealPointTags: MFC<Props> = ({ tagImtList }) => {
  const importantTagImtList = tagImtList.filter(
    (tagImtRecord) => tagImtRecord.IsImportant,
  );
  const importantListItems = renderImportantListItems(importantTagImtList);
  const hasImportantListItem = importantListItems.length > 0;
  const importantList = hasImportantListItem ? (
    <div className={styles["sh-AppealPoint_Important"]}>
      <h2 className={styles["sh-AppealPoint_ImportantTitle"]}>
        アピールポイント
      </h2>
      <ul className={styles["sh-AppealPoint_ImportantList"]}>
        {importantListItems}
      </ul>
    </div>
  ) : null;

  const otherTagImtList = tagImtList.filter(
    (tagImtRecord) => !tagImtRecord.IsImportant,
  );
  const otherListItems = renderOtherListItems(otherTagImtList);
  const otherList =
    otherListItems.length > 0 ? (
      <div className={styles["sh-AppealPoint_Other"]}>
        <h2 className={styles["sh-AppealPoint_OtherTitle"]}>その他の特徴</h2>
        <ul className={styles["sh-AppealPoint_OtherList"]}>{otherListItems}</ul>
      </div>
    ) : null;

  const appealPointAreaCls = [
    styles["sh-AppealPoint"],
    hasImportantListItem ? styles["sh-AppealPoint-withImportant"] : null,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={appealPointAreaCls}>
      {importantList}
      {otherList}
    </div>
  );
};

/**
 * 「アピールポイント」枠の各アイテムを描画
 * @param importantTagImtList
 */
function renderImportantListItems(importantTagImtList: TagImtList) {
  return importantTagImtList
    .map((tagImtRecord) => {
      const tagLabel = tagImtRecord.Label;
      const iconUrl = tagImtRecord.Genre
        ? GENRE_SVG_ICON_MAP[tagImtRecord.Genre]
        : "";
      const icon = iconUrl ? (
        <Image
          className={styles["sh-AppealPoint_ImportantListItemIcon"]}
          src={iconUrl}
          alt={tagLabel}
        />
      ) : null;

      return (
        <li
          key={tagLabel}
          className={styles["sh-AppealPoint_ImportantListItem"]}
        >
          {icon}
          {tagLabel}
        </li>
      );
    })
    .toArray();
}

/**
 * 「その他の特徴」枠の各アイテムを描画
 * @param otherTagImtList
 */
function renderOtherListItems(otherTagImtList: TagImtList) {
  return otherTagImtList
    .map((tagImtRecord) => {
      const tagLabel = tagImtRecord.Label;
      return (
        <li key={tagLabel} className={styles["sh-AppealPoint_OtherListItem"]}>
          {tagLabel}
        </li>
      );
    })
    .toArray();
}

export default AppealPointTags;
