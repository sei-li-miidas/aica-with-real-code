import PropTypes from "prop-types";

import { TRAITS } from "@/constants/business";
import { hasSomeTraitValues } from "@/helpers/positionDetail";

import ContentList from "@/components/positions/detail/parts/trait/ContentList";
import ContentListItem from "@/components/positions/detail/parts/trait/ContentListItem";
import TraitList from "@/components/positions/detail/parts/trait/TraitList";
import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";

import styles from "./BusinessScale.module.scss";

/**
 * 事業規模
 */
export default function BusinessScale({ businessImtRecord }) {
  // 事業の従業員数
  const employeeQty = renderBusinessScaleItem(
    businessImtRecord.get("EmployeeQty"),
  );
  // 事業の設立
  const establishmentYear = renderBusinessScaleItem(
    businessImtRecord.get("EstablishmentYear"),
  );
  // 事業の売上規模
  const salesScale = renderBusinessScaleItem(
    businessImtRecord.get("SalesScale"),
  );

  const items = [employeeQty, establishmentYear, salesScale];

  if (hasSomeTraitValues(items)) {
    return (
      <section className={styles.section}>
        <TraitList>
          <TraitListItem
            itemKey={TRAITS.BTX_EMPLOYEE_QTY.ID}
            itemName="事業の規模"
            content={employeeQty}
          />
          <TraitListItem
            itemKey={TRAITS.BTX_YEARS_OF_ESTABLISHMENT.ID}
            itemName="事業の設立"
            content={establishmentYear}
          />
          <TraitListItem
            itemKey={TRAITS.BTX_SALES_SCALE.ID}
            itemName="事業の売上規模"
            content={salesScale}
          />
        </TraitList>
      </section>
    );
  }

  return null;
}

BusinessScale.propTypes = {
  businessImtRecord: PropTypes.object.isRequired,
};

/**
 * 事業規模の項目をrenderするメソッド
 */
function renderBusinessScaleItem(traitImtRecord) {
  if (!traitImtRecord) return null;

  return (
    <ContentList>
      <ContentListItem traitImtRecord={traitImtRecord} />
    </ContentList>
  );
}
