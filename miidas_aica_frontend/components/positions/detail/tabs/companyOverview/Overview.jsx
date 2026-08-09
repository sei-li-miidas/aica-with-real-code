import { List } from "immutable";
import PropTypes from "prop-types";
import { useState } from "react";

import { EXCEPTION_HIDDEN_TRAIT_OPTION, TRAITS } from "@/constants/companies";
import { POSITION_LABEL_DISPLAY_TYPE } from "@/constants/position";

import { ImmutableListFinder } from "@/utils/finder";
import { getModifiedLabel } from "@/helpers/traitLabel";

import ExternalLink from "@/containers/app/ExternalLink";
import TraitList from "@/components/positions/detail/parts/trait/TraitList";
import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";
import ContentList from "@/components/positions/detail/parts/trait/ContentList";
import ContentListItem from "@/components/positions/detail/parts/trait/ContentListItem";
import ContentMultipleValueWithNote from "@/components/positions/detail/parts/trait/ContentMultipleValueWithNote";
import ContentMultipleValueWithHelp from "@/components/positions/detail/parts/trait/ContentMultipleValueWithHelp";
import ContentListItemWithHelp from "@/components/positions/detail/parts/trait/ContentListItemWithHelp";
import ContentHorizontalList from "@/components/positions/detail/parts/trait/ContentHorizontalList";
import NoteModalBtn from "@/components/positions/detail/parts/NoteModalBtn";
import CollapsibleNote from "@/components/positions/detail/parts/CollapsibleNote";
import CollapsibleOptionList from "@/components/positions/detail/parts/CollapsibleOptionList";
import ReadMoreBox from "@/components/positions/detail/parts/ReadMoreBox";

import HelpTooltipModal from "@/components/utils/HelpTooltipModal";
import OriginalDocuments from "./OriginalDocuments";

import styles from "./Overview.module.scss";

/**
 * 企業の基本情報
 */
export default function Overview(props) {
  // 企業の基本情報の展開状態
  const [isExpanded, setIsExpanded] = useState(false);

  // 健康経営優良法人認定のヘルプボタンのタッチイベントを処理する
  const handleHPMCertificationHelpBtnTouch = () => {
    return props.showModalHPMCertificationDescription();
  };

  const companyName = renderCompanyName(props.companyImtRecord);

  const companyAddress = renderCompanyAddress(props.companyImtRecord);

  const employeeQty = renderEmployeeQty(props.companyImtRecord);

  const yearsOfEstablishment = renderYearsOfEstablishment(
    props.companyImtRecord,
  );

  const capitalTypeName = renderCapitalTypeName(props.companyImtRecord);
  const capitalTypeLabels = renderCapitalTypeLabels(props.companyImtRecord);

  const salesScale = renderSalesScale(props.companyImtRecord);

  // 常に表示する項目
  const displayList = (
    <>
      <TraitListItem
        itemKey="company_name"
        itemName="企業名"
        content={companyName}
      />
      {/* <TraitListItem
        itemKey="company_address"
        itemName="本社住所"
        content={companyAddress}
      />
      <TraitListItem
        itemKey={TRAITS.CTX_EMPLOYEE_QTY.ID}
        itemName="企業規模"
        content={employeeQty}
      />
      <TraitListItem
        itemKey={TRAITS.CTX_YEARS_OF_ESTABLISHMENT.ID}
        itemName="設立"
        content={yearsOfEstablishment}
      />
      <TraitListItem
        itemKey={TRAITS.CTX_CAPITAL_TYPE.ID}
        itemName={capitalTypeName}
        content={capitalTypeLabels}
      />
      <TraitListItem
        itemKey={TRAITS.CTX_SALES_SCALE.ID}
        itemName="売上規模"
        content={salesScale}
      /> */}
    </>
  );

  const website = renderWebsite(props.companyImtRecord);

  const appealPointName = renderAppealPointName(props.companyImtRecord);
  const appealPointLabels = renderAppealPointLabels(
    props.companyImtRecord,
    handleHPMCertificationHelpBtnTouch,
  );

  const otherName = renderOtherName(props.companyImtRecord);
  const otherLabels = renderOtherLabels(props.companyImtRecord);

  const originalDocuments = renderOriginalDocuments(
    props.positionImtRecord,
    props.companyImtRecord,
  );

  // 「続きを読む」ボタンを押下した際に表示する項目
  const displayListWithExpanded = isExpanded ? (
    <>
      {/* <TraitListItem
        itemKey={TRAITS.CTX_PRESIDENT_NAME.ID}
        itemName="代表者"
        content={props.companyImtRecord?.get("PresidentName")}
      /> */}
      <TraitListItem
        itemKey={TRAITS.CTX_WEBSITE.ID}
        // inputのname用のeslintルールに引っかかるためeslint-disable
        // eslint-disable-next-line @miidas-company/miidas/name-attribute-is-snake-case
        itemName="企業サイトURL"
        content={website}
      />
      <TraitListItem
        itemKey={TRAITS.CTX_APPEAL_POINT.ID}
        itemName={appealPointName}
        content={appealPointLabels}
      />
      {/* <TraitListItem
        itemKey={TRAITS.CTX_OTHER.ID}
        itemName={otherName}
        content={otherLabels}
      />
      <TraitListItem
        itemKey="original_documents"
        itemName="オリジナル資料"
        content={originalDocuments}
      /> */}
    </>
  ) : null;

  return (
    <ReadMoreBox isExpanded={isExpanded} setIsExpanded={setIsExpanded}>
      <TraitList>
        {displayList}
        {displayListWithExpanded}
      </TraitList>
    </ReadMoreBox>
  );
}

