import PropTypes from "prop-types";

import { TRAITS, EXCEPTION_HIDDEN_TRAIT_OPTION } from "@/constants/business";
import { READ_MORE_SECTION_OMITTED_HEIGHT } from "@/constants/position";
import { hasSomeTraitValues } from "@/helpers/positionDetail";
import { ImmutableListFinder } from "@/utils/finder";

import SectionListItem from "@/components/positions/detail/parts/SectionListItem";
import CollapsibleNote from "@/components/positions/detail/parts/CollapsibleNote";
import CollapsibleOptionList from "@/components/positions/detail/parts/CollapsibleOptionList";
import ContentHorizontalList from "@/components/positions/detail/parts/trait/ContentHorizontalList";
import ContentOptions from "@/components/positions/detail/parts/btiTrait/ContentOptions";
import TraitList from "@/components/positions/detail/parts/trait/TraitList";
import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";
import ReadMoreSection from "@/components/positions/detail/parts/ReadMoreSection";

import styles from "./BusinessSpecified.module.scss";

/**
 * 事業の詳細
 */
export default function BusinessSpecified(props) {
  // メーカー（メディカル系）得意領域
  const medicalAdvantageField = renderMedicalAdvantageFieldLabels(
    props.businessImtRecord.get("MedicalAdvantageField"),
  );

  // メーカー（自動車部品）Tier
  const carPartsTier = renderCarPartsTierLabels(
    props.businessImtRecord.get("CarPartsTier"),
  );

  // 請負会社の特徴
  const contractCompany = renderContractCompany(props.businessImtRecord);

  // システムインテグレーター
  const sier = renderSIer(props.businessImtRecord);

  const items = [medicalAdvantageField, carPartsTier, sier, contractCompany];

  if (hasSomeTraitValues(items)) {
    return (
      <SectionListItem title="事業の詳細">
        <ReadMoreSection
          omittedHeight={READ_MORE_SECTION_OMITTED_HEIGHT.BUSINESS_SPECIFIED}
          gaClassName="ga-PositionDetail_BusinessSpecified"
        >
          <TraitList>
            <TraitListItem
              itemKey={TRAITS.BTI_MEDICAL_ADVANTAGE_FIELD.ID}
              itemName="得意領域"
              content={medicalAdvantageField}
            />
            <TraitListItem
              itemKey={TRAITS.BTI_CAR_PARTS_TIER.ID}
              // inputのname用のeslintルールに引っかかるためeslint-disable
              // eslint-disable-next-line @miidas-company/miidas/name-attribute-is-snake-case
              itemName="Tier"
              content={carPartsTier}
            />
            <TraitListItem
              itemKey="bti_si"
              itemName="システムインテグレーター"
              content={sier}
            />
            <TraitListItem
              itemKey="bti_contract_company"
              itemName="請負会社の特徴"
              content={contractCompany}
            />
          </TraitList>
        </ReadMoreSection>
      </SectionListItem>
    );
  }

  return null;
}

BusinessSpecified.propTypes = {
  businessImtRecord: PropTypes.object.isRequired,
};

/**
 * bti_*** トレイトの見出し＆単一設定値を表示
 */
function renderBtiTraitSingleValue(
  traitId,
  traitName,
  btiSingleTraitImtRecord,
  notApplicableValue,
) {
  if (!btiSingleTraitImtRecord.get("ID")) return null;

  const isDisplayNA = btiSingleTraitImtRecord.get("ID") === notApplicableValue;
  const noteText = btiSingleTraitImtRecord.get("Note");

  // 「該当なし」かつ補足も無い場合は非表示
  if (isDisplayNA && !noteText) {
    return null;
  }

  // 設定値のラベル
  const label = btiSingleTraitImtRecord.get("Name");

  // 折りたたんで表示する補足
  const collapsibleNote = noteText ? (
    <CollapsibleNote contentText={noteText} />
  ) : null;

  // 「該当なし」の場合は、ラベルの下に全ての選択肢を折りたたみで表示
  const options = isDisplayNA ? (
    <ContentOptions
      optionImtList={btiSingleTraitImtRecord.get("Options")}
      notApplicableValue={notApplicableValue}
    />
  ) : null;

  // 設定値の下に補足を表示
  return (
    <li key={traitId}>
      <h6 className={styles.btiTitle}>{traitName}</h6>
      <span>
        {label}
        {collapsibleNote}
      </span>
      <CollapsibleOptionList content={options} />
    </li>
  );
}

