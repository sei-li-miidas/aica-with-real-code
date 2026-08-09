import { List } from "immutable";

import React, { type MFC } from "react";
// @ts-expect-error: No type definitions
import { Splide, SplideSlide } from "@splidejs/react-splide";
import "@splidejs/splide/dist/css/splide.min.css";

import type PositionImageRecord from "@/models/position/records/PositionImage";
import { MAX_POSITION_IMAGES_COUNT } from "@/constants/position";

import styles from "./PositionImageCarousel.module.scss";

type Props = { positionImageImtList: List<PositionImageRecord> };

const GAP_WIDTH = 7;
const BREAKPOINT_TABLET = 768;

// 求人画像のカルーセル
const PositionImageCarousel: MFC<Props> = ({ positionImageImtList }) => {
  const positionImages = renderPositionImages(positionImageImtList);

  // Note: Tabletでブレイクポイントを設定
  // SP(~767px)は、ページネーションありで1枚ごとにドラッグにより表示
  // Tablet（768px~1023px）、PC（1024px~）は、ページネーションなし、横幅最大3枚で収まるよう表示。

  return (
    <div className={styles.container}>
      {/* @see {@link https://splidejs.com/guides/options/} */}
      <Splide
        options={{
          gap: `${GAP_WIDTH}px`,
          arrows: false,
          classes: {
            pagination: `splide__pagination ${styles.pagination}`,
            page: `splide__pagination__page ${styles.page}`,
          },
          // PC、Tablet
          perPage: MAX_POSITION_IMAGES_COUNT,
          drag: false,
          pagination: false,
          // デフォルトではメディアクエリにmax-widthを指定
          breakpoints: {
            // SP
            [BREAKPOINT_TABLET - 1]: {
              fixedWidth: "90%",
              perPage: 1,
              drag: true,
              pagination: true,
            },
          },
        }}
      >
        {positionImages}
      </Splide>
    </div>
  );
};

function renderPositionImages(positionImageImtList: List<PositionImageRecord>) {
  return positionImageImtList.map((positionImageImtRecord, index) => {
    const id = index + 1;
    // TODO: ts EmployeeOffer TS化後、ts-expect-error/eslint-disable削除・get/getIn -> property accessor(dot notation/bracket notation)
    const url = positionImageImtRecord.get("URL");
    return (
      <SplideSlide key={id}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img className={styles.image} src={url} alt={`求人画像_${id}`} />
      </SplideSlide>
    );
  });
}

export default PositionImageCarousel;
