from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from database import Base
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
    field_validator,
)
from datetime import datetime

from utils.const import PHONE_PATTERN, PASSWORD_PATTERN
from utils.enum import (
    CompanyCount,
    DriverLicence,
    EmployeeSize,
    EmploymentPost,
    EmploymentType,
    EnglishLevel,
    ExperienceYears,
    FirstLanguage,
    Gender,
    JobChangePeriod,
    LocationType,
    ManagementPeople,
    Month,
    SchoolType,
)
from utils.time_utils import (
    get_current_year,
    get_minimum_graduation_year,
    get_minimum_join_retire_year,
)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.session_id"))
    user_name = Column(String, nullable=True)
    user_purpose = Column(String, nullable=True)
    interest_tendency = Column(String, nullable=True)
    job_search_motivation = Column(String, nullable=True)
    current_job_experience_years = Column(Integer, nullable=True)
    current_job_description = Column(String, nullable=True)
    job_feedback_positive = Column(ARRAY(String), nullable=True)
    job_feedback_negative = Column(ARRAY(String), nullable=True)
    miidas_registration_user_data: Mapped[JSONB] = mapped_column(JSONB, nullable=True)
    deleted_at = Column(DateTime, nullable=True)


class IDNameModel(BaseModel):
    id: int = Field(..., alias="ID")
    name: str = Field(..., alias="Name")


class AddressModel(BaseModel):
    prefecture: IDNameModel
    city: IDNameModel


class BaseJSONModel(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def convert_empty_str_to_none(cls, v):
        """Convert empty string values to None for all fields"""
        if v == "":
            return None
        return v


class BaseJSONUserProfile(BaseJSONModel):
    pass


class JSONUserProfileBasicInfo(BaseJSONUserProfile):
    """
    ユーザーの基本的なプロフィールモデル
    DBに保存時はUserProfileのmiidas_registration_user_dataにJSONとして格納される
    """

    gender: Gender = Field(...)  # 性別
    last_name: str = Field(..., max_length=50, alias="lastName")
    first_name: str = Field(..., max_length=50, alias="firstName")
    last_name_kana: str = Field(..., max_length=50, alias="lastNameKana")
    first_name_kana: str = Field(..., max_length=50, alias="firstNameKana")
    birth_year: int = Field(..., alias="birthYear")
    birth_month: Month = Field(..., alias="birthMonth")
    # フロントエンドがチェック成功して、バックエンドが失敗したらややこしいので
    # バックエンドはEmailStrを利用するだけとします。
    # あとはメアドチェックはフロントエンドと会員登録APIに任せます。
    email: EmailStr = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=16)
    phone_no: str = Field(..., min_length=10, max_length=11, alias="phoneNo")
    prefecture: IDNameModel
    city: IDNameModel
    first_language: FirstLanguage = Field(..., alias="firstLanguage")  # 第一言語
    driver_licence: DriverLicence = Field(
        ..., alias="driverLicence"
    )  # 運転免許証の有無

    @field_validator("phone_no")
    @classmethod
    def validate_phone_no(cls, v):
        """
        電話番号の妥当性検証
        0で始まる10桁または11桁の数字
        """
        if not PHONE_PATTERN.match(v):
            raise ValueError("有効な電話番号を入力してください（ハイフンなし）")
        return v

    @field_validator("birth_year")
    @classmethod
    def validate_birth_year(cls, v):
        """
        誕生日の年の妥当性検証
        """
        current_year = datetime.now().year
        if v < current_year - 100:
            raise ValueError(f"{current_year - 100}以降の年を入力してください")
        if v > current_year - 15:
            raise ValueError(f"{current_year - 15}までの年を入力してください")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """
        パスワードの妥当性検証
        英数字を含む8-16文字
        """
        if not PASSWORD_PATTERN.match(v):
            raise ValueError("パスワードは英字と数字を含む8-16文字である必要があります")
        return v


class JSONUserProfileEducation(BaseJSONUserProfile):
    """
    ユーザーの学歴モデル。
    DBに保存時はUserProfileのmiidas_registration_user_dataにJSONとして格納される
    """

    school_type: SchoolType = Field(
        ...,
        alias="schoolType",
    )  # 学校種別
    graduation_year: int = Field(
        ...,
        alias="graduationYear",
    )  # 卒業年: 1940年から現在の年まで
    english_level: EnglishLevel = Field(
        ...,
        alias="englishLevel",
    )  # 英語レベル
    school_name: str | None = Field(
        None,
        max_length=200,
        alias="schoolName",
    )
    department: IDNameModel | None = Field(
        None,
        alias="department",
    )
    professional_training_college_category: IDNameModel = Field(
        ...,
        alias="professionalTrainingCollegeCategory",
    )

    @field_validator("graduation_year")
    @classmethod
    def validate_graduation_year(cls, v):
        """卒業年の妥当性検証"""
        current_year = get_current_year()
        minimum_year = get_minimum_graduation_year()
        if v < minimum_year:
            raise ValueError(f"{minimum_year}以降の年を入力してください")
        if v > current_year:
            raise ValueError(f"{current_year}までの年を入力してください")
        return v

    @model_validator(mode="after")
    def conditional_validation(self):
        """
        条件付きバリデーション
        """
        # school_typeが専門学校、高等学校、中学校以外の場合、school_nameとdepartmentが必須
        if SchoolType.requires_department(self.school_type):
            if not self.school_name or self.school_name.strip() == "":
                raise ValueError("学校名は必須です")
            if self.department is None or self.department.id is None:
                raise ValueError("学部・学科は必須です")

        # school_typeが専門学校の場合、professional_training_college_categoryが必須
        if self.school_type == SchoolType.VOCATIONAL_SCHOOL:
            if (
                self.professional_training_college_category is None
                or self.professional_training_college_category.id is None
            ):
                raise ValueError("専門学校カテゴリは必須です")

        return self


