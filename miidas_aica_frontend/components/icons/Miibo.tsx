import Image from "@/components/utils/Image";
import { Asset } from "@/constants/enum";

export default function Miibo() {
  return (
    <Image
      src={Asset.MIIBO}
      alt="ミイダス AI転職アドバイザー"
      height={50}
      width={50}
    />
  );
}