Overview.propTypes = {
  positionImtRecord: PropTypes.object.isRequired,
  companyImtRecord: PropTypes.object.isRequired,
};

/**
 * 法人種別のラベル表示
 */
function renderCompanyType(companyImtRecord) {
  const value = companyImtRecord?.getIn(["ProfitCompany", "ID"]);

  // トレイト値がないか、「営利団体」の場合は描画しない
  if (!value || value === EXCEPTION_HIDDEN_TRAIT_OPTION.CTX_IS_PROFIT_COMPANY) {
    return null;
  }

  const label = companyImtRecord.getIn(["ProfitCompany", "Name"]);
  const noteText = companyImtRecord.getIn(["ProfitCompany", "Note"]);
  const note = noteText ? (
    <li>
      <CollapsibleNote contentText={noteText} />
    </li>
  ) : null;

  return (
    <>
      <li>{`[${label}]`}</li>
      {note}
    </>
  );
}

/**
 * 「企業名」のラベル表示
 */
function renderCompanyName(companyImtRecord) {
  const companyType = renderCompanyType(companyImtRecord);

  return (
    <ContentList>
      {companyType}
      <li>{companyImtRecord?.get("Name")}</li>
    </ContentList>
  );
}

/**
 * 「本社住所」のラベル表示
 */
function renderCompanyAddress(companyImtRecord) {
  const address = companyImtRecord?.get("Address")
    ? companyImtRecord.getAddressForDisplay()
    : null;

  if (!address) {
    return null;
  }

  return address;
}

/**
 * 「企業規模」のラベル表示
 */
function renderEmployeeQty(companyImtRecord) {
  const masterImtRecord = companyImtRecord?.get("EmployeeQty");

  if (!masterImtRecord) {
    return null;
  }

  return (
    <ContentList>
      <ContentListItem traitImtRecord={masterImtRecord} />
    </ContentList>
  );
}

/**
 * 「設立」のラベル表示
 */
function renderYearsOfEstablishment(companyImtRecord) {
  const masterImtRecord = companyImtRecord?.get("EstablishmentYear");

  if (!masterImtRecord) {
    return null;
  }

  return (
    <ContentList>
      <ContentListItem traitImtRecord={masterImtRecord} />
    </ContentList>
  );
}

/**
 * 「資本区分」の見出し表示
 */
function renderCapitalTypeName(companyImtRecord) {
  const noteText = companyImtRecord?.getIn(["CapitalType", "Note"]);

  // モーダルで表示する補足
  const noteModalBtn = noteText ? (
    <NoteModalBtn contentText={noteText} />
  ) : null;

  // [補足] ボタンを横につけたラベル
  return (
    <>
      資本区分
      {noteModalBtn}
    </>
  );
}

/**
 * 「資本区分」のラベル表示
 */