class JSONUserProfileCarrer(BaseJSONUserProfile):
    """
    ユーザーの経歴モデル。
    DBに保存時はUserProfileのmiidas_registration_user_dataにJSONとして格納される
    """

    exp_company_num: CompanyCount = Field(
        ...,
        alias="expCompanyNum",
    )  # 経験社数
    management_exp_term: ExperienceYears = Field(
        ...,
        alias="managementExpTerm",
    )  # 今までのマネジメント経験年数
    management_people_num: ManagementPeople | None = Field(
        None,
        alias="managementPeopleNum",
    )  # 今までのマネジメント経験人数
    company_name: str | None = Field(
        None,
        max_length=255,
        alias="companyName",
    )  # 企業名
    industry_small_id: IDNameModel | None = Field(
        None,
        alias="industrySmallID",
    )  # 業種
    employee_num: EmployeeSize | None = Field(
        None,
        alias="employeeNum",
    )  # 企業規模
    employment_type: EmploymentType | None = Field(
        None,
        alias="employmentType",
    )  # 直近企業の雇用形態
    employment_post: EmploymentPost | None = Field(
        None,
        alias="employmentPost",
    )  # 直近企業の役職
    job_type_small_id: IDNameModel | None = Field(
        None,
        alias="jobTypeSmallID",
    )  # 職種
    job_type_exp_term: ExperienceYears | None = Field(
        None,
        alias="jobTypeExpTerm",
    )  # 経験職種の経験年数（直近の企業のみ）
    all_career_job_type_exp_term: ExperienceYears | None = Field(
        None,
        alias="allCareerJobTypeExpTerm",
    )  # 経験職種の経験年数（トータル）
    income: int | None = Field(
        None,
        ge=1,
        le=9999,
        alias="income",
    )  # 年収 最大9999万円（99,990,000円）
    join_year: int | None = Field(
        None,
        alias="joinYear",
    )
    join_month: Month | None = Field(
        None,
        alias="joinMonth",
    )
    retire_year: int | None = Field(
        None,
        alias="retireYear",
    )
    retire_month: Month | None = Field(
        None,
        alias="retireMonth",
    )

    @field_validator("join_year", "retire_year")
    @classmethod
    def validate_year(cls, v):
        """入社年・退社年の妥当性検証"""
        if v is not None:
            current_year = get_current_year()
            minimum_year = get_minimum_join_retire_year()
            if v < minimum_year:
                raise ValueError(f"{minimum_year}以降の年を入力してください")
            if v > current_year:
                raise ValueError(f"{current_year}までの年を入力してください")
        return v

    @model_validator(mode="after")
    def conditional_validation(self):
        """
        条件付きバリデーション
        """
        if (
            self.management_exp_term != ExperienceYears.NONE
            and self.management_people_num is None
        ):
            raise ValueError("今までのマネジメント経験人数は必須です")

        # 経験者数が1社以上であればその他の項目は必須になる
        # マスタの1=ゼロ社
        # マスタの2=1社なので、ここでは1より大きいで比較する
        if self.exp_company_num != CompanyCount.ZERO:
            if self.company_name is None:
                raise ValueError("企業名は必須です")
            if self.income is None:
                raise ValueError("年収は必須です")
            if self.industry_small_id.id is None:
                raise ValueError("業種は必須です")
            if self.employee_num is None:
                raise ValueError("企業規模は必須です")
            if self.job_type_small_id.id is None:
                raise ValueError("職種は必須です")
            if self.join_year is None or self.join_month is None:
                raise ValueError("入社年月は必須です")
            if self.employment_type is None:
                raise ValueError("雇用形態は必須です")
            if self.employment_post is None:
                raise ValueError("役職は必須です")
            if self.job_type_exp_term is None:
                raise ValueError("直近企業での職種経験年数は必須です")
            if self.job_type_exp_term == ExperienceYears.NONE:
                raise ValueError(
                    "直近企業での職種経験年数は「経験なし」を選択できません"
                )
            if self.all_career_job_type_exp_term is None:
                raise ValueError("トータル職種経験年数は必須です")
            if self.all_career_job_type_exp_term == ExperienceYears.NONE:
                raise ValueError("トータル職種経験年数は「経験なし」を選択できません")
            if self.job_type_exp_term > self.all_career_job_type_exp_term:
                raise ValueError(
                    "直近企業での職種経験年数はトータル職種経験年数を超えてはいけません"
                )

            # 退社年月はNoneであれば在籍中という意味
            if self.retire_year is not None and self.retire_month is not None:
                # 但し、退社年月は入社年月よりも未来でなければなりません
                join_date = datetime(self.join_year, self.join_month, 1)
                retire_date = datetime(self.retire_year, self.retire_month, 1)

                if retire_date < join_date:
                    raise ValueError("退社年月は入社年月よりも過去であってはなりません")

            # job_type_exp_termの在籍期間に基づく検証
            # 1=経験なし, 2=1年未満の場合はチェック不要
            if self.job_type_exp_term >= ExperienceYears.ONE_OR_MORE:
                join_date = datetime(self.join_year, self.join_month, 1)
                if self.retire_year is not None and self.retire_month is not None:
                    # 退社済みの場合（退社月の翌月1日）
                    if self.retire_month == 12:
                        end_date = datetime(self.retire_year + 1, 1, 1)
                    else:
                        end_date = datetime(self.retire_year, self.retire_month + 1, 1)
                else:
                    # 在籍中の場合（現在月の翌月1日）
                    now = datetime.now()
                    if now.month == 12:
                        end_date = datetime(now.year + 1, 1, 1)
                    else:
                        end_date = datetime(now.year, now.month + 1, 1)

                # 在籍期間を年数で計算
                months_employed = (end_date.year - join_date.year) * 12 + (
                    end_date.month - join_date.month
                )
                years_employed = months_employed // 12

                # ExperienceYearsの値から必要な最低年数を計算
                # 3=1年以上, 4=2年以上, 5=3年以上, ..., 12=10年以上
                min_years_required = self.job_type_exp_term.min_years

                if years_employed < min_years_required:
                    months = months_employed % 12
                    raise ValueError(
                        f"直近企業での職種経験年数は在籍期間（{years_employed}年{months}ヶ月）を超えることはできません"
                    )
        return self