/**
 * bti_*** トレイトの見出し＆複数設定値を表示
 */
function renderBtiTraitMultiValue(
  traitId,
  traitName,
  btiMultipleTraitImtRecord,
  notApplicableValue,
) {
  const isDisplayNA = ImmutableListFinder.findById(
    btiMultipleTraitImtRecord.get("IDs"),
    notApplicableValue,
  );
  const noteText = btiMultipleTraitImtRecord.get("Note");

  // 「該当なし」かつ補足も無い場合は非表示
  if (isDisplayNA && !noteText) {
    return null;
  }

  // 設定値のラベル（複数）
  const labels = btiMultipleTraitImtRecord.get("IDs").map((idImtRecord) => {
    const label = idImtRecord.get("Name");

    return <li key={label}>{label}</li>;
  });

  // 折りたたんで表示する補足
  const collapsibleNote = noteText ? (
    <CollapsibleNote contentText={noteText} />
  ) : null;

  // 「該当なし」の場合は、ラベルの下に全ての選択肢を折りたたみで表示
  const options = isDisplayNA ? (
    <ContentOptions
      optionImtList={btiMultipleTraitImtRecord.get("Options")}
      notApplicableValue={notApplicableValue}
    />
  ) : null;

  // 設定値の下に補足を表示
  return (
    <li key={traitId}>
      <h6 className={styles.btiTitle}>{traitName}</h6>
      <ContentHorizontalList>{labels}</ContentHorizontalList>
      {collapsibleNote}
      <CollapsibleOptionList content={options} />
    </li>
  );
}

/**
 * bti_*** トレイト用の見出し＆ラベル表示
 */
function renderBtiTrait(
  traitId,
  traitName,
  notApplicableValue,
  btiTraitImtRecord,
) {
  if (!btiTraitImtRecord) return null;

  const isMultiValue = Boolean(btiTraitImtRecord.get("IDs"));

  return isMultiValue
    ? renderBtiTraitMultiValue(
        traitId,
        traitName,
        btiTraitImtRecord,
        notApplicableValue,
      )
    : renderBtiTraitSingleValue(
        traitId,
        traitName,
        btiTraitImtRecord,
        notApplicableValue,
      );
}

/**
 * メーカー（メディカル系）得意領域 の設定値
 */
function renderMedicalAdvantageFieldLabels(medicalAdvantageFieldImtRecord) {
  if (!medicalAdvantageFieldImtRecord) return null;

  const isDisplayNA = ImmutableListFinder.findById(
    medicalAdvantageFieldImtRecord.get("IDs"),
    EXCEPTION_HIDDEN_TRAIT_OPTION.BTI_MEDICAL_ADVANTAGE_FIELD,
  );
  const noteText = medicalAdvantageFieldImtRecord.get("Note");

  // 「該当なし」かつ補足も無い場合は非表示
  if (isDisplayNA && !noteText) {
    return null;
  }

  // 「該当なし」の場合は、ラベルの下に全ての選択肢を折りたたみで表示
  const options = isDisplayNA ? (
    <ContentOptions
      optionImtList={medicalAdvantageFieldImtRecord.get("Options")}
      notApplicableValue={
        EXCEPTION_HIDDEN_TRAIT_OPTION.BTI_MEDICAL_ADVANTAGE_FIELD
      }
    />
  ) : null;

  // 設定値のラベル（複数）
  const labels = medicalAdvantageFieldImtRecord
    .get("IDs")
    .map((idImtRecord) => {
      const label = idImtRecord.get("Name");

      return <li key={label}>{label}</li>;
    });

  // 折りたたんで表示する補足
  const collapsibleNote = noteText ? (
    <CollapsibleNote contentText={noteText} />
  ) : null;

  // 設定値の下に補足を表示
  return (
    <>
      <ContentHorizontalList>{labels}</ContentHorizontalList>
      {collapsibleNote}
      <CollapsibleOptionList content={options} />
    </>
  );
}

/**
 * メーカー（自動車部品）Tier の設定値
 */
