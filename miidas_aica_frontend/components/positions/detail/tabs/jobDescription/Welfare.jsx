import PropTypes from "prop-types";
import { List } from "immutable";

import {
  POSITION_DETAIL,
  TRAITS,
  EXCEPTION_TRAIT_OPTION,
} from "@/constants/position";
import {
  TRAITS as COMPANY_TRAITS,
  EXCEPTION_HIDDEN_TRAIT_OPTION,
} from "@/constants/companies";
import { ImmutableListFinder } from "@/utils/finder";

import TraitList from "@/components/positions/detail/parts/trait/TraitList";
import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";
import ContentMultipleValueWithNote from "@/components/positions/detail/parts/trait/ContentMultipleValueWithNote";
import NoteModalBtn from "@/components/positions/detail/parts/NoteModalBtn";
import TraitSmokeFree from "./traitListItem/TraitSmokeFree";

/**
 * 「福利厚生」
 */
export default function Welfare({
  positionImtRecord,
  companyImtRecord,
  smokeFreeMasterImtRecord,
  hasSmokeFreeValue,
}) {
  // 社会保険
  const insurance = renderWelfare(companyImtRecord, "WelfareInsurance");
  // 福利厚生
  const benefit = renderWelfare(companyImtRecord, "WelfareBenefit");
  // 人気の福利厚生
  const popular = renderWelfare(companyImtRecord, "WelfarePopular");
  // その他福利厚生
  const other = renderWelfare(companyImtRecord, "WelfareOther");
  // 実績のある制度
  const achievement = renderWelfare(companyImtRecord, "WelfareAchievement");

  // 労働環境の特徴の項目名
  const workEnvironmentName = renderWorkEnvironmentName(
    positionImtRecord.get(POSITION_DETAIL.IT_ENGINEER_WORK_ENVIRONMENT.ID),
  );
  // 労働環境の特徴
  const workEnvironmentFeatures =
    renderWorkEnvironmentFeatures(positionImtRecord);
  // 受動喫煙対策
  const smokeFree = hasSmokeFreeValue ? (
    <TraitSmokeFree
      positionImtRecord={positionImtRecord}
      smokeFreeMasterImtRecord={smokeFreeMasterImtRecord}
    />
  ) : null;

  return (
    <TraitList>
      <TraitListItem
        itemKey={COMPANY_TRAITS.CTX_WELFARE__INSURANCE.ID}
        itemName="社会保険"
        content={insurance}
      />
      <TraitListItem
        itemKey={COMPANY_TRAITS.CTX_WELFARE__BENEFIT.ID}
        itemName="福利厚生"
        content={benefit}
      />
      <TraitListItem
        itemKey={COMPANY_TRAITS.CTX_WELFARE__POPULAR.ID}
        itemName="人気の福利厚生"
        content={popular}
      />
      <TraitListItem
        itemKey={COMPANY_TRAITS.CTX_WELFARE__OTHER.ID}
        itemName="その他福利厚生"
        content={other}
      />
      <TraitListItem
        itemKey={COMPANY_TRAITS.CTX_WELFARE__ACHIEVEMENT.ID}
        itemName="実績のある制度"
        content={achievement}
      />
      <TraitListItem
        itemKey={TRAITS.PTX_WORKING_ENVIRONMENT.ID}
        itemName={workEnvironmentName}
        content={workEnvironmentFeatures}
      />
      {smokeFree}
    </TraitList>
  );
}

Welfare.propTypes = {
  positionImtRecord: PropTypes.object.isRequired,
  companyImtRecord: PropTypes.object.isRequired,
  smokeFreeMasterImtRecord: PropTypes.object,
  hasSmokeFreeValue: PropTypes.bool,
};

Welfare.defaultProps = {
  smokeFreeMasterImtRecord: null,
  hasSmokeFreeValue: false,
};

/**
 * 福利厚生欄の内容
 */
function renderWelfare(companyImtRecord, traitId) {
  const welfareImtMap = companyImtRecord?.get(traitId);

  // 設定値一覧
  const valueImtList = welfareImtMap?.get("ValueTexts");

  // 未入力の場合は非表示
  if (!valueImtList || !valueImtList.size) {
    return null;
  }

  // 「該当なし」が選択されている場合はそのRecordを取得
  const exceptionImtRecord = ImmutableListFinder.findById(
    valueImtList,
    EXCEPTION_HIDDEN_TRAIT_OPTION.MULTIPLE_TRAIT,
  );

  // オプション一覧
  const optionImtList = welfareImtMap?.get("Options");

  return (
    <ContentMultipleValueWithNote
      valueImtList={valueImtList}
      hasNotApplicable={Boolean(exceptionImtRecord)}
      notApplicableValue={EXCEPTION_HIDDEN_TRAIT_OPTION.MULTIPLE_TRAIT}
      optionImtList={optionImtList}
    />
  );
}

/**
 * 「労働環境の特徴」欄の内容
 */
function renderWorkEnvironmentFeatures(positionImtRecord) {
  // 「労働環境の特徴」
  const workEnvironmentMasterImtList = positionImtRecord.get(
    POSITION_DETAIL.WORK_ENVIRONMENT.ID,
  );

  // 求人特徴 「労働環境（ITエンジニア）」
  const itEngineerWorkEnvironmentImtRecord = positionImtRecord.get(
    POSITION_DETAIL.IT_ENGINEER_WORK_ENVIRONMENT.ID,
  );

  const itEngineerWorkEnvironmentMasterImtList =
    itEngineerWorkEnvironmentImtRecord?.get("IDs");

  if (
    !workEnvironmentMasterImtList?.size &&
    !itEngineerWorkEnvironmentMasterImtList?.size
  ) {
    return null;
  }

  // 「労働環境の特徴」と「労働環境（ITエンジニア）」をまとめて表示
  const displayMasterValueImtList = (workEnvironmentMasterImtList || List([]))
    .concat(itEngineerWorkEnvironmentMasterImtList || List([]))
    .filter((masterImtRecord) => {
      // 「該当なし」は表示しない
      return (
        masterImtRecord.get("ID") !==
        EXCEPTION_TRAIT_OPTION.PTX_WORKING_ENVIRONMENT
      );
    });

  // 値が存在しなければ描画しない
  // NOTE: 企業側で「該当なし」を選択した場合、他のチェック項目がクリアされるため、
  // 「労働環境の特徴」と「労働環境（ITエンジニア）」が両方「該当なし」の場合は、空配列
  if (!displayMasterValueImtList.size) {
    return null;
  }

  return (
    <ContentMultipleValueWithNote
      valueImtList={displayMasterValueImtList}
      hasNotApplicable={false}
    />
  );
}

/**
 * 「労働環境の特徴」欄の項目名
 */
function renderWorkEnvironmentName(traitImtRecord) {
  const noteText = traitImtRecord?.get("Note");
  // モーダルで表示する補足
  const noteModalBtn = noteText ? (
    <NoteModalBtn contentText={noteText} />
  ) : null;

  // [補足] ボタン横につけたラベル
  return (
    <>
      労働環境の特徴
      {noteModalBtn}
    </>
  );
}
