import PropTypes from "prop-types";

import { TRAITS } from "@/constants/companies";
import { READ_MORE_SECTION_OMITTED_HEIGHT } from "@/constants/position";
import { hasSomeTraitValues } from "@/helpers/positionDetail";

import Text2LinkWrapper from "@/components/positions/detail/parts/Text2LinkWrapper";
import SectionListItem from "@/components/positions/detail/parts/SectionListItem";
import ContentList from "@/components/positions/detail/parts/trait/ContentList";
import ContentListItem from "@/components/positions/detail/parts/trait/ContentListItem";
import TraitList from "@/components/positions/detail/parts/trait/TraitList";
import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";
import HelpTooltip from "@/components/utils/HelpTooltip";
import ReadMoreSection from "@/components/positions/detail/parts/ReadMoreSection";

/**
 * 「キャリア制度」
 */
export default function Career(props) {
  // 研修制度
  const trainingSystemExists = renderTrainingSystemExists(
    props.companyImtRecord,
  );

  // 研修内容
  const trainingSystemText = renderTrainingSystemText(props.companyImtRecord);

  // 社員の成長のための定期的な部署異動
  const jobRotationExists = renderJobRotationExists(props.companyImtRecord);

  // 異動希望
  const changeDepartmentRequest = renderChangeDepartmentRequest(
    props.companyImtRecord,
  );

  // 副業
  const sideBusiness = renderSideBusiness(props.companyImtRecord);

  const items = [
    trainingSystemExists,
    trainingSystemText,
    jobRotationExists,
    changeDepartmentRequest,
    sideBusiness,
  ];

  if (hasSomeTraitValues(items)) {
    // 社員の成長のための定期的な部署異動の項目名
    const jobRotationExistsName = renderJobRotationName();

    // 異動希望の項目名
    const changeDepartmentRequestName = renderChangeDepartmentRequestName();

    return (
      <SectionListItem title="キャリア制度">
        <ReadMoreSection
          omittedHeight={READ_MORE_SECTION_OMITTED_HEIGHT.CAREER}
          gaClassName="ga-PositionDetail_Career"
        >
          <TraitList>
            <TraitListItem
              itemKey={TRAITS.CTX_TRAINING_SYSTEM_EXISTS.ID}
              itemName="研修制度"
              content={trainingSystemExists}
            />
            <TraitListItem
              itemKey={TRAITS.CTX_TRAINING_SYSTEM_TEXT.ID}
              itemName="研修内容"
              content={trainingSystemText}
            />
            <TraitListItem
              itemKey={TRAITS.CTX_JOB_ROTATION_EXISTS.ID}
              itemName={jobRotationExistsName}
              content={jobRotationExists}
            />
            <TraitListItem
              itemKey={TRAITS.CTX_CHANGE_DEPARTMENT_REQUEST.ID}
              itemName={changeDepartmentRequestName}
              content={changeDepartmentRequest}
            />
            <TraitListItem
              itemKey={TRAITS.CTX_SIDE_BUSINESS.ID}
              itemName="副業"
              content={sideBusiness}
            />
          </TraitList>
        </ReadMoreSection>
      </SectionListItem>
    );
  }

  return null;
}

Career.propTypes = {
  companyImtRecord: PropTypes.object.isRequired,
};

/**
 * 「研修制度」欄の内容
 */
function renderTrainingSystemExists(companyImtRecord) {
  const trainingSystemExists = companyImtRecord.getIn([
    "TrainingSystem",
    "Exists",
  ]);
  if (!trainingSystemExists) {
    return null;
  }

  return "研修制度に自信あり";
}

/**
 * 「研修内容」欄の内容
 */
function renderTrainingSystemText(companyImtRecord) {
  const trainingSystemText = companyImtRecord.getIn(["TrainingSystem", "Text"]);
  if (!trainingSystemText) {
    return null;
  }

  return <Text2LinkWrapper text={trainingSystemText} />;
}

/**
 * 「社員の成長のための定期的な部署異動」欄の内容
 */
function renderJobRotationExists(companyImtRecord) {
  const jobRotationExistsImtMap = companyImtRecord.get("JobRotationExists");

  if (!jobRotationExistsImtMap) {
    return null;
  }

  return (
    <ContentList>
      <ContentListItem
        traitImtRecord={jobRotationExistsImtMap.get("Flg")}
        noteText={jobRotationExistsImtMap.get("Note")}
      />
    </ContentList>
  );
}

/**
 *  「社員の成長のための定期的な部署異動」欄の項目名
 */
function renderJobRotationName() {
  const helpTooltip = (
    <HelpTooltip help={TRAITS.CTX_JOB_ROTATION_EXISTS.Help} />
  );

  // ヘルプツールチップを横につけたラベル
  return (
    <>
      社員の成長のための定期的な部署異動
      <br />
      （ジョブローテーション）
      {helpTooltip}
    </>
  );
}

/**
 * 「異動希望」欄の内容
 */
function renderChangeDepartmentRequest(companyImtRecord) {
  const changeDepartmentRequestImtMap = companyImtRecord.get(
    "ChangeDepartmentRequest",
  );

  if (!changeDepartmentRequestImtMap) {
    return null;
  }

  const noteText = changeDepartmentRequestImtMap.get("Note");

  // 「申請できない」で、補足もない場合は表示しない
  if (!changeDepartmentRequestImtMap.getIn(["Flg", "On"]) && !noteText) {
    return null;
  }

  return (
    <ContentList>
      <ContentListItem
        traitImtRecord={changeDepartmentRequestImtMap.get("Flg")}
        noteText={changeDepartmentRequestImtMap.get("Note")}
      />
    </ContentList>
  );
}

/**
 *  「異動希望」欄の項目名
 */
function renderChangeDepartmentRequestName() {
  const helpTooltip = (
    <HelpTooltip help={TRAITS.CTX_CHANGE_DEPARTMENT_REQUEST.Help} />
  );

  // ヘルプツールチップを横につけたラベル
  return (
    <>
      異動希望
      {helpTooltip}
    </>
  );
}

/**
 * 「副業」欄の内容
 */
function renderSideBusiness(companyImtRecord) {
  // 副業
  const sideBusinessMasterImtRecord = companyImtRecord.get("SideBusiness");
  // 副業の条件
  const sideBusinessConditionText =
    companyImtRecord.get("SideBusinessCondition") || undefined;

  if (!sideBusinessMasterImtRecord) {
    return null;
  }

  return (
    <ContentList>
      <ContentListItem
        traitImtRecord={sideBusinessMasterImtRecord}
        noteText={sideBusinessConditionText}
      />
    </ContentList>
  );
}
