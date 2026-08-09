from contextlib import AbstractContextManager
from datetime import datetime, timedelta
import json
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Callable

from utils.const import LOGGER_PREFIX
from utils.crypt import create_secret_key, decrypt, encrypt
from utils.enum import EncryptKeyType


class ChatCommand:
    """
    チャット操作関連コマンド
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
    ) -> None:
        """
        インスタンス初期化

        Args:
            session_factory: DBセッションッ
        """
        self._logger = logging.getLogger(
            f"{LOGGER_PREFIX}.{self.__class__.__module__}.{self.__class__.__name__}"
        )
        self._session_factory = session_factory

    def _process_basic_profile_for_session(
        self, session: Session, session_id: str
    ) -> bool:
        """
        指定セッションのuser_profilesのmiidas_registration_user_dataの
        - basic_profile
        - experience_profile
        から指定キーを削除

        Args:
            session: DBセッション
            session_id: 処理対象のセッションID

        Returns:
            プロフィールが更新されたかどうか
        """
        # 対象プロフィールを取得
        get_profile_sql = text(
            """
            SELECT id, miidas_registration_user_data
            FROM user_profiles
            WHERE session_id = :session_id
        """
        )
        profile = session.execute(get_profile_sql, {"session_id": session_id}).first()

        if not profile:
            return False

        profile_id, user_data = profile

        if not user_data:
            return False

        key = create_secret_key(session_id, EncryptKeyType.PROFILE)
        updated = False

        try:
            # basic_profileの処理
            if "basic_profile" in user_data:
                encrypted_basic_profile = user_data["basic_profile"]
                if not isinstance(encrypted_basic_profile, str):
                    error_msg = (
                        f"basic_profileが文字列ではありません"
                        f"(session_id={session_id}, "
                        f"type={type(encrypted_basic_profile).__name__})"
                    )
                    raise TypeError(error_msg)

                # 復号化
                decrypted = decrypt(key, encrypted_basic_profile)
                basic_profile = json.loads(decrypted)

                if not isinstance(basic_profile, dict):
                    error_msg = (
                        f"basic_profileがdictではありません"
                        f"(session_id={session_id}, "
                        f"type={type(basic_profile).__name__})"
                    )
                    raise TypeError(error_msg)

                # 指定キーを削除
                basic_profile_keys_to_remove = {
                    "lastName",
                    "firstName",
                    "lastNameKana",
                    "firstNameKana",
                    "email",
                    "phoneNo",
                    "password",
                }
                for key_to_remove in basic_profile_keys_to_remove:
                    basic_profile.pop(key_to_remove, None)

                # 暗号化して保存
                serialized = json.dumps(basic_profile)
                encrypted = encrypt(key, serialized)

                # DBを更新 (basic_profileとexperience_profileを同時に更新)
                # `#-`はJSONBカラムからkey/valueを削除する命令
                # `basic_profile`は値だけではなくキーも含めて全部暗号化しているので、
                # 一度複合化しないと特定のkey/valyeの削除ができない（つまり`#-`が使えない）
                update_sql = text(
                    """
                        UPDATE user_profiles
                        SET miidas_registration_user_data =
                            jsonb_set(
                                miidas_registration_user_data
                                #- '{experience_profile, companyName}',
                                '{basic_profile}',
                                to_jsonb(CAST(:encrypted_value AS text))
                            )
                        WHERE id = :profile_id
                    """
                )
                session.execute(
                    update_sql,
                    {
                        "encrypted_value": encrypted,
                        "profile_id": profile_id,
                    },
                )
                return True

            return updated

        except Exception:
            self._logger.exception(
                "プロフィール処理エラー詳細 (session_id=%s)", session_id
            )
            raise

    def _backup_and_delete_old_data(
        self, session: Session, cutoff_date: datetime
    ) -> None:
        """
        指定日時より前のデータをバックアップに移動してから物理削除

        Args:
            session: DBセッション
            cutoff_date: 削除基準日時（この日時より前のデータが対象）
        """
        # 1-1. chat_sessionsをバックアップ
        backup_sessions_sql = text(
            """
            INSERT INTO chat_sessions_backup
            SELECT *
            FROM chat_sessions
            WHERE created_at < :cutoff_date
        """
        )

        backup_sessions_result = session.execute(
            backup_sessions_sql, {"cutoff_date": cutoff_date}
        )
        backup_sessions_count = backup_sessions_result.rowcount
        self._logger.info(
            "バックアップレコード数(chat_sessions): %d",
            backup_sessions_count,
        )

        if backup_sessions_count > 0:
            # 1-2. chat_historiesをバックアップ
            backup_histories_sql = text(
                """
                INSERT INTO chat_histories_backup
                SELECT ch.*
                FROM chat_histories ch
                INNER JOIN chat_sessions cs ON ch.session_id = cs.session_id
                WHERE cs.created_at < :cutoff_date
            """
            )

            backup_histories_result = session.execute(
                backup_histories_sql, {"cutoff_date": cutoff_date}
            )
            backup_histories_count = backup_histories_result.rowcount
            self._logger.info(
                "バックアップレコード数(chat_histories): %d",
                backup_histories_count,
            )

            # 1-3. user_profilesをバックアップ
            backup_profiles_sql = text(
                """
                INSERT INTO user_profiles_backup
                SELECT up.*
                FROM user_profiles up
                INNER JOIN chat_sessions cs ON up.session_id = cs.session_id
                WHERE cs.created_at < :cutoff_date
            """
            )

            backup_profiles_result = session.execute(
                backup_profiles_sql, {"cutoff_date": cutoff_date}
            )
            backup_profiles_count = backup_profiles_result.rowcount
            self._logger.info(
                "バックアップレコード数(user_profiles): %d",
                backup_profiles_count,
            )

            # 1-4. job_search_filtersをバックアップ
            backup_job_search_filters_sql = text(
                """
                INSERT INTO job_search_filters_backup
                SELECT jsf.*
                FROM job_search_filters jsf
                INNER JOIN chat_sessions cs ON jsf.session_id = cs.session_id
                WHERE cs.created_at < :cutoff_date
            """
            )

            backup_job_search_filters_result = session.execute(
                backup_job_search_filters_sql, {"cutoff_date": cutoff_date}
            )
            backup_job_search_filters_count = backup_job_search_filters_result.rowcount
            self._logger.info(
                "バックアップレコード数(job_search_filters): %d",
                backup_job_search_filters_count,
            )

        # 物理削除
        physical_delete_sql = text(
            """
            SELECT COUNT(*) FROM chat_sessions
            WHERE created_at < :cutoff_date
        """
        )
        physical_delete_count = session.execute(
            physical_delete_sql, {"cutoff_date": cutoff_date}
        ).scalar()
        self._logger.info("物理削除セッション数: %d", physical_delete_count)

        delete_sessions_sql = text(
            """
            DELETE FROM chat_sessions
            WHERE created_at < :cutoff_date
        """
        )
        session.execute(delete_sessions_sql, {"cutoff_date": cutoff_date})

    def _clean_unregistered_sessions(
        self, session: Session, cutoff_date: datetime
    ) -> None:
        """
        会員未登録セッションのプロファイルをクリーニングする

        処理内容:
        1. 指定日時前のデータで会員未登録（status < 200）のセッションを取得
        2. 各セッションのuser_profilesから
          - miidas_registration_user_data.basic_profileから以下のキーを削除
            - lastName
            - firstName
            - lastNameKana
            - firstNameKana
            - email
            - phoneNo
            - password
          - miidas_registration_user_data.experience_profileから以下のキーを削除
            - companyName

        Args:
            session: DBセッション
            cutoff_date: 基準日時（この日時より前のデータが対象）
        """
        self._logger.info("会員未登録セッションプロファイルクリーニング開始")

        # 対象セッションのsession_idを取得
        get_session_ids_sql = text(
            """
            SELECT session_id FROM chat_sessions
            WHERE created_at < :cutoff_date
            AND status < 200
            AND deleted_at IS NULL
        """
        )
        session_ids = [
            row[0]
            for row in session.execute(
                get_session_ids_sql,
                {"cutoff_date": cutoff_date},
            )
        ]

        target_count = len(session_ids)
        self._logger.info("対象セッション数: %d", target_count)

        if target_count > 0:
            profiles_count = 0

            # 各セッションのプロファイルを処理
            for session_id in session_ids:
                try:
                    # user_profilesのbasic_profileを処理
                    updated = self._process_basic_profile_for_session(
                        session,
                        session_id,
                    )
                    if updated:
                        profiles_count += 1

                except Exception:
                    self._logger.exception(
                        "セッション処理エラー詳細 (session_id=%s)",
                        session_id,
                    )
                    raise

            self._logger.info("プロファイル更新数: %d", profiles_count)
        else:
            self._logger.info("対象セッションなし")

        self._logger.info("会員未登録セッションプロファイルクリーニング完了")

    def _logical_delete_old_data(
        self, session: Session, cutoff_date: datetime, now: datetime
    ) -> None:
        """
        指定日時より前のデータを論理削除

        Args:
            session: DBセッション
            cutoff_date: 削除基準日時（この日時より前のデータが対象）
            now: 現在時刻
        """
        logical_delete_sql = text(
            """
            SELECT COUNT(*) FROM chat_sessions
            WHERE created_at < :cutoff_date AND deleted_at IS NULL
        """
        )
        logical_delete_count = session.execute(
            logical_delete_sql, {"cutoff_date": cutoff_date}
        ).scalar()
        self._logger.info("論理削除セッション数: %d", logical_delete_count)

        update_sessions_sql = text(
            """
            UPDATE chat_sessions
            SET deleted_at = :now
            WHERE created_at < :cutoff_date AND deleted_at IS NULL
        """
        )
        session.execute(update_sessions_sql, {"cutoff_date": cutoff_date, "now": now})

    def clean_session(self):
        """
        会話履歴クリーニング
        - 2日前の会員未登録セッションのプロファイルをクリーニング
        - 30日前のデータをバックアップに移動
        - 2日前のデータを論理削除
        """
        self._logger.info("セッションクリーニング開始")

        try:
            with self._session_factory() as session:
                now = datetime.now()
                two_days_ago = now - timedelta(days=2)
                one_month_ago = now - timedelta(days=30)

                # 1. 2日前の会員未登録セッションのプロファイルをクリーニング
                self._clean_unregistered_sessions(session, two_days_ago)

                # 2. 30日前のデータをバックアップに移動してから物理削除
                self._backup_and_delete_old_data(session, one_month_ago)

                # 3. 2日前のデータを論理削除
                self._logical_delete_old_data(session, two_days_ago, now)

                session.commit()

            self._logger.info("セッションクリーニング完了")

        except Exception:
            self._logger.exception("セッションクリーニング失敗")
            raise
