import { type MFC } from "react";

import { TRAIT_OPTION_HELPS } from "@/constants/position";
import { TRAIT_OPTION_HELPS as COMPANY_TRAIT_OPTION_HELPS } from "@/constants/companies";

import HelpTooltip from "@/components/utils/HelpTooltip";

type Props = {
  traitId: keyof typeof TRAIT_OPTION_HELPS &
    keyof typeof COMPANY_TRAIT_OPTION_HELPS;
  traitValue: number | null;
};

/**
 * トレイト値のヘルプツールチップ
 */
const TraitHelpTooltip: MFC<Props> = ({ traitId, traitValue }) => {
  if (traitValue !== null && TRAIT_OPTION_HELPS[traitId]?.[traitValue]) {
    return <HelpTooltip help={TRAIT_OPTION_HELPS[traitId][traitValue]} />;
  }

  if (
    traitValue !== null &&
    COMPANY_TRAIT_OPTION_HELPS[traitId]?.[traitValue]
  ) {
    return (
      <HelpTooltip help={COMPANY_TRAIT_OPTION_HELPS[traitId][traitValue]} />
    );
  }

  return null;
};

export default TraitHelpTooltip;
