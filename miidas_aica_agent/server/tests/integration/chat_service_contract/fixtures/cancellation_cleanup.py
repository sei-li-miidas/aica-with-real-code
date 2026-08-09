"""
フィクスチャ: Cancellation cleanup 検証。

このフィクスチャが示すもの:
- 実行中の stream cancellation
- Idempotent な stream guard cleanup

Task-3 (security-cancellation-parity) の behavioral test が実際の検証を実装。
"""

# このフィクスチャは cancellation scenario と期待される cleanup 振る舞いを定義


def cancellation_cleanup_fixture():
    """Cancellation cleanup テストシナリオ用のフィクスチャファクトリー。"""
    return {
        "_description": "chat() generator cancellation removes stream-local detector state idempotently",
        "first_delta": "安全な最初のチャンクです。",
        "second_delta": "キャンセル後には消費されないチャンクです。",
        "expected_final_state": "detector_session_removed",
    }
