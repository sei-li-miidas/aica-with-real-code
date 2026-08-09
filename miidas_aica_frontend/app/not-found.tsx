import React from "react";
import Link from "next/link";

const Custom404 = () => {
  return (
    <div>
      <h1>404 - ページが存在しません</h1>
      <p>このページは存在しません。アドレスを再度ご確認願います。</p>
      <p>
        ホームへ戻る場合は<Link href="/">こちら</Link>。
      </p>
    </div>
  );
};

export default Custom404;
