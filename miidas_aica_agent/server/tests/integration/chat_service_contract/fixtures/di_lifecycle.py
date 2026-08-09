"""
フィクスチャ: DI lifecycle 検証。

このフィクスチャは chat service 解決の DI 振る舞いを説明:
- Container.chat_svc は websocket session ごとに fresh instance を解決
- legacy と real-refactored variant は lifecycle 境界を保護

Task-2 で characterization test に必要な具体的なシナリオデータを追加する。
"""

DI_LIFECYCLE_FIXTURE = {
    "variants": ["legacy", "real-refactored"],
    "expectation": "fresh-instance-per-session",
}
