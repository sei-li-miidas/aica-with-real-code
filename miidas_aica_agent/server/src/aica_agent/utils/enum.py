from enum import IntEnum, StrEnum
import os


class PageName(StrEnum):
    CHAT = "Chat"
    POSITION_DETAIL = "PositionDetail"
    PROFILE_BASIC_INFO = "BasicInfo"
    PROFILE_CARRER = "Carrer"
    PROFILE_EDUCATION = "Education"
    PROFILE_WILL = "Will"


class HttpMethod(StrEnum):
    GET = "GET"
    POST = "POST"


class ComponentName(StrEnum):
    POSITION = "position"
    RECOMMENDATION = "recommendation"


class ProfileInputRequestPath(StrEnum):
    BASIC_INFO = "profile/basic"
    CARRER = "profile/carrer"
    EDUCATION = "profile/education"
    WILL = "profile/will"


class ApplyResult(IntEnum):
    UNKNOWN = -999
    INVALID_SESSION_STATUS = -10
    REGISTER_ALREADY = 10
    REGISTER_SUCCESS = 20
    REGISTER_FAIL = 30
    MEETING_APPLICATION_ALREADY = 40
    MEETING_APPLICATION_SUCCESS = 50
    MEETING_APPLICATION_FAIL = 60


class LLMMessageRole(StrEnum):
    DEVELOPER = "developer"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    HANDOFF = "handoff"
    REASONING = "reasoning"
    SYSTEM = "system"


class LocationType(StrEnum):
    RESIDENCE = "居住地"
    WORK_LOCATION = "希望勤務地"
    FULL_REMOTE = "フルリモート"


class FirstLanguage(IntEnum):
    """第一言語の選択肢"""

    MANDARIN = 1  # 北京語
    CANTONESE = 2  # 広東語
    KOREAN = 3  # 韓国・朝鮮語
    FRENCH = 4  # フランス語
    GERMAN = 5  # ドイツ語
    SPANISH = 6  # スペイン語
    THAI = 7  # タイ語
    INDONESIAN = 8  # インドネシア語
    ITALIAN = 9  # イタリア語
    RUSSIAN = 10  # ロシア語
    PORTUGUESE = 11  # ポルトガル語
    MALAYSIAN = 12  # マレーシア語
    VIETNAMESE = 13  # ベトナム語
    ARABIC = 14  # アラビア語
    TAGALOG = 15  # タガログ語
    TAIWANESE = 16  # 台湾語
    DUTCH = 17  # オランダ語
    SWEDISH = 18  # スウェーデン語
    HINDI = 19  # ヒンディー語
    JAPANESE = 91  # 日本語
    ENGLISH = 92  # 英語
    OTHER = 99  # その他


class DriverLicence(IntEnum):
    """運転免許証の有無"""

    NONE = 1  # なし
    AT_ONLY = 2  # あり（AT車限定）
    MT = 3  # あり（MT車）

    @classmethod
    def get_value(cls, value: int) -> dict:
        """運転免許証の日本語ラベルを取得"""
        if value == cls.NONE:
            return {"HasLicence": False, "IsFull": None}
        elif value == cls.AT_ONLY:
            return {"HasLicence": True, "IsFull": False}
        elif value == cls.MT:
            return {"HasLicence": True, "IsFull": True}
        else:
            raise ValueError(f"Invalid DriverLicence value: {value}")


class Gender(IntEnum):
    """性別"""

    MALE = 1  # 男性
    FEMALE = 2  # 女性


class Month(IntEnum):
    """月"""

    JANUARY = 1
    FEBRUARY = 2
    MARCH = 3
    APRIL = 4
    MAY = 5
    JUNE = 6
    JULY = 7
    AUGUST = 8
    SEPTEMBER = 9
    OCTOBER = 10
    NOVEMBER = 11
    DECEMBER = 12