function renderCarPartsTierLabels(carPartsTierImtRecord) {
  if (!carPartsTierImtRecord) return null;

  const isDisplayNA =
    carPartsTierImtRecord.get("ID") ===
    EXCEPTION_HIDDEN_TRAIT_OPTION.BTI_CAR_PARTS_TIER;
  const noteText = carPartsTierImtRecord.get("Note");

  // 「該当なし」かつ補足も無い場合は非表示
  if (isDisplayNA && !noteText) {
    return null;
  }

  // 「該当なし」の場合は、ラベルの下に全ての選択肢を折りたたみで表示
  const options = isDisplayNA ? (
    <ContentOptions
      optionImtList={carPartsTierImtRecord.get("Options")}
      notApplicableValue={EXCEPTION_HIDDEN_TRAIT_OPTION.BTI_CAR_PARTS_TIER}
    />
  ) : null;

  // 折りたたんで表示する補足
  const collapsibleNote = noteText ? (
    <CollapsibleNote contentText={noteText} />
  ) : null;

  // 設定値の下に補足を表示
  return (
    <>
      {carPartsTierImtRecord.get("Name")}
      {collapsibleNote}
      <CollapsibleOptionList content={options} />
    </>
  );
}

/**
 * 請負会社の特徴
 */
function renderContractCompany(businessImtRecord) {
  // 主な収益源
  const profitSource = renderBtiTrait(
    TRAITS.BTI_CONTRACT_COMPANY__PROFIT_SOURCE.ID,
    TRAITS.BTI_CONTRACT_COMPANY__PROFIT_SOURCE.Name,
    EXCEPTION_HIDDEN_TRAIT_OPTION.BTI_CONTRACT_COMPANY__PROFIT_SOURCE,
    businessImtRecord.get("ContractCompanyProfitSource"),
  );

  // プロジェクト期間
  const projectTerm = renderBtiTrait(
    TRAITS.BTI_CONTRACT_COMPANY__PROJECT_TERM.ID,
    TRAITS.BTI_CONTRACT_COMPANY__PROJECT_TERM.Name,
    EXCEPTION_HIDDEN_TRAIT_OPTION.BTI_CONTRACT_COMPANY__PROJECT_TERM,
    businessImtRecord.get("ContractCompanyProjectTerm"),
  );

  // 客先常駐
  const clientResident = renderBtiTrait(
    TRAITS.BTI_CONTRACT_COMPANY__CLIENT_RESIDENT.ID,
    TRAITS.BTI_CONTRACT_COMPANY__CLIENT_RESIDENT.Name,
    EXCEPTION_HIDDEN_TRAIT_OPTION.BTI_CONTRACT_COMPANY__CLIENT_RESIDENT,
    businessImtRecord.get("ContractCompanyClientResident"),
  );

  // 常駐形態
  const residentType = renderBtiTrait(
    TRAITS.BTI_CONTRACT_COMPANY__RESIDENT_TYPE.ID,
    TRAITS.BTI_CONTRACT_COMPANY__RESIDENT_TYPE.Name,
    EXCEPTION_HIDDEN_TRAIT_OPTION.BTI_CONTRACT_COMPANY__RESIDENT_TYPE,
    businessImtRecord.get("ContractCompanyResident"),
  );

  const items = [profitSource, projectTerm, clientResident, residentType];

  if (hasSomeTraitValues(items)) {
    return (
      <ul className={styles.btiContentList}>
        {profitSource}
        {projectTerm}
        {clientResident}
        {residentType}
      </ul>
    );
  }

  return null;
}

/**
 * システムインテグレーター
 */
function renderSIer(businessImtRecord) {
  // SI種別
  const siType = renderBtiTrait(
    TRAITS.BTI_SI__TYPE.ID,
    TRAITS.BTI_SI__TYPE.Name,
    EXCEPTION_HIDDEN_TRAIT_OPTION.BTI_SI__TYPE,
    businessImtRecord.get("SIType"),
  );

  // 得意領域
  const siAdvantageIndustry = renderBtiTrait(
    TRAITS.BTI_SI__ADVANTAGE_INDUSTRY.ID,
    TRAITS.BTI_SI__ADVANTAGE_INDUSTRY.Name,
    EXCEPTION_HIDDEN_TRAIT_OPTION.BTI_SI__ADVANTAGE_INDUSTRY,
    businessImtRecord.get("SIAdvantageIndustry"),
  );

  const items = [siType, siAdvantageIndustry];

  if (hasSomeTraitValues(items)) {
    return (
      <ul className={styles.btiContentList}>
        {siType}
        {siAdvantageIndustry}
      </ul>
    );
  }

  return null;
}
