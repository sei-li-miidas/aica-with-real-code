import asyncio
from enum import IntEnum, StrEnum
from typing import Final
import aiohttp
from fastapi import status
from datetime import datetime, timezone

from domain.entities.chat_session import ChatSessionStatus
from domain.entities.user_profile import (
    JSONUserProfileBasicInfo,
    JSONUserProfileCarrer,
    JSONUserProfileEducation,
    JSONUserProfileWill,
    UserProfile,
)
from repositories.action_log_repo import ActionLogRepository, ActionLogType
from repositories.api_repo import AICAAPIRepository
from repositories.chat_repo import ChatRepository
from repositories.user_repo import UserRepository
from services.base_service import BaseService
from services.position_service import PositionService
from utils.const import APPLY_POSITION_IDS_KEY
from utils.crypt import decrypt
from utils.enum import (
    EncryptKeyType,
    ApplyResult,
    DriverLicence,
    HttpMethod,
    PageName,
    SchoolType,
    ExperienceYears,
    CompanyCount,
)
from utils.log_utils import get_session_id
from utils.http import request


class UserQuickEntryValidationErrorKey(StrEnum):
    CODE = "Code"


class UserQuickEntryValidationErrorCode(IntEnum):
    EMAIL_DUPLICATION = 1013
    PHONE_NO_DUPLICATION = 1001


INTERVAL_BETWEEN_REGISTRATION_AND_APPLY: Final[int] = 11


