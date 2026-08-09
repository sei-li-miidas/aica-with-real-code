import HelpTooltipModal from "@/components/utils/HelpTooltipModal";
import { useModal } from "@/hooks/useModal";
import ModalWorkExperience from "@/components/positions/detail/tabs/modalWorkExperience/ModalWorkExperience";
import styles from "./WorkExperienceHeader.module.scss";

const WorkExperienceHeader = () => {
  const { showModal, hideModal, isDisplayModal } = useModal();

  return (
    <div className={styles.itemHeader}>
      <ModalWorkExperience
        isDisplayModal={isDisplayModal}
        hideModal={hideModal}
      />
      リアル職場体験
      <HelpTooltipModal showModal={showModal} />
    </div>
  );
};

export default WorkExperienceHeader;