class JSONUserProfileWill(BaseJSONUserProfile):
    """
    ユーザーの希望条件モデル。
    DBに保存時はUserProfileのmiidas_registration_user_dataにJSONとして格納される
    """

    will_income: int = Field(
        ...,
        ge=100,
        le=2000,
        alias="willIncome",
    )  # 希望年収: 100万円から2000万円まで,
    will_work_addresses: list[AddressModel] = Field(
        ...,
        min_length=1,
        max_length=40,
        alias="willWorkAddresses",
    )  # 希望勤務地リスト
    will_remote_work: bool = Field(
        ...,
        alias="willRemoteWork",
    )  # 在宅勤務を希望する
    will_job_types: list[IDNameModel] = Field(
        ...,
        min_length=1,
        max_length=40,
        alias="willJobTypes",
    )  # 希望職種リスト
    will_job_change_period: JobChangePeriod = Field(
        ...,
        alias="willJobChangePeriod",
    )  # 転職希望時期
    is_rpo_agreement: bool = Field(
        ...,
        alias="isRpoAgreement",
    )  # 希望する求人マッチングサービスを利用するかどうか

    @model_validator(mode="after")
    def validate_unique_prefectures(self):
        """
        希望勤務地の都道府県数チェック
        """
        # 希望勤務地リストからUnique都道府県IDを取得
        unique_prefecture_ids = set()
        for address in self.will_work_addresses:
            unique_prefecture_ids.add(address.prefecture.id)

        # 重複しない都道府県数が5以下であることを確認
        if len(unique_prefecture_ids) > 5:
            raise ValueError("希望勤務地の都道府県は最大5つの都道府県まで選択可能です")

        return self


class JSONSearchKeyword(BaseModel):
    """
    キーワード検索リクエストモデル
    """

    keyword: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_keyword(self):
        """
        キーワードの妥当性検証
        """
        if not self.keyword or self.keyword.strip() == "":
            raise ValueError("キーワードは必須です")

        self.keyword = self.keyword.strip()

        return self


class JSONSearchName(BaseModel):
    """
    名前検索リクエストモデル
    """

    names: list[str] = Field(..., min_length=1)


class JSONLocation(BaseJSONModel):
    """
    都道府県、市区町村リクエストモデル
    """

    model_config = ConfigDict(populate_by_name=True)

    prefecture_name: str | None = Field(None, alias="PrefectureName")
    city_name: str = Field(..., alias="CityName")

    @model_validator(mode="after")
    def validate_keyword(self):
        if not self.city_name or self.city_name.strip() == "":
            raise ValueError("市区町村名は必須です")
        self.city_name = self.city_name.strip()

        self.prefecture_name = (
            self.prefecture_name.strip() if self.prefecture_name else None
        )

        return self


class JSONVerifyLocations(BaseJSONModel):
    """
    都道府県、市区町村検証（複数）リクエストモデル
    """

    model_config = ConfigDict(populate_by_name=True)

    locations: list[JSONLocation] = Field(..., min_length=1, alias="Locations")
