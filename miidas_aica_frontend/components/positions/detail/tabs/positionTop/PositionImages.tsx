import React from "react";
import { List } from "immutable";

// 求人画像カルーセル
import PositionImageCarousel from "@/components/app/shared/positions/employee/PositionImageCarousel";
// import PositionNoImage from '@/components/app/shared/positions/employee/PositionNoImage';

import type PositionImageRecord from "@/models/position/records/PositionImage";
import styles from "./PositionImages.module.scss";

type Props = { positionImageImtList: List<PositionImageRecord> };

/**
 * ポジション画像（最大3枚）
 */
export default class PositionImages extends React.Component<Props> {
  /**
   * 複数枚の求人画像を返す
   */
  renderPositionMultipleImages() {
    return (
      <div className={styles.container}>
        <PositionImageCarousel
          positionImageImtList={this.props.positionImageImtList}
        />
      </div>
    );
  }

  /**
   * 単独の求人画像を返す
   */
  renderPositionSingleImage() {
    const url = this.props.positionImageImtList.get(0)?.URL;

    return (
      <div className={styles.container}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          className={styles.mainImage}
          src={url}
          alt="求人画像"
          draggable={false}
        />
      </div>
    );
  }

  render() {
    if (this.props.positionImageImtList.size >= 2) {
      return this.renderPositionMultipleImages();
    }

    if (this.props.positionImageImtList.size === 1) {
      return this.renderPositionSingleImage();
    }

    return null;
    // NOTE: #67013 準備中を適応できるようになったらコメントアウトを外す
    // return this.renderPositionNoImage();
  }
}
