from datetime import datetime

# 入退社に登録可能なのは60年前まで
CAREER_MIN_JOIN_RETIRE_YEARS = 60
# 卒業に登録可能なのは100年前まで
EDUCATION_MIN_GRADUATION_YEAR = 100


def get_current_year() -> int:
    """現在の年を取得（動的に計算）"""
    return datetime.now().year


def get_minimum_join_retire_year() -> int:
    """最小年を取得（現在年 - 60年）"""
    return get_current_year() - CAREER_MIN_JOIN_RETIRE_YEARS


def get_minimum_graduation_year() -> int:
    """最小年を取得（現在年 - 100年）"""
    return get_current_year() - EDUCATION_MIN_GRADUATION_YEAR
