import PropTypes from "prop-types";

import {
  TRAITS,
  POSITION_DETAIL,
  WORK_ADDRESS_OMITTED_MAX_DISPLAY_COUNT,
} from "@/constants/position";

import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";
import ContentList from "@/components/positions/detail/parts/trait/ContentList";
import ContentListItem from "@/components/positions/detail/parts/trait/ContentListItem";
import NoteModalBtn from "@/components/positions/detail/parts/NoteModalBtn";
import ReadMoreItems from "@/components/positions/detail/parts/ReadMoreItems";

import styles from "./TraitWorkAddress.module.scss";

/**
 * 勤務地リスト
 */
export default function TraitWorkAddress(props) {
  const workAddressListName = renderworkAddressListName(
    props.positionImtRecord.get(POSITION_DETAIL.WORK_ADDRESS.ID),
  );
  const workAddressList = renderWorkAddressList(props.positionImtRecord);

  return (
    <TraitListItem
      itemKey={TRAITS.PTX_WORK_ADDRESS.ID}
      itemName={workAddressListName}
      content={workAddressList}
    />
  );
}

TraitWorkAddress.propTypes = {
  positionImtRecord: PropTypes.object.isRequired,
};

/**
 * 「勤務地」欄の項目名
 */
function renderworkAddressListName(traitImtRecord) {
  const noteText = traitImtRecord?.get("Note");
  // モーダルで表示する補足
  const noteModalBtn = noteText ? (
    <NoteModalBtn contentText={noteText} />
  ) : null;

  // [補足] ボタン横につけたラベル
  return (
    <>
      勤務地
      {noteModalBtn}
    </>
  );
}

/**
 * 「勤務地」欄の内容
 */
function renderWorkAddressList(positionImtRecord) {
  const traitImtRecord = positionImtRecord.get(POSITION_DETAIL.WORK_ADDRESS.ID);
  const masterImtList = traitImtRecord?.get("Values");

  if (!traitImtRecord || !masterImtList?.size) {
    return null;
  }

  const workAddressList = masterImtList
    .map((masterImtRecord) => {
      return (
        <li key={masterImtRecord.get("ID")}>
          <ContentList>
            <ContentListItem traitImtRecord={masterImtRecord} />
          </ContentList>
        </li>
      );
    })
    .toArray();

  // 勤務地が表示最大値より多い場合は「もっと見る」ボタンを表示
  if (masterImtList.size > WORK_ADDRESS_OMITTED_MAX_DISPLAY_COUNT) {
    return (
      <ReadMoreItems maxCount={WORK_ADDRESS_OMITTED_MAX_DISPLAY_COUNT}>
        {workAddressList}
      </ReadMoreItems>
    );
  }

  return <ul className={styles.list}>{workAddressList}</ul>;
}