function renderCapitalTypeLabels(companyImtRecord) {
  const traitImtRecord = companyImtRecord.get("CapitalType");

  // 「資本区分」の設定値一覧
  const valueImtList = traitImtRecord?.get("IDs");

  // 未入力の場合は非表示
  if (!valueImtList || !valueImtList.size) {
    return null;
  }

  // 「該当なし」が選択されている場合はそのRecordを取得
  const exceptionImtRecord = ImmutableListFinder.findById(
    valueImtList,
    EXCEPTION_HIDDEN_TRAIT_OPTION.MULTIPLE_TRAIT,
  );

  // 「該当なし」が選択されている、かつ補足も無い場合は非表示
  if (exceptionImtRecord && !traitImtRecord.get("Note")) {
    return null;
  }

  // 「資本区分」のオプション一覧
  const optionImtList = traitImtRecord?.get("Options");

  return (
    <ContentMultipleValueWithHelp
      traitId={TRAITS.CTX_CAPITAL_TYPE.ID}
      valueImtList={valueImtList}
      hasNotApplicable={Boolean(exceptionImtRecord)}
      notApplicableValue={EXCEPTION_HIDDEN_TRAIT_OPTION.MULTIPLE_TRAIT}
      optionImtList={optionImtList}
    />
  );
}

/**
 * 「売上規模」
 */
function renderSalesScale(companyImtRecord) {
  // 売上規模
  const salesScaleMasterImtRecord = companyImtRecord?.get("SalesScale");

  const salesScale = salesScaleMasterImtRecord ? (
    <ContentListItem traitImtRecord={salesScaleMasterImtRecord} />
  ) : null;

  // 海外売上比率
  const salesOverseasRateMasterImtRecord =
    companyImtRecord?.get("SalesOverseasRate");

  const labelModifier = () => {
    return getModifiedLabel(
      TRAITS.CTX_SALES_OVERSEAS_RATE.ID,
      salesOverseasRateMasterImtRecord,
      POSITION_LABEL_DISPLAY_TYPE.DETAIL,
    );
  };

  //  設定値ありかつ海外売上比率が10%以上の場合は表示
  const salesOverseasRate =
    salesOverseasRateMasterImtRecord &&
    !EXCEPTION_HIDDEN_TRAIT_OPTION.CTX_SALES_OVERSEAS_RATE.includes(
      salesOverseasRateMasterImtRecord.get("ID"),
    ) ? (
      <ContentListItem
        traitImtRecord={salesOverseasRateMasterImtRecord}
        labelModifier={labelModifier}
      />
    ) : null;

  return (
    <ContentList>
      {salesScale}
      {salesOverseasRate}
    </ContentList>
  );
}

/**
 * 企業サイトURL
 */
function renderWebsite(companyImtRecord) {
  const websiteUrl = companyImtRecord?.get("Website");

  // 空文字で返ってくる場合は項目を非表示にする
  // #15297 必須項目だけどURL形式が不正な場合は空文字
  if (!websiteUrl) {
    return null;
  }

  return (
    <div className={styles.link}>
      <ExternalLink url={websiteUrl}>{websiteUrl}</ExternalLink>
    </div>
  );
}

/**
 * 「当社のアピールポイント」の見出し
 */
function renderAppealPointName(companyImtRecord) {
  const noteText = companyImtRecord?.getIn(["AppealPoint", "Note"]);

  // モーダルで表示する補足
  const noteModalBtn = noteText ? (
    <NoteModalBtn contentText={noteText} />
  ) : null;

  // [補足] ボタンを横につけたラベル
  return (
    <>
      当社のアピールポイント
      {noteModalBtn}
    </>
  );
}

/**
 * 「当社のアピールポイント」のラベル表示
 */