class SchoolType(IntEnum):
    """学校種別"""

    GRADUATE_SCHOOL = 1  # 大学院
    UNIVERSITY = 2  # 大学
    JUNIOR_COLLEGE = 3  # 短期大学
    VOCATIONAL_SCHOOL = 4  # 専門学校
    TECHNICAL_COLLEGE = 5  # 高等専門学校
    HIGH_SCHOOL = 6  # 高等学校
    MIDDLE_SCHOOL = 7  # 中学校

    @classmethod
    def requires_department(cls, value: int) -> bool:
        """学部・学科の指定が必要かどうかを判定"""
        return cls(value) not in [
            cls.VOCATIONAL_SCHOOL,
            cls.HIGH_SCHOOL,
            cls.MIDDLE_SCHOOL,
        ]

    @classmethod
    def requires_category(cls, value: int) -> bool:
        """専門学校区分の指定が必要かどうかを判定"""
        return cls(value) == cls.VOCATIONAL_SCHOOL


class EnglishLevel(IntEnum):
    """英語レベル"""

    NONE = 1  # あてはまるものはない
    DAILY_CONVERSATION = 2  # 日常会話レベル
    BUSINESS_CONVERSATION = 3  # ビジネス会話レベル
    NATIVE = 4  # ネイティブレベル


class CompanyCount(IntEnum):
    """経験社数"""

    ZERO = 1  # 0社
    ONE = 2  # 1社
    TWO = 3  # 2社
    THREE = 4  # 3社
    FOUR = 5  # 4社
    FIVE = 6  # 5社
    SIX = 7  # 6社
    SEVEN = 8  # 7社
    EIGHT = 9  # 8社
    NINE = 10  # 9社
    TEN_OR_MORE = 11  # 10社以上


class ExperienceYears(IntEnum):
    """経験年数"""

    NONE = 1  # 経験なし
    LESS_THAN_1 = 2  # 1年未満
    ONE_OR_MORE = 3  # 1年以上
    TWO_OR_MORE = 4  # 2年以上
    THREE_OR_MORE = 5  # 3年以上
    FOUR_OR_MORE = 6  # 4年以上
    FIVE_OR_MORE = 7  # 5年以上
    SIX_OR_MORE = 8  # 6年以上
    SEVEN_OR_MORE = 9  # 7年以上
    EIGHT_OR_MORE = 10  # 8年以上
    NINE_OR_MORE = 11  # 9年以上
    TEN_OR_MORE = 12  # 10年以上

    @classmethod
    def has_experience(cls, value: int) -> bool:
        """経験があるかどうかを判定（経験なし以外）"""
        return cls(value) != cls.NONE

    @property
    def min_years(self) -> int:
        """経験最小年数を取得"""
        mapping = {
            self.NONE: 0,
            self.LESS_THAN_1: 0,
            self.ONE_OR_MORE: 1,
            self.TWO_OR_MORE: 2,
            self.THREE_OR_MORE: 3,
            self.FOUR_OR_MORE: 4,
            self.FIVE_OR_MORE: 5,
            self.SIX_OR_MORE: 6,
            self.SEVEN_OR_MORE: 7,
            self.EIGHT_OR_MORE: 8,
            self.NINE_OR_MORE: 9,
            self.TEN_OR_MORE: 10,
        }
        return mapping.get(self, 0)


class ManagementPeople(IntEnum):
    """マネジメント経験人数"""

    ONE_TO_FOUR = 1  # 1〜4人
    FIVE_TO_NINE = 2  # 5〜9人
    TEN_TO_TWENTY_NINE = 3  # 10〜29人
    THIRTY_TO_NINETY_NINE = 4  # 30〜99人
    HUNDRED_OR_MORE = 5  # 100人以上


class EmployeeSize(IntEnum):
    """企業規模"""

    LESS_THAN_10 = 1  # 10人未満
    TEN_TO_TWENTY_NINE = 2  # 10〜29人
    THIRTY_TO_NINETY_NINE = 3  # 30～99人
    HUNDRED_TO_TWO_NINETY_NINE = 4  # 100〜299人
    THREE_HUNDRED_TO_NINE_NINETY_NINE = 5  # 300〜999人
    THOUSAND_TO_TWO_NINE_NINETY_NINE = 6  # 1000〜2999人
    THREE_THOUSAND_OR_MORE = 7  # 3000人以上


