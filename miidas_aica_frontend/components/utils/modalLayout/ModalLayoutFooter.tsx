import { type MFC, type ReactNode } from "react";
import styles from "./ModalLayoutFooter.module.scss";

type Props = {
  primaryBtn: ReactNode;
  secondaryBtn?: ReactNode;
  errorText?: string;
};

const ModalLayoutFooter: MFC<Props> = ({
  primaryBtn,
  secondaryBtn = null,
  errorText = "",
}) => {
  const errorTextContent = errorText && (
    <p className={styles.errorText}>{errorText}</p>
  );

  const singleButtonCls = !secondaryBtn && styles.single;

  const buttons = (
    <div className={`${styles.buttons} ${singleButtonCls}`}>
      {secondaryBtn}
      {primaryBtn}
    </div>
  );

  return (
    <footer className={styles.content}>
      {errorTextContent}
      {buttons}
    </footer>
  );
};

export default ModalLayoutFooter;
