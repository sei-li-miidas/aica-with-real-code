import React from "react";
import ReactDOM from "react-dom";
import PropTypes from "prop-types";

// 汎用オーバーレイコンポーネント
import Overlay from "@/components/utils/Overlay";

import Text2LinkWrapper from "@/components/positions/detail/parts/Text2LinkWrapper";
import { clsx } from "@/utils/className";

import styles from "./ModalSupplementHalfView.module.scss";

/**
 * ModalSupplementHalfView
 * 補足情報モーダルコンポーネント
 */

export default class ModalSupplementHalfView extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      touchStartY: 0,
    };

    this.handleTouchStart = this.handleTouchStart.bind(this);
    this.handleTouchEnd = this.handleTouchEnd.bind(this);
    this.handleClose = this.handleClose.bind(this);
  }

  /**
   * handleTouchStart
   * スワイプを開始した時イベント
   */
  handleTouchStart(e) {
    this.setState({ touchStartY: e.touches[0].clientY });
  }

  /**
   * handleTouchEnd
   * スワイプを終了した時イベント
   */
  handleTouchEnd(e) {
    const touchEndY = e.changedTouches[0].clientY;

    // 下方向へスワイプされた場合はモーダルを閉じる
    if (touchEndY > this.state.touchStartY) {
      this.handleClose();
    }
  }

  /**
   * handleClose
   * モーダルを閉じる
   */
  handleClose() {
    this.props.onClose();
  }

  render() {
    const { isDisplay, content } = this.props;
    const body = content ? <Text2LinkWrapper text={content} /> : "";
    const wrapperCls = clsx(styles.wrapper, isDisplay && styles.show);

    return ReactDOM.createPortal(
      <div className={wrapperCls}>
        <Overlay isDisplay={isDisplay} onClick={this.handleClose}>
          <div className={styles.content}>
            <div
              className={styles.touchArea}
              onTouchStart={(e) => {
                return this.handleTouchStart(e);
              }}
              onTouchEnd={(e) => {
                return this.handleTouchEnd(e);
              }}
            />
            <div className={styles.scrollBlock}>
              {body}
              {this.props.children}
            </div>
            <button
              type="button"
              className={styles.btn}
              onClick={this.handleClose}
            >
              <span className={styles.btnText}>閉じる</span>
            </button>
          </div>
        </Overlay>
      </div>,
      document.body,
    );
  }
}

ModalSupplementHalfView.propTypes = {
  isDisplay: PropTypes.bool.isRequired,
  content: PropTypes.string,
  children: PropTypes.any,
  onClose: PropTypes.func.isRequired,
};

ModalSupplementHalfView.defaultProps = {
  content: "",
  children: undefined,
};