function renderAppealPointLabels(
  companyImtRecord,
  handleHPMCertificationHelpBtnTouch,
) {
  const traitImtRecord = companyImtRecord?.get("AppealPoint");

  // 「当社のアピールポイント」の設定値一覧
  const valueImtList = traitImtRecord?.get("IDs") || List([]);

  // 未入力の場合は非表示
  if (!valueImtList.size) {
    return null;
  }

  // 「該当なし」が選択されている場合はそのRecordを取得
  const exceptionImtRecord = ImmutableListFinder.findById(
    valueImtList,
    EXCEPTION_HIDDEN_TRAIT_OPTION.MULTIPLE_TRAIT,
  );
  // 健康経営優良法人認定されているかどうか
  const isHpmCertified = Boolean(
    companyImtRecord?.get("HPMCertificationDisplayYear"),
  );
  // 「該当なし」が選択されている、かつ健康経営認定もされていない場合は、表示が「該当なし」になる
  const isDisplayNA = exceptionImtRecord && !isHpmCertified;

  // 表示が「該当なし」になる、かつ補足も無い場合
  if (isDisplayNA && !traitImtRecord?.get("Note")) {
    // 欄ごと非表示
    return null;
  }

  // 設定値のラベルのリストを生成
  let values = valueImtList.map((masterImtRecord) => {
    return (
      <ContentListItemWithHelp
        key={masterImtRecord.get("Name")}
        traitId={TRAITS.CTX_APPEAL_POINT.ID}
        traitImtRecord={masterImtRecord}
      />
    );
  });

  // 健康経営優良法人認定されている場合は、「健康経営優良法人認定」を設定されている値の1つとして扱う
  if (isHpmCertified) {
    const hpmCertificated = (
      <li key="hpm_certification" className={styles.hpmLabel}>
        健康経営優良法人認定
        <HelpTooltipModal showModal={handleHPMCertificationHelpBtnTouch} />
      </li>
    );

    if (exceptionImtRecord) {
      // 「該当なし」が設定されている場合は、「該当なし」では無く健康経営認定が1つの選択肢として選択されているように扱う
      values = List([hpmCertificated]);
    } else {
      // 設定値がある場合は、健康経営認定も選択されているように扱う
      values = values.push(hpmCertificated);
    }
  }

  // ラベルを横並べにする
  const valueList = <ContentHorizontalList>{values}</ContentHorizontalList>;

  let collapsibleOptionList = null;

  // 表示上が「該当なし」になる場合
  if (isDisplayNA) {
    // 「当社のアピールポイント」のオプション一覧
    const optionImtList = traitImtRecord?.get("Options") || List([]);

    // オプション一覧のラベルのリストを生成
    const options = optionImtList
      .filter((masterImtRecord) => {
        // 「該当なし」は除外
        return (
          masterImtRecord.get("ID") !==
          EXCEPTION_HIDDEN_TRAIT_OPTION.MULTIPLE_TRAIT
        );
      })
      .map((masterImtRecord) => {
        return (
          <ContentListItemWithHelp
            key={masterImtRecord.get("Name")}
            traitId={TRAITS.CTX_APPEAL_POINT.ID}
            traitImtRecord={masterImtRecord}
          />
        );
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
}

/**
 * 「その他企業特徴」の見出し表示
 */
function renderOtherName(companyImtRecord) {
  const noteText = companyImtRecord?.getIn(["Other", "Note"]);

  // モーダルで表示する補足
  const noteModalBtn = noteText ? (
    <NoteModalBtn contentText={noteText} />
  ) : null;

  // [補足] ボタンを横につけたラベル
  return (
    <>
      その他企業特徴
      {noteModalBtn}
    </>
  );
}

/**
 * 「その他企業特徴」のラベル表示
 */
function renderOtherLabels(companyImtRecord) {
  const otherImtMap = companyImtRecord?.get("Other");

  // 「その他企業特徴」の設定値一覧
  const valueImtList = otherImtMap?.get("IDs");

  // 未入力の場合は非表示
  if (!valueImtList || !valueImtList.size) {
    return null;
  }

  // 「なし」が選択されている場合はそのRecordを取得
  const exceptionImtRecord = ImmutableListFinder.findById(
    valueImtList,
    EXCEPTION_HIDDEN_TRAIT_OPTION.MULTIPLE_TRAIT,
  );

  // 「その他企業特徴」のオプション一覧
  const optionImtList = otherImtMap?.get("Options");

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
 * オリジナル資料
 */
function renderOriginalDocuments(positionImtRecord, companyImtRecord) {
  const originalDocumentImtList = companyImtRecord?.get("OriginalDocuments");

  if (!originalDocumentImtList?.size) {
    return null;
  }

  return (
    <div className={styles.link}>
      <OriginalDocuments
        positionId={positionImtRecord?.get("ID")}
        companyId={companyImtRecord?.get("ID")}
        originalDocumentImtList={originalDocumentImtList}
      />
    </div>
  );
}
