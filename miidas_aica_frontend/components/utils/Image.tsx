import { type MFC, type ComponentPropsWithoutRef } from "react";

type Props = ComponentPropsWithoutRef<"img"> & {
  src: string;
  alt: string;
};

/**
 * Image
 * 汎用Imageコンポーネント
 * imgタグのsrcにNEXT_PUBLIC_ASSET_PATHを追加した形で返す
 */
const Image: MFC<Props> = ({ src, alt, srcSet, ...rest }) => {
  // srcSetがある場合、srcSetにもNEXT_PUBLIC_ASSET_PATHを追加する
  const handleCDNPathAddedSrcSet = () => {
    if (srcSet) {
      const splittedSrcSets = srcSet.split(",");
      const cdnPathAddedSrcSet = splittedSrcSets
        .map((splittedSrcSet) => {
          return process.env.NEXT_PUBLIC_ASSET_PATH + splittedSrcSet.trim();
        })
        .join(", ");
      return cdnPathAddedSrcSet;
    }

    return undefined;
  };

  const cdnPathAddedSrcSet = handleCDNPathAddedSrcSet();

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={`${process.env.NEXT_PUBLIC_ASSET_PATH}${src}`}
      alt={alt}
      srcSet={cdnPathAddedSrcSet}
      {...rest}
    />
  );
};

export default Image;
