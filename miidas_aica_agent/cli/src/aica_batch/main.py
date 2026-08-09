import typer
import atexit
from datetime import datetime, timedelta
from typing import Annotated

from containers import Container

app = typer.Typer(help="AICA Batch CLI")
container = Container()
container.init_resources()


def shutdown():
    container.shutdown_resources()


atexit.register(shutdown)


@app.command("clean_session", help="セッションをクリーニングする")
def clean_session():
    chat_command = container.chat_command_factory()
    chat_command.clean_session()


@app.command(
    "aggregate_and_delete_rate_limits",
    help="日次で、前日分のレート制限データを集計し削除する",
)
def aggregate_and_delete_rate_limits(
    target_date_str: Annotated[
        str | None,
        typer.Option(
            "--target-date",
            help="集計対象の日付 (YYYY-MM-DD形式)。指定がない場合は実行日の前日を対象とします。",
        ),
    ] = None,
):
    if target_date_str:
        try:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()

            # 今日以降の日付はエラーとする
            if target_date >= datetime.now().date():
                raise ValueError("Target date must be before today.")
        except ValueError as e:
            raise typer.BadParameter(f"Invalid date format: {e}")
    else:
        # 指定がない場合は前日を対象とする
        target_date = (datetime.now() - timedelta(days=1)).date()

    command = container.aggregate_and_delete_rate_limits_factory()
    command.execute(target_date=target_date)


@app.command(hidden=True)
def _dummy():
    """
    コマンドが1つしかない場合、実行時にコマンド名を指定できないので、ダミーを作った
    """
    pass


if __name__ == "__main__":
    app()
