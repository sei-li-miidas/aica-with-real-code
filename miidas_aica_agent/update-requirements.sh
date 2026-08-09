#!/usr/bin/env bash
#
# 全コンポーネント（server/cli/e2e）の依存関係ロックファイルを更新
#
# このスクリプトはpip-toolsを使用してpyproject.tomlからrequirements.txtと
# requirements-dev.txt（test/dev依存関係を含む）を再生成します。以下の場合に実行してください：
# - pyproject.tomlで依存関係を追加・削除・更新した時
# - 依存関係を最新の互換バージョンにアップグレードしたい時
#
# 使用方法:
#   ./update-requirements.sh                    # 全コンポーネントのロックファイルを更新
#   ./update-requirements.sh server             # serverのみ更新
#   ./update-requirements.sh cli                # cliのみ更新
#   ./update-requirements.sh e2e                # e2eのみ更新
#   ./update-requirements.sh --upgrade          # 全コンポーネントを最新の互換バージョンにアップグレード
#   ./update-requirements.sh server --upgrade   # serverのみ最新版にアップグレード
#   ./update-requirements.sh --upgrade-package fastapi
#                                            # 指定パッケージのみを最新版にアップグレード
#   ./update-requirements.sh server -P fastapi -P pydantic
#                                            # serverで複数パッケージのみアップグレード
#

set -e  # エラー時に終了

# プロジェクトルート（このスクリプトのディレクトリ）を決定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# 出力用の色設定
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # 色なし

# 利用可能なコンポーネント
COMPONENTS=("server" "cli" "e2e")

# コマンドライン引数を解析
SELECTED_COMPONENTS=()
UPGRADE_FLAG=""
UPGRADE_PACKAGES=()
PIP_COMPILE_UPGRADE_ARGS=()

build_pip_compile_upgrade_args() {
    PIP_COMPILE_UPGRADE_ARGS=()

    if [ -n "$UPGRADE_FLAG" ]; then
        PIP_COMPILE_UPGRADE_ARGS+=("--upgrade")
    fi

    for package in "${UPGRADE_PACKAGES[@]}"; do
        PIP_COMPILE_UPGRADE_ARGS+=("--upgrade-package" "$package")
    done
}

while [ "$#" -gt 0 ]; do
    arg="$1"

    if [ "$arg" == "--upgrade" ]; then
        UPGRADE_FLAG="--upgrade"
        shift
    elif [ "$arg" == "--upgrade-package" ] || [ "$arg" == "-P" ]; then
        if [ "$#" -lt 2 ]; then
            echo -e "${RED}エラー: $arg にはパッケージ名が必要です${NC}"
            echo "使用方法: $0 [server|cli|e2e] [--upgrade] [--upgrade-package <package>|-P <package>]"
            exit 1
        fi
        UPGRADE_PACKAGES+=("$2")
        shift 2
    elif [[ "$arg" == --upgrade-package=* ]]; then
        pkg="${arg#*=}"
        if [ -z "$pkg" ]; then
            echo -e "${RED}エラー: --upgrade-package= の値が空です${NC}"
            echo "使用方法: $0 [server|cli|e2e] [--upgrade] [--upgrade-package <package>|-P <package>]"
            exit 1
        fi
        UPGRADE_PACKAGES+=("$pkg")
        shift
    else
        case "$arg" in
            server|cli|e2e)
                SELECTED_COMPONENTS+=("$arg")
                shift
                ;;
            *)
                echo -e "${RED}エラー: 不明な引数 '$arg'${NC}"
                echo "使用方法: $0 [server|cli|e2e] [--upgrade] [--upgrade-package <package>|-P <package>]"
                exit 1
                ;;
        esac
    fi
done

