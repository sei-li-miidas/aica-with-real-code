import React from "react";

import Modal from "@/containers/utils/Modal";
import Image from "@/components/utils/Image";

import ModalLayout from "@/components/utils/modalLayout/ModalLayout";
import ModalLayoutHeader from "@/components/utils/modalLayout/ModalLayoutHeader";
import ModalLayoutFooter from "@/components/utils/modalLayout/ModalLayoutFooter";
import ModalLayoutButton from "@/components/utils/modalLayout/ModalLayoutButton";
import { MODAL_BTN_VARIANTS } from "@/constants/modal";
import {
  type EmptyProps,
  type ClassComponentProps,
} from "@/types/utility-types";
import styles from "./ModalBadgeDescription.module.scss";

type DefaultProps = EmptyProps;

type Props = ClassComponentProps<
  DefaultProps,
  {
    isDisplay: boolean;
    hideModal: () => void;
  }
>;

/**
 * はたらく人ファースト宣言の説明モーダルコンポーネント
 */
export default class ModalBadgeDescription extends React.Component<Props> {
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
              title="はたらく人ファースト宣言"
              onClose={this.props.hideModal}
            />
          }
          footer={
            <ModalLayoutFooter
              primaryBtn={
                <ModalLayoutButton
                  variant={MODAL_BTN_VARIANTS.BLUE_FILL}
                  onClick={this.props.hideModal}
                >
                  OK
                </ModalLayoutButton>
              }
            />
          }
        >
          <div className={styles["sh-ModalBadgeDescriptionContents"]}>
            <Image
              src="/assets/next/img/offers/img_hatarakuhito_first_badge.svg"
              alt="はたらく人ファースト宣言バッジ"
              width={212}
              height={103}
            />
            <p
              className={styles["sh-ModalHatarakuhitoFirstDescriptionTextarea"]}
            >
              <strong>はたらく人一人ひとりを大切にする企業</strong>
              の意思表示として、朝日新聞社と共に作った
              <strong>「はたらく人ファースト宣言」に賛同した企業</strong>
              であることを証明するものです。
            </p>
            <section
              className={styles["sh-ModalHatarakuhitoFirstDescriptionTextarea"]}
            >
              <h2>「はたらく人ファースト宣言」</h2>
              <ul
                className={styles["sh-ModalHatarakuhitoFirstDescriptionList"]}
              >
                <li>
                  はたらく人の多様なはたらきがいを尊重している、または今後尊重していく企業
                </li>
                <li>
                  はたらく人の声を聞く機会を設けている、または今後設けていく企業
                </li>
                <li>
                  はたらく人の声をもとに改善に努めている、または今後努めていく企業
                </li>
              </ul>
            </section>
          </div>
        </ModalLayout>
      </Modal>
    );
  }
}
