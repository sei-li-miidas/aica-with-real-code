import React from "react";
import Modal from "@/containers/utils/Modal";
import ModalLayout from "@/components/utils/modalLayout/ModalLayout";
import ModalLayoutHeader from "@/components/utils/modalLayout/ModalLayoutHeader";
import ModalLayoutFooter from "@/components/utils/modalLayout/ModalLayoutFooter";
import ModalLayoutButton from "@/components/utils/modalLayout/ModalLayoutButton";
import { MODAL_BTN_VARIANTS } from "@/constants/modal";
import {
  type EmptyProps,
  type ClassComponentProps,
} from "@/types/utility-types";
import styles from "./ModalHPMCertificationDescription.module.scss";

type DefaultProps = EmptyProps;

type Props = ClassComponentProps<
  DefaultProps,
  {
    isDisplay: boolean;
    hideModal: () => void;
  }
>;

/**
 * 健康経営優良法人認定の説明モーダルコンポーネント
 */
export default class ModalHPMCertificationDescription extends React.Component<Props> {
  static defaultProps: DefaultProps = {};

  componentWillUnmount() {
    // ブラウザバックなどで遷移した際にモーダルが残らないようにするため
    this.props.hideModal();
  }

  render() {
    return (
      <Modal display={this.props.isDisplay}>
        <ModalLayout
          header={
            <ModalLayoutHeader
              title="健康経営優良法人認定制度"
              onClose={this.props.hideModal}
            />
          }
          footer={
            <ModalLayoutFooter
              primaryBtn={
                <ModalLayoutButton
                  variant={MODAL_BTN_VARIANTS.GRAY_FILL}
                  onClick={this.props.hideModal}
                >
                  閉じる
                </ModalLayoutButton>
              }
            />
          }
        >
          <div className={styles.contents}>
            <p>
              経済産業省により2016年に創設された制度で、
              <strong>優良な健康経営を実践している企業を認定するもの</strong>
              です。
              <br />
              この認定を取得している企業は、
              <strong>従業員の健康を大切にしている企業</strong>
              として、経済産業省から認められています。
            </p>
          </div>
        </ModalLayout>
      </Modal>
    );
  }
}
