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
import { nl2br } from "@/utils/jsx";
import styles from "./ErrorModal.module.scss";

type DefaultProps = EmptyProps;

type Props = ClassComponentProps<
  DefaultProps,
  {
    isDisplay: boolean;
    hideModal: () => void;
    title?: string;
    message: string;
  }
>;

/**
 * エラーメッセージ表示用のモーダルコンポーネント
 */
export default class ErrorModal extends React.Component<Props> {
  static defaultProps: DefaultProps = {};

  componentWillUnmount() {
    // ブラウザバックなどで遷移した際にモーダルが残らないようにするため
    this.props.hideModal();
  }

  render() {
    const { isDisplay, hideModal, title = "エラー", message } = this.props;

    return (
      <Modal display={isDisplay}>
        <ModalLayout
          header={<ModalLayoutHeader title={title} onClose={hideModal} />}
          footer={
            <ModalLayoutFooter
              primaryBtn={
                <ModalLayoutButton
                  variant={MODAL_BTN_VARIANTS.BLUE_FILL}
                  onClick={hideModal}
                >
                  閉じる
                </ModalLayoutButton>
              }
            />
          }
        >
          <div className={styles["error-modal-contents"]}>
            <p className={styles["error-message"]}>{nl2br(message)}</p>
          </div>
        </ModalLayout>
      </Modal>
    );
  }
}
