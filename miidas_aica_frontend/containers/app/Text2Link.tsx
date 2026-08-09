import { type MFC } from "react";

import Text2LinkComponent from "@/components/utils/Text2Link";
import { useAppActions } from "@/hooks/useAppActions";

type Props = {
  text?: string;
  isNl2br?: boolean;
  isUrl2link?: boolean;
  isMail2link?: boolean;
  isPhone2link?: boolean;
};

const Text2Link: MFC<Props> = ({
  text = "",
  isNl2br = true,
  isUrl2link = true,
  isMail2link = true,
  isPhone2link = true,
}) => {
  const { showExternalLinkDialog } = useAppActions();

  return (
    <Text2LinkComponent
      text={text}
      nl2br={isNl2br}
      url2link={isUrl2link}
      mail2link={isMail2link}
      phone2link={isPhone2link}
      onClick={showExternalLinkDialog}
    />
  );
};

export default Text2Link;
