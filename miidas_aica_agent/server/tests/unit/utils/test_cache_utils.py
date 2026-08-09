import pytest

from utils.cache_utils import CacheUtil
from utils.log_utils import set_session_id, clear_session_id


def test_build_cache_key_and_reject_none():
    assert CacheUtil.build_cache_key("a", "b") == "a:b"
    # 空文字もそのままキーに含まれる
    assert CacheUtil.build_cache_key("a", "", "b") == "a::b"
    with pytest.raises(ValueError):
        CacheUtil.build_cache_key("a", None)


def test_build_cache_key_with_session_id():
    set_session_id("session123")
    try:
        assert CacheUtil.build_cache_key_with_session_id("x", "y") == "session123:x:y"
    finally:
        clear_session_id()
