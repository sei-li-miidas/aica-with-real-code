import json
import logging
from typing import overload, Type
from contextlib import AbstractContextManager
from copy import deepcopy
from cryptography.fernet import InvalidToken
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Any, Callable

from domain.entities.user_profile import UserProfile
from utils.const import APPLY_POSITION_IDS_KEY, LOGGER_PREFIX
from utils.enum import EncryptKeyType
from utils.crypt import decrypt, encrypt
from utils.log_utils import get_session_id

JOB_SEARCH_OPTIONS_KEY_JOBTYPES = "jobtypes"
JOB_SEARCH_OPTIONS_KEY_LOCATIONS = "locations"
JOB_SEARCH_OPTIONS_KEY_SALARY = "salary"
JOB_SEARCH_OPTIONS_KEY_OTHER_FILTERS = "other_filters"


class UserRepository:
    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
    ) -> None:
        self._session_factory = session_factory
        self._logger = logging.getLogger(
            f"{LOGGER_PREFIX}.{self.__class__.__module__}.{self.__class__.__name__}"
        )

    def _encrypt_basic_profile(self, user_profile: UserProfile) -> None:
        """
        miidas_registration_user_data.basic_profileを暗号化する
        """
        data = user_profile.miidas_registration_user_data
        if data is None:
            return

        basic_profile = data.get("basic_profile")
        if not isinstance(basic_profile, dict):
            return

        serialized = json.dumps(basic_profile)
        try:
            data["basic_profile"] = encrypt(EncryptKeyType.PROFILE, serialized)
        except Exception:
            self._logger.exception("基本プロフィール情報の暗号化に失敗しました")
            raise

    def _encrypt_experience_profile(self, user_profile: UserProfile) -> None:
        """
        miidas_registration_user_data.experience_profile.companyNameを暗号化する
        """
        data = user_profile.miidas_registration_user_data
        if data is None:
            return

        experience_profile = data.get("experience_profile")
        if not isinstance(experience_profile, dict):
            return

        company_name = experience_profile.get("companyName")
        if not isinstance(company_name, str):
            return

        try:
            experience_profile["companyName"] = encrypt(
                EncryptKeyType.PROFILE, company_name
            )
        except Exception:
            self._logger.exception("職歴企業名の暗号化に失敗しました")
            raise

    def _decrypt_basic_profile(self, user_profile: UserProfile) -> None:
        """
        miidas_registration_user_data.basic_profileを復号化する
        """
        data = user_profile.miidas_registration_user_data
        if data is None:
            return

        basic_profile = data.get("basic_profile")
        if not isinstance(basic_profile, str):
            return

        try:
            decrypted = decrypt(EncryptKeyType.PROFILE, basic_profile)
            data["basic_profile"] = json.loads(decrypted)
        except Exception:
            self._logger.exception("基本プロフィール情報の復号化に失敗しました")
            raise

    def _decrypt_experience_profile(self, user_profile: UserProfile) -> None:
        """
        miidas_registration_user_data.experience_profile.companyNameを復号化する
        """
        data = user_profile.miidas_registration_user_data
        if data is None:
            return

        experience_profile = data.get("experience_profile")
        if not isinstance(experience_profile, dict):
            return

        company_name = experience_profile.get("companyName")
        if not isinstance(company_name, str):
            return

        try:
            experience_profile["companyName"] = decrypt(
                EncryptKeyType.PROFILE, company_name
            )
        except InvalidToken:
            # 既に平文の場合は復号せずそのまま利用する
            pass
        except Exception:
            self._logger.exception("職歴企業名の復号化に失敗しました")
            raise

    def get_user_profile(
        self,
    ) -> UserProfile | None:
        """
        セッションIDからーザープロフィールを取得
        """
        session_id = get_session_id()
        with self._session_factory() as session:
            user_profile = (
                session.query(UserProfile)
                .filter(
                    UserProfile.session_id == session_id,
                    UserProfile.deleted_at.is_(None),
                )
                .first()
            )
            if user_profile:
                self._decrypt_basic_profile(user_profile)
                self._decrypt_experience_profile(user_profile)
            return user_profile

    def save_user_profile(
        self,
        user_profile: UserProfile,
    ) -> bool:
        """
        ユーザープロフィールを保存
        """
        session_id = get_session_id()
        with self._session_factory() as session:
            profile_to_save = deepcopy(user_profile)
            profile_to_save.session_id = session_id
            self._encrypt_basic_profile(profile_to_save)
            self._encrypt_experience_profile(profile_to_save)

            session.merge(profile_to_save)
            session.commit()
            return True

    @overload
    def update_miidas_registration_user_data(
        self,
        key: str,
        value: str,
    ) -> bool: ...

    @overload
    def update_miidas_registration_user_data(
        self,
        key: str,
        model: Type[BaseModel],
    ) -> bool: ...

    @overload
    def update_miidas_registration_user_data(
        self,
        data: dict,
    ) -> bool: ...

    def update_miidas_registration_user_data(
        self,
        key: str | None = None,
        value: str | None = None,
        model: BaseModel | None = None,
        data: dict | None = None,
    ) -> bool:
        """
        ユーザープロフィールのmiidas_registration_user_dataを更新する

        Args:
            key: キー
            value: 文字列値
            model: Pydanticモデル
            data: 辞書データ

        Returns:
            boolean: 更新成功ならTrue, 失敗ならFalse
        """
        user_profile = self.get_user_profile()
        if not user_profile:
            user_profile = UserProfile(
                session_id=get_session_id(),
            )

        if user_profile.miidas_registration_user_data is None:
            user_profile.miidas_registration_user_data = {}

        if data is not None:
            user_profile.miidas_registration_user_data.update(data)
        elif key is not None:
            if model is not None:
                value = model.model_dump(mode="json", by_alias=True)  # Removed ()
                user_profile.miidas_registration_user_data[key] = value
            elif value is not None:
                user_profile.miidas_registration_user_data[key] = value
            else:
                return False
        else:
            return False

        return self.save_user_profile(user_profile)

    def get_applied_position_ids(self) -> list[str] | None:
        """
        応募済みポジションIDリストを取得

        Returns:
            list[str] | None: ポジションIDリスト、存在しない場合はNone
        """
        user_profile = self.get_user_profile()
        if not user_profile:
            return None

        if user_profile.miidas_registration_user_data is None:
            return None

        position_ids = user_profile.miidas_registration_user_data.get(
            APPLY_POSITION_IDS_KEY
        )

        return position_ids

    def add_apply_position(
        self,
        positions_id: str,
    ) -> bool:
        """
        応募ポジション追加

        Args:
            positions_id: ポジションID

        Returns:
            boolean: 更新成功ならTrue, 失敗ならFalse
        """
        user_profile = self.get_user_profile()
        if not user_profile:
            user_profile = UserProfile(
                session_id=get_session_id(),
            )

        if user_profile.miidas_registration_user_data is None:
            user_profile.miidas_registration_user_data = {}

        if APPLY_POSITION_IDS_KEY not in user_profile.miidas_registration_user_data:
            user_profile.miidas_registration_user_data[APPLY_POSITION_IDS_KEY] = [
                positions_id
            ]
        elif isinstance(
            user_profile.miidas_registration_user_data[APPLY_POSITION_IDS_KEY], list
        ):
            if (
                positions_id
                not in user_profile.miidas_registration_user_data[
                    APPLY_POSITION_IDS_KEY
                ]
            ):
                user_profile.miidas_registration_user_data[
                    APPLY_POSITION_IDS_KEY
                ].append(positions_id)
        else:
            user_profile.miidas_registration_user_data[APPLY_POSITION_IDS_KEY] = [
                user_profile.miidas_registration_user_data[APPLY_POSITION_IDS_KEY],
                positions_id,
            ]

        return self.save_user_profile(user_profile)