class UserService(BaseService):
    """
    ユーザープロフィール関連のサービス
    """

    def __init__(
        self,
        position_svc: PositionService,
        chat_repository: ChatRepository,
        user_repository: UserRepository,
        aica_api_repository: AICAAPIRepository,
        action_log_repository: ActionLogRepository,
        miidas_api_url: str,
        timeout: int,
    ) -> None:
        super().__init__()

        self._position_service = position_svc
        self._chat_repository = chat_repository
        self._user_repository = user_repository
        self._aica_api_repository = aica_api_repository
        self._action_log_repository = action_log_repository
        self._miidas_api_url = miidas_api_url
        self._timeout = timeout

    def get_profile(
        self,
    ) -> UserProfile | None:
        """
        ユーザープロフィールを取得する

        Args:
            None

        Returns:
            存在する場合: ユーザープロフィール
            存在しない場合: None
        """
        profile = self._user_repository.get_user_profile()
        if profile and profile.miidas_registration_user_data:
            profile.miidas_registration_user_data.pop(APPLY_POSITION_IDS_KEY, None)
        return profile

    def save_basic_profile(
        self,
        basic_profile: JSONUserProfileBasicInfo,
    ) -> bool:
        """
        ユーザーの基本情報を保存する

        Args:
            basic_profile: 基本情報

        Returns:
            boolean: 保存成功ならTrue, 失敗ならFalse
        """
        return self._user_repository.update_miidas_registration_user_data(
            "basic_profile",
            model=basic_profile,
        )

    def save_education_profile(
        self,
        education_profile: JSONUserProfileEducation,
    ) -> bool:
        """
        ユーザーの学歴を保存する

        Args:
            education_profile: 学歴

        Returns:
            boolean: 保存成功ならTrue, 失敗ならFalse
        """
        return self._user_repository.update_miidas_registration_user_data(
            "education_profile",
            model=education_profile,
        )

    def save_experience_profile(
        self,
        experience_profile: JSONUserProfileCarrer,
    ) -> bool:
        """
        ユーザーの職歴を保存する

        Args:
            experience_profile: 職歴

        Returns:
            boolean: 保存成功ならTrue, 失敗ならFalse
        """
        return self._user_repository.update_miidas_registration_user_data(
            "experience_profile",
            model=experience_profile,
        )

    def save_preferences_profile(
        self,
        preferences_profile: JSONUserProfileWill,
    ) -> bool:
        """
        ユーザーの希望条件を保存する

        Args:
            preferences_profile: 希望条件

        Returns:
            boolean: 保存成功ならTrue, 失敗ならFalse
        """
        # Remove duplicates from will_job_types
        seen_job_type_ids = set()
        unique_job_types = []
        for job_type in preferences_profile.will_job_types:
            if job_type.id not in seen_job_type_ids:
                seen_job_type_ids.add(job_type.id)
                unique_job_types.append(job_type)
        preferences_profile.will_job_types = unique_job_types

        # Remove duplicates from will_work_addresses
        seen_city_ids = set()
        unique_cities = []
        for city_item in preferences_profile.will_work_addresses:
            if city_item.city.id not in seen_city_ids:
                seen_city_ids.add(city_item.city.id)
                unique_cities.append(city_item)
        preferences_profile.will_work_addresses = unique_cities

        return self._user_repository.update_miidas_registration_user_data(
            "preferences_profile",
            model=preferences_profile,
        )

    async def start_apply(
        self,
        encrypted_position_id: str | None = None,
    ) -> ChatSessionStatus | None:
        """
        応募開始

        Args:
            encrypted_position_id: 変換後ポジションID。ない場合、登録。ある場合、面談応募

        Returns:
            セッションが見つかった場合: セッションステータス
            見つからなかった場合: None
        """
        session_status = await asyncio.to_thread(self._chat_repository.session_status)
        if session_status:
            if session_status == ChatSessionStatus.CHATTING:
                try:
                    if encrypted_position_id:
                        real_id = decrypt(
                            EncryptKeyType.POSITION, encrypted_position_id
                        )
                        await asyncio.to_thread(
                            self._user_repository.update_miidas_registration_user_data,
                            APPLY_POSITION_IDS_KEY,
                            [real_id],
                        )

                        session_status = await asyncio.to_thread(
                            self._chat_repository.update_session_status,
                            ChatSessionStatus.APPLYING,
                        )
                    else:
                        # 分析用のログ出力
                        await asyncio.to_thread(
                            self._action_log_repository.insert,
                            log_type=ActionLogType.REGISTRATION,
                            source=PageName.POSITION_DETAIL,
                        )
                        session_status = await asyncio.to_thread(
                            self._chat_repository.update_session_status,
                            ChatSessionStatus.REGISTERING,
                        )
                except Exception:
                    self.logger.exception("応募開始失敗")

        return session_status

    async def apply_add_position(
        self,
        encrypted_position_id: str,
    ) -> ChatSessionStatus | None:
        """
        応募ポジション追加

        Args:
            encrypted_position_id: 変換後ポジションID

        Returns:
            セッションが見つかった場合: セッションステータス
            見つからなかった場合: None
        """
        session_status = await asyncio.to_thread(self._chat_repository.session_status)
        if session_status:
            if session_status in [
                ChatSessionStatus.REGISTERING,
                ChatSessionStatus.APPLYING,
            ]:
                try:
                    real_id = decrypt(EncryptKeyType.POSITION, encrypted_position_id)
                    await asyncio.to_thread(
                        self._user_repository.add_apply_position,
                        real_id,
                    )

                    if session_status == ChatSessionStatus.REGISTERING:
                        session_status = await asyncio.to_thread(
                            self._chat_repository.update_session_status,
                            ChatSessionStatus.APPLYING,
                        )

                    return session_status
                except Exception:
                    self.logger.exception("Failed add position to apply.")

        return None

    async def _call_register_user_api(
        self,
        client: aiohttp.ClientSession,
        user_profile: UserProfile,
        user_agent: str | None = None,
    ) -> tuple[int, dict | None]:
        """
        本体側の簡易登録用ユーザー登録APIを呼び出して、ユーザーを本体に登録します。

        Args:
            client: aiohttp.ClientSessionインスタンス
            user_profile: UserProfileインスタンス

        Returns:
            tuple:
                - HTTPステータスコード（intまたはNone）
                - APIレスポンスデータ（dictまたはNone）
        """
        data = user_profile.miidas_registration_user_data
        basic_profile = data["basic_profile"]
        education_profile = data["education_profile"]
        experience_profile = data["experience_profile"]
        preferences_profile = data["preferences_profile"]
        request_body = {
            "Gender": basic_profile["gender"],
            "LastName": basic_profile["lastName"],
            "FirstName": basic_profile["firstName"],
            "Birthday": str(basic_profile["birthYear"])
            + "-"
            + str(basic_profile["birthMonth"]).zfill(2)
            + "-"
            + "01",
            "Email": basic_profile["email"],
            "Password": basic_profile["password"],
            "PhoneNo": basic_profile["phoneNo"],
            "Prefecture": basic_profile["prefecture"]["ID"],
            "City": basic_profile["city"]["ID"],
            "FirstLanguage": basic_profile["firstLanguage"],
            "DriverLicence": DriverLicence.get_value(basic_profile["driverLicence"]),
            "SchoolType": education_profile["schoolType"],
            "GraduationYear": education_profile["graduationYear"],
            "EnglishLevel": education_profile["englishLevel"],
            "ExpCompanyNum": experience_profile["expCompanyNum"],
            "ManagementExpTerm": experience_profile["managementExpTerm"],
            "WillJobTypes": {
                "Smalls": list(
                    dict.fromkeys(
                        will_job_types_small["ID"]
                        for will_job_types_small in preferences_profile["willJobTypes"]
                    )
                )
            },
            "WillWorkAddresses": {
                "Cities": list(
                    dict.fromkeys(
                        will_work_addresses_city["city"]["ID"]
                        for will_work_addresses_city in preferences_profile[
                            "willWorkAddresses"
                        ]
                    )
                )
            },
            "WillIncome": preferences_profile["willIncome"],
            "WillJobChangePeriod": preferences_profile["willJobChangePeriod"],
            "IsRpoAgreement": preferences_profile["isRpoAgreement"],
        }

        if "lastNameKana" in basic_profile and "firstNameKana" in basic_profile:
            request_body |= {
                "LastNameKana": basic_profile["lastNameKana"],
                "FirstNameKana": basic_profile["firstNameKana"],
            }

        if SchoolType.requires_department(education_profile["schoolType"]):
            # 学校区分が専門学校、高等学校、中学校以外の場合、学校名と学部・学科系統必須
            request_body |= {
                "SchoolName": education_profile["schoolName"],
                "Department": education_profile["department"]["ID"],
            }
        elif SchoolType.requires_category(education_profile["schoolType"]):
            # 学校区分が専門学校の場合、専門学校区分必須
            request_body |= {
                "ProfessionalTrainingCollegeCategory": education_profile[
                    "professionalTrainingCollegeCategory"
                ]["ID"],
            }

        if ExperienceYears.has_experience(experience_profile["managementExpTerm"]):
            request_body |= {
                "ManagementPeopleNum": experience_profile["managementPeopleNum"],
            }

        if experience_profile["expCompanyNum"] != CompanyCount.ZERO:
            # 経験社数が1(1：0社)以上なら必須
            request_body |= {
                "IndustrySmallID": experience_profile["industrySmallID"]["ID"],
                "JobTypeSmallID": experience_profile["jobTypeSmallID"]["ID"],
                "JobTypeExpTerm": experience_profile["jobTypeExpTerm"],
                "AllCareerJobTypeExpTerm": experience_profile[
                    "allCareerJobTypeExpTerm"
                ],
                "EmploymentPost": experience_profile["employmentPost"],
                "Income": experience_profile["income"],
                "EmploymentStatus": 2 if experience_profile["retireYear"] else 1,
                "JoinYm": str(experience_profile["joinYear"])
                + "-"
                + str(experience_profile["joinMonth"]).zfill(2),
                "CompanyName": experience_profile["companyName"],
                "EmployeeNum": experience_profile["employeeNum"],
                "EmploymentType": experience_profile["employmentType"],
            }

            if experience_profile["retireYear"] and experience_profile["retireMonth"]:
                request_body |= {
                    "RetireYm": str(experience_profile["retireYear"])
                    + "-"
                    + str(experience_profile["retireMonth"]).zfill(2),
                }

        # 固定：リモート可、リモート可（条件付き）
        if preferences_profile["willRemoteWork"]:
            request_body |= {
                "WillRemoteWork": {"Exists": [3, 2], "OfficeFrequency": []}
            }

        api_path = "user_entry/api/v2/user_quick_entry"
        self.logger.debug("本体側の簡易登録用ユーザー登録 APIリクエスト: %s", api_path)
        headers = {
            "User-Agent": user_agent if user_agent else "AICA V1",
            "x-miidas-is-pwa": "0",
            "x-from": "https://miidas.jp/aica",
        }

        return await request(
            client,
            HttpMethod.POST,
            api_path,
            json=request_body,
            headers=headers,
        )

    async def _call_meeting_application_api(
        self,
        client: aiohttp.ClientSession,
        position_id: int,
        user_agent: str | None = None,
    ) -> tuple[int, dict | None]:
        """
        本体側の面談応募APIを呼び出します。

        Args:
            None

        Returns:
            None
        """
        position_detail = await self._position_service.get_position_detail(
            str(position_id),
            False,
        )

        if not position_detail or "Modified" not in position_detail.get("Position", {}):
            self.logger.error(
                "ポジション詳細取得失敗かModifiedがポジション詳細にない: %s",
                position_id,
            )
            # 応募APIを呼び出さずにエラーを返す
            return status.HTTP_404_NOT_FOUND, None

        # Example: Sun, 06 Nov 1994 08:49:37 GMT
        modified_date = datetime.fromisoformat(position_detail["Position"]["Modified"])
        if_unmodified_since = modified_date.astimezone(timezone.utc).strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        )

        api_path = f"apply/api/positions/{position_id}/meeting_application/"
        self.logger.debug("本体側の面談応募 APIリクエスト: %s", api_path)
        headers = {
            "User-Agent": user_agent if user_agent else "AICA V1",
            "x-miidas-is-pwa": "0",
            "x-from": "https://miidas.jp/aica",
            "x-miidas-if-position-unmodified-since": if_unmodified_since,
        }

        http_status, result = await request(
            client,
            HttpMethod.POST,
            api_path,
            headers=headers,
        )
        if http_status != status.HTTP_200_OK:
            self.logger.error(
                "Failed to call meeting application API for position %s: %s",
                position_id,
                http_status,
            )

        return http_status, result

    async def post_apply_failure(
        self,
        position_ids: list[int],
        successful_position_ids: list[int],
        failed_position_ids: list[int],
        cookies: list,
    ):
        # 応募失敗がある場合
        api_path = "positions/summaries"
        http_status, response_data = await self._aica_api_repository.post(
            api_path,
            json={"PositionIDs": position_ids},
        )

        if (
            http_status != status.HTTP_200_OK
            or not response_data
            or not response_data.get("Positions")
        ):
            # たぶんAPIサーバーダウンしか考えられないので、基本ない。
            self.logger.error(
                "応募ポジションサマリ取得が失敗しました: %s", position_ids
            )

            if successful_position_ids:
                # この場合しょうがない
                # 応募成功ポジションがあるので、応募失敗ポジションを無視して、１つ目の応募成功したポジションの面談応募完了画面にリダイレクトします。
                return (
                    status.HTTP_200_OK,
                    ChatSessionStatus.APPLIED,
                    ApplyResult.MEETING_APPLICATION_SUCCESS,
                    {
                        "Cookies": cookies,
                        "PositionID": successful_position_ids[0],
                    },
                )
            else:
                # 面談応募は全部失敗したので、結果として会員登録のみと同じ扱いとします。
                return (
                    status.HTTP_200_OK,
                    ChatSessionStatus.REGISTERED,
                    ApplyResult.REGISTER_SUCCESS,
                    {
                        "Cookies": cookies,
                    },
                )

        position_id_to_position = {pos["ID"]: pos for pos in response_data["Positions"]}

        successful_positions = [
            position_id_to_position[pos_id]
            for pos_id in successful_position_ids
            if pos_id in position_id_to_position
        ]
        if len(successful_position_ids) != len(successful_positions):
            self.logger.error(
                "応募成功ポジションの一部サマリが取得できません: %s",
                [
                    pos_id
                    for pos_id in successful_position_ids
                    if pos_id not in position_id_to_position
                ],
            )

        failed_positions = [
            position_id_to_position[pos_id]
            for pos_id in failed_position_ids
            if pos_id in position_id_to_position
        ]
        if len(failed_position_ids) != len(failed_positions):
            self.logger.error(
                "応募失敗ポジションの一部サマリが取得できません: %s",
                [
                    pos_id
                    for pos_id in failed_position_ids
                    if pos_id not in position_id_to_position
                ],
            )

        return (
            (
                status.HTTP_200_OK,
                ChatSessionStatus.APPLIED,
                ApplyResult.MEETING_APPLICATION_FAIL,
                {
                    "Cookies": cookies,
                    "SuccessfulPositions": successful_positions,
                    "FailedPositions": failed_positions,
                },
            )
            if failed_positions
            else None
        )

    async def post_register_success(
        self,
        client: aiohttp.ClientSession,
        user_register_result: dict,
        user_profile: UserProfile,
        user_agent: str | None = None,
    ):
        if not user_register_result or "UserID" not in user_register_result:
            # 想定外レスポンス
            self.logger.error(
                "impossible response from register user api: %s", user_register_result
            )

        # 会員登録成功後処理
        if not await asyncio.to_thread(
            self._chat_repository.register_user_id,
            ChatSessionStatus.REGISTERED,
            user_register_result.get("UserID") if user_register_result else None,
        ):
            # DB更新エラー
            self.logger.error("Failed to update session status to registered")

        cookies = list(client.cookie_jar)
        self.logger.info("Received cookies: %s", cookies)

        # session_statusはChatSessionStatus.REGISTEREDかChatSessionStatus.APPLYINGにかかわらず
        # 面談応募ポジションがあるかを確認します。
        position_ids = [
            int(pos_id)
            for pos_id in user_profile.miidas_registration_user_data.get(
                APPLY_POSITION_IDS_KEY,
                [],
            )
        ]
        if not position_ids:
            # 面談応募ポジションがない場合
            return (
                status.HTTP_200_OK,
                ChatSessionStatus.REGISTERED,
                ApplyResult.REGISTER_SUCCESS,
                {
                    "Cookies": cookies,
                },
            )

        # 本体側仕様に合わせて会員登録後11秒待ってからポジションを応募する。
        await asyncio.sleep(INTERVAL_BETWEEN_REGISTRATION_AND_APPLY)

        # 順次で応募APIを呼び出す
        position_results = {}
        for position_id in position_ids:
            result = await self._call_meeting_application_api(
                client,
                position_id,
                user_agent,
            )
            position_results[position_id] = result

        successful_position_ids = []
        failed_position_ids = []
        for position_id, (
            http_status,
            result,
        ) in position_results.items():
            if http_status == status.HTTP_200_OK:
                # 応募成功
                self.logger.info("Successfully applied to position: %d", position_id)
                successful_position_ids.append(position_id)
            else:
                # 応募失敗
                self.logger.error(
                    "Failed to apply to position: %d, %d, %s",
                    position_id,
                    http_status,
                    result,
                )
                failed_position_ids.append(position_id)

        if successful_position_ids:
            # 応募成功がある場合（応募失敗があっても）
            if not await asyncio.to_thread(
                self._chat_repository.update_session_status,
                ChatSessionStatus.APPLIED,
            ):
                # DB更新エラー
                self.logger.error("Failed to update session status to applied")

        if failed_position_ids:
            # 応募失敗がある場合
            result = await self.post_apply_failure(
                position_ids,
                successful_position_ids,
                failed_position_ids,
                cookies,
            )
            if result is not None:
                return result

        # 面談応募全部成功した場合か
        # 応募失敗ポジションがサマリ取得できなかった場合
        return (
            status.HTTP_200_OK,
            ChatSessionStatus.APPLIED,
            ApplyResult.MEETING_APPLICATION_SUCCESS,
            {
                "Cookies": cookies,
                "PositionID": successful_position_ids[0],
            },
        )

    def post_register_validation_failure(
        self,
        user_register_result: dict,
        user_profile: UserProfile,
        session_status: ChatSessionStatus,
    ) -> tuple[int, ChatSessionStatus, int, dict | None] | None:
        if (
            user_register_result.get(UserQuickEntryValidationErrorKey.CODE)
            == UserQuickEntryValidationErrorCode.EMAIL_DUPLICATION
        ):
            # メールアドレス重複エラー
            return (
                status.HTTP_409_CONFLICT,
                session_status,
                ApplyResult.REGISTER_FAIL,
                {
                    "Errors": [
                        {
                            "Page": PageName.PROFILE_BASIC_INFO,
                            "Field": "email",
                            "Value": user_profile.miidas_registration_user_data[
                                "basic_profile"
                            ]["email"],
                            "Message": "メールアドレスは既に登録されています。",
                        }
                    ],
                },
            )

        if (
            user_register_result.get(UserQuickEntryValidationErrorKey.CODE)
            == UserQuickEntryValidationErrorCode.PHONE_NO_DUPLICATION
        ):
            # 電話番号重複エラー
            return (
                status.HTTP_409_CONFLICT,
                session_status,
                ApplyResult.REGISTER_FAIL,
                {
                    "Errors": [
                        {
                            "Page": PageName.PROFILE_BASIC_INFO,
                            "Field": "phoneNo",
                            "Value": user_profile.miidas_registration_user_data[
                                "basic_profile"
                            ]["phoneNo"],
                            "Message": "電話番号は既に登録されています。",
                        }
                    ],
                },
            )

        details = user_register_result.get("Details")
        if details:
            errors = []
            for detail in details:
                field = detail.get("Field")
                if field:
                    # その他バリデーションエラー
                    field = field[0].lower() + field[1:]

                    # プロフィールモデルからバリデーションエラーフィールドを探す
                    basic_fields = {
                        field_info.alias or field_name
                        for field_name, field_info in JSONUserProfileBasicInfo.model_fields.items()
                    }
                    education_fields = {
                        field_info.alias or field_name
                        for field_name, field_info in JSONUserProfileEducation.model_fields.items()
                    }
                    experience_fields = {
                        field_info.alias or field_name
                        for field_name, field_info in JSONUserProfileCarrer.model_fields.items()
                    }
                    preferences_fields = {
                        field_info.alias or field_name
                        for field_name, field_info in JSONUserProfileWill.model_fields.items()
                    }

                    profile_section = ""
                    page_name = ""
                    error_fields = [field]

                    if field in basic_fields:
                        profile_section = "basic_profile"
                        page_name = PageName.PROFILE_BASIC_INFO
                    elif field in education_fields:
                        profile_section = "education_profile"
                        page_name = PageName.PROFILE_EDUCATION
                    elif field in experience_fields:
                        profile_section = "experience_profile"
                        page_name = PageName.PROFILE_CARRER
                    elif field in preferences_fields:
                        profile_section = "preferences_profile"
                        page_name = PageName.PROFILE_WILL
                    elif field == "birthday":
                        profile_section = "basic_profile"
                        page_name = PageName.PROFILE_BASIC_INFO
                        error_fields = ["birthYear", "birthMonth"]
                    elif field == "joinYm":
                        profile_section = "experience_profile"
                        page_name = PageName.PROFILE_CARRER
                        error_fields = ["joinYear", "joinMonth"]
                    elif field == "retireYm":
                        profile_section = "experience_profile"
                        page_name = PageName.PROFILE_CARRER
                        error_fields = ["retireYear", "retireMonth"]
                    else:
                        # 想定外フィールド
                        self.logger.error(
                            "Unexpected field in validation error: %s", field
                        )

                    for error_field in error_fields:
                        errors.append(
                            {
                                "Page": page_name,
                                "Field": error_field,
                                "Value": user_profile.miidas_registration_user_data[
                                    profile_section
                                ].get(error_field),
                            }
                        )

            if errors:
                return (
                    status.HTTP_400_BAD_REQUEST,
                    session_status,
                    ApplyResult.REGISTER_FAIL,
                    {
                        "Errors": errors,
                    },
                )

        # 想定外エラー
        return None

    async def apply_position(
        self,
        encrypted_position_id: str,
        cookies: dict,
        user_agent: str | None = None,
    ) -> tuple[int, str | None]:
        session_status = await asyncio.to_thread(self._chat_repository.session_status)
        if session_status not in [
            ChatSessionStatus.REGISTERED,
            ChatSessionStatus.APPLIED,
        ]:
            self.logger.error(
                "Invalid session status for session %s: %s",
                get_session_id(),
                session_status,
            )
            return status.HTTP_400_BAD_REQUEST

        try:
            position_id = decrypt(
                EncryptKeyType.POSITION,
                encrypted_position_id,
            )
        except ValueError:
            self.logger.exception(
                "ポジションID復号化が失敗しました: %s",
                encrypted_position_id,
            )
            return status.HTTP_400_BAD_REQUEST

        applied_position_ids = await asyncio.to_thread(
            self._user_repository.get_applied_position_ids
        )
        if applied_position_ids and position_id in applied_position_ids:
            self.logger.info(
                "Position already applied for session %s: %s",
                get_session_id(),
                position_id,
            )
            return status.HTTP_200_OK, None

        async with aiohttp.ClientSession(
            base_url=self._miidas_api_url,
            timeout=aiohttp.ClientTimeout(total=self._timeout),
            cookies=cookies,
            headers={"User-Agent": user_agent if user_agent else "AICA V1"},
        ) as client:
            http_status, _ = await self._call_meeting_application_api(
                client,
                int(position_id),
                user_agent,
            )

            if http_status == status.HTTP_200_OK:
                if session_status == ChatSessionStatus.REGISTERED:
                    if await asyncio.to_thread(
                        self._chat_repository.update_session_status,
                        ChatSessionStatus.APPLIED,
                    ):
                        session_status = ChatSessionStatus.APPLIED
                    else:
                        # DB更新エラー
                        self.logger.error(
                            "Failed to update session status to ChatSessionStatus.APPLIED"
                        )
                await asyncio.to_thread(
                    self._user_repository.add_apply_position, position_id
                )

                return status.HTTP_200_OK, position_id

            return http_status, None

    async def finish_apply(
        self,
        user_agent: str | None = None,
    ) -> tuple[int, ChatSessionStatus, int, dict | None]:
        """
        簡易登録用ユーザー登録APIを呼び出して、会員登録をします。
        面談応募の場合、また会員登録後面談応募APIを呼び出して、面談応募します。

        Args:
            None

        Returns:
            tuple:
                - HTTPステータスコード（int）
                - セッションステータス（ChatSessionStatus）
                - 応募結果（int）
                - エラー情報（dictまたはNone）
        """
        session_status = await asyncio.to_thread(self._chat_repository.session_status)
        if not session_status or session_status == ChatSessionStatus.CHATTING:
            self.logger.error(
                "Invalid session status for session %s: %s",
                get_session_id(),
                session_status,
            )
            return (
                status.HTTP_400_BAD_REQUEST,
                session_status,
                ApplyResult.INVALID_SESSION_STATUS,
                None,
            )

        if session_status == ChatSessionStatus.REGISTERED:
            self.logger.error(
                "Session already registered for session %s", get_session_id()
            )
            return (
                status.HTTP_200_OK,
                session_status,
                ApplyResult.REGISTER_ALREADY,
                None,
            )

        if session_status == ChatSessionStatus.APPLIED:
            self.logger.error(
                "Session already applied for session %s", get_session_id()
            )
            return (
                status.HTTP_200_OK,
                session_status,
                ApplyResult.MEETING_APPLICATION_ALREADY,
                None,
            )

        user_profile = await asyncio.to_thread(self._user_repository.get_user_profile)
        if not user_profile:
            # セッションステータスが取れたので、基本不可能
            self.logger.error(
                "User profile not found for session: %s", get_session_id()
            )
            return (
                status.HTTP_400_BAD_REQUEST,
                session_status,
                ApplyResult.UNKNOWN,
                None,
            )

        async with aiohttp.ClientSession(
            base_url=self._miidas_api_url,
            timeout=aiohttp.ClientTimeout(total=self._timeout),
        ) as client:
            # 会員登録後、必要に応じて面談応募を行いますので、
            # セッション情報を引き継ぐため、１つのHTTPセッションの中でやります。
            # まずは会員登録API
            http_status, user_register_result = await self._call_register_user_api(
                client,
                user_profile,
                user_agent=user_agent,
            )
            if http_status == status.HTTP_200_OK:
                # 会員登録成功
                return await self.post_register_success(
                    client,
                    user_register_result,
                    user_profile,
                    user_agent=user_agent,
                )
            elif http_status in [status.HTTP_409_CONFLICT, status.HTTP_400_BAD_REQUEST]:
                # メールアドレス重複エラー
                # 電話番号重複エラー
                # その他会員登録バリデーションエラー
                validation_failure_result = self.post_register_validation_failure(
                    user_register_result,
                    user_profile,
                    session_status,
                )
                if validation_failure_result is not None:
                    return validation_failure_result

            # 想定外エラー
            self.logger.error(
                "Unexpected error occurred during registration: %s, %s",
                http_status,
                user_register_result,
            )
            return (
                http_status,
                session_status,
                ApplyResult.REGISTER_FAIL,
                None,
            )

    async def search_master_data(
        self,
        names: list[str],
    ) -> dict:
        """
        APIを呼び出して、マスターデータを取得します。

        Args:
            names: マスターデータ名リスト

        Returns:
            マスターデータ
        """
        api_path = "masters/"
        self.logger.debug("マスターデータ取得APIリクエスト: %s", api_path)
        _, result = await self._aica_api_repository.get(
            api_path, params={"names": names}
        )

        return result

    async def search_by_prefecture_city_name(
        self,
        locations: list[dict[str, str]],
    ) -> dict:
        """
        APIを呼び出して、指定都道府県名・市区町村名で検索します。

        Args:
            locations: 都道府県名・市区町村名のリスト

        Returns:
            都道府県、市区町村
        """
        api_path = "location/verify/prefecture/city"
        self.logger.debug(
            "指定都道府県名・市区町村名での検索APIリクエスト: %s", api_path
        )
        _, result = await self._aica_api_repository.post(
            api_path,
            json={
                "Locations": locations,
            },
        )

        return result

    async def search_commuting_areas(
        self,
        prefecture_name: str,
        city_name: str,
    ) -> dict:
        """
        APIを呼び出して、通勤エリアを探します。

        Args:
            prefecture_name: 都道府県名
            city_name: 市区町村名

        Returns:
            都道府県、市区町村
        """
        api_path = "location/search/commuting_areas"
        self.logger.debug("通勤エリア検索APIリクエスト: %s", api_path)
        _, result = await self._aica_api_repository.post(
            api_path,
            json={
                "PrefectureName": prefecture_name,
                "CityName": city_name,
            },
        )

        return result

    async def search_location(
        self,
        keyword: str,
    ) -> dict:
        """
        APIを呼び出して、都道府県、市区町村を探します。

        Args:
            keyword: キーワード

        Returns:
            都道府県、市区町村
        """
        api_path = "location/search/keyword"
        self.logger.debug("場所検索APIリクエスト: %s", api_path)
        _, result = await self._aica_api_repository.post(
            api_path,
            json={"Keyword": keyword},
        )

        return result

    async def search_industry(
        self,
        keyword: str,
    ) -> dict:
        """
        APIを呼び出して、業界を探します。

        Args:
            keyword: キーワード

        Returns:
            業界リスト
        """
        api_path = "industry/search/semantic"
        self.logger.debug("業界検索APIリクエスト: %s", api_path)
        _, result = await self._aica_api_repository.post(
            api_path,
            json={"Sentence": keyword},
        )

        return result

    async def search_jobtype_by_keyword(
        self,
        keyword: str,
    ) -> dict:
        """
        APIを呼び出して、職種を探します。

        Args:
            keyword: キーワード

        Returns:
            職種リスト
        """
        api_path = "jobtype/search/semantic"
        self.logger.debug("職種キーワード検索APIリクエスト: %s", api_path)
        _, result = await self._aica_api_repository.post(
            api_path,
            json={"Keyword": keyword},
        )

        return result

    async def search_jobtype_by_names(
        self,
        names: list[str],
    ) -> dict:
        """
        APIを呼び出して、職種を探します。

        Args:
            names: 職種名

        Returns:
            職種リスト
        """
        api_path = "jobtype/search/names"
        self.logger.debug("職種名検索APIリクエスト: %s", api_path)
        _, result = await self._aica_api_repository.post(
            api_path,
            json={"Names": names},
        )

        return result
