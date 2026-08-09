import { type ReactNode, type MouseEventHandler } from "react";
import Modal from "@/components/utils/Modal";
import ModalLayout from "@/components/utils/modalLayout/ModalLayout";
import ModalLayoutHeader from "@/components/utils/modalLayout/ModalLayoutHeader";
import ModalLayoutButton from "@/components/utils/modalLayout/ModalLayoutButton";
import ModalLayoutFooter from "@/components/utils/modalLayout/ModalLayoutFooter";
import { MODAL_BTN_VARIANTS } from "@/constants/modal";
import { CERTIFICATION_RANK } from "@/constants/companies";
import CertificationRankBadge from "./badges/CertificationRankBadge";
import styles from "./ModalCertification.module.scss";

type Props = {
  children?: ReactNode;
  display: boolean;
  onCloseBtnClick: MouseEventHandler<HTMLButtonElement>;
};

/**
 * ミイダス認定説明モーダルコンポーネント
 */
export default function ModalCertification({
  children = null,
  display,
  onCloseBtnClick,
}: Props) {
  if (!display) return null;
  return (
    <Modal display>
      <ModalLayout
        header={
          <ModalLayoutHeader
            title="ミイダス認定とは？"
            onClose={onCloseBtnClick}
          />
        }
        footer={
          <ModalLayoutFooter
            primaryBtn={
              <ModalLayoutButton
                variant={MODAL_BTN_VARIANTS.BLUE_FILL}
                onClick={onCloseBtnClick}
              >
                OK
              </ModalLayoutButton>
            }
          />
        }
      >
        <div className={styles.content}>
          <p className={styles.description}>
            ミイダスでは、
            <strong>入社後のミスマッチをなくすことが重要</strong>
            だと考えています。そこで、
            <strong>「より多くの情報を透明性高く公開している」</strong>
            <strong>
              「経験やスキルだけでなく、応募者の適性も考慮した採用を行なっている」
            </strong>
            などの基準をクリアした企業のポジションを認定し、BRONZE、SILVER、GOLDの三段階で表示しています。
          </p>
          <div className={styles.badge}>
            <CertificationRankBadge
              certificationRank={CERTIFICATION_RANK.BRONZE}
              width={106}
            />
          </div>
          <p className={styles.description}>
            企業情報や仕事詳細など、
            <strong>ミイダスの推奨する100項目以上がすべて入力されている</strong>
            ポジションです。豊富な情報をもとに応募を検討できます。
          </p>
          <div className={styles.badge}>
            <CertificationRankBadge
              certificationRank={CERTIFICATION_RANK.SILVER}
              width={106}
            />
          </div>
          <p className={styles.description}>
            <strong>自社社員にコンピテンシー診断を実施している</strong>
            企業のポジションです。自社で活躍する社員の特徴を把握した上で採用を行うことにより、入社後のミスマッチを防いでいます。
          </p>
          <div className={styles.badge}>
            <CertificationRankBadge
              certificationRank={CERTIFICATION_RANK.GOLD}
              width={106}
            />
          </div>
          <p className={styles.description}>
            <strong>BRONZE認定とSILVER認定の両方を取得した</strong>
            企業のポジションです。豊富な情報量とミスマッチを生まない採用体制で、ユーザーの効率的な転職活動に特に貢献している企業といえます。
          </p>
          <div className={styles.link}>
            <p className={styles.linkText}>
              ※なお登録されている企業情報等について、ミイダスでは詳細の確認やご質問へのお答えはできません。企業に直接お問い合わせください。
            </p>
            {children}
          </div>
        </div>
      </ModalLayout>
    </Modal>
  );
}