if [ -n "$UPGRADE_FLAG" ] || [ ${#UPGRADE_PACKAGES[@]} -gt 0 ]; then
    build_pip_compile_upgrade_args
fi

# コンポーネントが指定されていない場合は全て対象
if [ ${#SELECTED_COMPONENTS[@]} -eq 0 ]; then
    SELECTED_COMPONENTS=("${COMPONENTS[@]}")
fi

echo -e "${BLUE}=== 依存関係ロックファイルの更新 ===${NC}\n"

# 一時的な仮想環境を作成してpip-toolsをインストール
TEMP_VENV=".venv-pip-tools"
# ロック生成の再現性を優先し、pip/pip-toolsは既知互換レンジで管理
PIP_VERSION_SPEC="${PIP_VERSION_SPEC:-pip>=25,<27}"
PIP_TOOLS_VERSION_SPEC="${PIP_TOOLS_VERSION_SPEC:-pip-tools>=7.4.0,<8}"
echo -e "${YELLOW}クリーンな仮想環境を作成中...${NC}"

# 既存の一時環境があれば削除
if [ -d "$TEMP_VENV" ]; then
    rm -rf "$TEMP_VENV"
fi

python3.14 -m venv "$TEMP_VENV"
source "$TEMP_VENV/bin/activate"

echo -e "${YELLOW}pip-toolsをインストール中...${NC}"
pip install --quiet --upgrade "$PIP_VERSION_SPEC"
pip install --quiet --upgrade "$PIP_TOOLS_VERSION_SPEC"

# スクリプト終了時（正常終了・異常終了問わず）に仮想環境を削除
trap "deactivate 2>/dev/null; rm -rf $TEMP_VENV" EXIT

echo -e "${GREEN}仮想環境の準備が完了しました${NC}\n"

if [ -n "$UPGRADE_FLAG" ]; then
    echo -e "${YELLOW}全ての依存関係を最新の互換バージョンにアップグレード中...${NC}\n"
elif [ ${#UPGRADE_PACKAGES[@]} -gt 0 ]; then
    echo -e "${YELLOW}指定パッケージをアップグレード中: ${UPGRADE_PACKAGES[*]}${NC}\n"
fi

# プロジェクトルートに移動
cd "$PROJECT_ROOT"

# 各コンポーネントを処理
for component in "${SELECTED_COMPONENTS[@]}"; do
    echo -e "${BLUE}--- ${component} を処理中 ---${NC}"

    # コンポーネントのpyproject.tomlが存在するか確認
    if [ ! -f "${component}/pyproject.toml" ]; then
        echo -e "${RED}エラー: ${component}/pyproject.toml が見つかりません${NC}\n"
        continue
    fi

    # コンポーネントがtest/dev依存関係を持っているか確認
    HAS_DEV_DEPS=false
    if grep -q "\[project\.optional-dependencies\]" "${component}/pyproject.toml" && \
       grep -A 10 "\[project\.optional-dependencies\]" "${component}/pyproject.toml" | grep -qE "(test|dev)"; then
        HAS_DEV_DEPS=true
    fi

    if [ "$HAS_DEV_DEPS" = true ]; then
        # 本番用と開発用の2つのファイルを生成
        echo -e "${GREEN}[1/2] requirements.txt（本番用依存関係のみ）を生成中...${NC}"
        pip-compile --strip-extras "${PIP_COMPILE_UPGRADE_ARGS[@]}" "${component}/pyproject.toml" -o "${component}/requirements.txt"

        echo -e "${GREEN}[2/2] requirements-dev.txt（test/dev依存関係を含む）を生成中...${NC}"
        pip-compile --strip-extras "${PIP_COMPILE_UPGRADE_ARGS[@]}" --extra test --extra dev "${component}/pyproject.toml" -o "${component}/requirements-dev.txt"

        # サマリーを表示
        PROD_COUNT=$(grep -c '^[a-z]' "${component}/requirements.txt" || echo "0")
        DEV_COUNT=$(grep -c '^[a-z]' "${component}/requirements-dev.txt" || echo "0")
        TEST_COUNT=$((DEV_COUNT - PROD_COUNT))

        echo -e "${BLUE}サマリー:${NC}"
        echo "  - requirements.txt:     ${PROD_COUNT}パッケージ（本番用のみ）"
        echo "  - requirements-dev.txt: ${DEV_COUNT}パッケージ（本番用 + ${TEST_COUNT}test/dev用）"
    else
        # test/dev依存関係がない場合はrequirements.txtのみ生成
        echo -e "${GREEN}requirements.txt（全依存関係）を生成中...${NC}"
        pip-compile --strip-extras "${PIP_COMPILE_UPGRADE_ARGS[@]}" "${component}/pyproject.toml" -o "${component}/requirements.txt"

        # サマリーを表示
        PROD_COUNT=$(grep -c '^[a-z]' "${component}/requirements.txt" || echo "0")

        echo -e "${BLUE}サマリー:${NC}"
        echo "  - requirements.txt: ${PROD_COUNT}パッケージ"
    fi

    echo ""
done

echo -e "${GREEN}✓ ロックファイルの更新が完了しました！${NC}\n"

echo -e "${YELLOW}次のステップ:${NC}"
echo "  1. 変更を確認: git diff */requirements*.txt"
echo "  2. ローカルで変更をテスト:"
for component in "${SELECTED_COMPONENTS[@]}"; do
    if [ -f "${component}/requirements-dev.txt" ]; then
        echo "     cd ${component} && pip install -r requirements-dev.txt"
    else
        echo "     cd ${component} && pip install -r requirements.txt"
    fi
done
echo "  3. 更新されたロックファイルをコミット"