class EmploymentType(IntEnum):
    """雇用形態"""

    REGULAR = 1  # 正社員
    CONTRACT = 2  # 契約社員
    EXECUTIVE_CONTRACT = 3  # 役員（任用契約）
    OUTSOURCING = 4  # 業務委託
    DISPATCH = 5  # 派遣社員
    PART_TIME = 6  # アルバイト


class EmploymentPost(IntEnum):
    """役職"""

    NO_POSITION = 1  # 役職なし
    LEADER = 2  # 係長／リーダークラス
    MANAGER = 3  # 課長／マネージャークラス
    GENERAL_MANAGER = 4  # 部長／ゼネラルマネージャークラス
    EXECUTIVE = 5  # 役員クラス
    PRESIDENT = 6  # 代表クラス


class JobChangePeriod(IntEnum):
    """転職希望時期"""

    WITHIN_1_MONTH = 1  # 1ヶ月以内
    WITHIN_3_MONTHS = 2  # 3ヶ月以内
    WITHIN_6_MONTHS = 3  # 6ヶ月以内
    WITHIN_1_YEAR = 4  # 1年以内
    MORE_THAN_1_YEAR = 5  # 1年よりも先
    NOT_CONSIDERING = 6  # 転職を考えていない


class EncryptKeyType(IntEnum):
    POSITION = 1
    PROFILE = 2

    def get_key(self) -> str:
        """暗号化キータイプに対応するキーを取得"""
        if self == self.POSITION:
            key = os.environ.get("AICA_PYTHON_FERNET_AES_128_CBC_KEY_LV3")
            key_name = "AICA_PYTHON_FERNET_AES_128_CBC_KEY_LV3"
        elif self == self.PROFILE:
            key = os.environ.get("AICA_PYTHON_FERNET_AES_128_CBC_KEY_LV5")
            key_name = "AICA_PYTHON_FERNET_AES_128_CBC_KEY_LV5"
        else:
            raise ValueError(f"Invalid EncryptKeyType value: {self}")
        if not key:
            raise ValueError(
                f"Environment variable '{key_name}' is not set or is empty."
            )
        return key


class RateLimitScope(StrEnum):
    SESSION = "session"
    IP = "ip"
    GUEST = "guest"


class RateLimitActionType(StrEnum):
    CHAT_REQUEST = "chat_request"
    POSITION_DETAIL = "position_detail"
    POSITION_SEARCH = "position_search"
    LOAD_MORE_POSITIONS = "load_more_positions"


# フック必要なツール名
class ToolName(StrEnum):
    # ポジション検索
    GENERIC_POSITION_SEARCH = "search_job_postings"
    IT_POSITION_SEARCH = "search_job_postings_for_it_engineer"
    FINANCIAL_SALES_POSITION_SEARCH = "search_job_postings_for_sales_financial_sales"
    # ポジション検索条件保存
    USER_PREFERENCE = "save_user_preference"
    # 応募
    APPLICATION = "form_application"
    # 登録
    REGISTRATION = "form_registration"
    # 職種検索（By キーワード）
    JOBTYPE_SEARCH_BY_KEYWORDS = "search_occupations_by_sentence"
    # 職種検索（By 性質）
    # 現在はワークフローで対応しているためツールとして存在しないが、チャット履歴の表示に必要なため残す
    JOBTYPE_SEARCH_BY_NATURE = "search_occupations_by_work_nature"
    # ワークフロー開始
    START_WORKFLOW = "start_workflow"

    @staticmethod
    def is_position_search_tool(tool_name: str) -> bool:
        return tool_name in (
            ToolName.GENERIC_POSITION_SEARCH,
            ToolName.IT_POSITION_SEARCH,
            ToolName.FINANCIAL_SALES_POSITION_SEARCH,
        )

    @staticmethod
    def is_chat_history_tool(tool_name: str) -> bool:
        return ToolName.is_position_search_tool(tool_name) or tool_name in (
            ToolName.JOBTYPE_SEARCH_BY_KEYWORDS,
            ToolName.JOBTYPE_SEARCH_BY_NATURE,
            ToolName.START_WORKFLOW,
        )
