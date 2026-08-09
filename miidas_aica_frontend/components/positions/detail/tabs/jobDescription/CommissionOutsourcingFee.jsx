import PropTypes from "prop-types";

import Text2LinkWrapper from "@/components/positions/detail/parts/Text2LinkWrapper";

import styles from "./CommissionOutsourcingFee.module.scss";

/**
 * 報酬（業務委託、完全歩合）
 */
export default function CommissionOutsourcingFee(props) {
  const commissionFee = props.positionImtRecord.getIn([
    "CommissionOutsourcing",
    "Fee",
  ]);

  return (
    <div className={styles.container}>
      <Text2LinkWrapper text={commissionFee} />
    </div>
  );
}

CommissionOutsourcingFee.propTypes = {
  positionImtRecord: PropTypes.object.isRequired,
};
