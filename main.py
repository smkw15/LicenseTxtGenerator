"""メインモジュール。"""
import os
import subprocess
import json
import argparse
from models import Package, Requirement

# 入出力ファイルまでのパス
META_INPUT_FILE_PATH = "license.meta.json"
INPUT_FILE_PATH = "license.json"
OUTPUT_FILE_PATH = "LICENSE.txt"
# 依存パッケージ定義
REQUIREMENTS_FILE_PATH = "requirements.txt"
# ライセンス
MIT = "MIT"
BSD = "BSD"
GPL = "GPL"
# 処理対象ライセンス
TARGET_LICENSES = [MIT, BSD, GPL]
# 一般定数
ENCODING = "utf-8"


def _write_input_file(repository: str, input_file_path: str, override_input_file: bool):
    """入力ファイルを作成する。

    OSに`pip-licenses`を実行させてパッケージ情報をJSONとして書き出す。

    Args:
        repository (str): リポジトリ。
        input_file_path (str): 入力ファイルまでのパス。
        override_input_file (bool): 入力ファイルの上書きフラグ。
    """
    # 書き込み関数
    def _write():
        subprocess.run(
            f"pip-licenses --python {repository} --with-license-file --format=json --output-file={input_file_path}",
            stdout=subprocess.DEVNULL)
        print("created:", input_file_path)
    # ファイルが存在している場合は、強制フラグが立ってる時だけ書き込む
    if os.path.exists(input_file_path):
        if override_input_file:
            os.remove(input_file_path)
            print("removed input file:", input_file_path)
            _write()
    else:
        _write()


def _read_input_file(input_file_path: str) -> list[Package]:
    """入力ファイルを読み取る。

    Args:
        input_file_path (str): 入力ファイルまでのパス。

    Returns:
        list[PackageInfo]: 入力ファイルの内容。パッケージ情報。
    """
    # 入力ファイル読み取り
    with open(INPUT_FILE_PATH, mode="r", encoding=ENCODING) as f:
        lst = json.load(f)
        if lst is None:
            lst = []
        print("load input file:", input_file_path)
    # `pip-licenses`関係のパッケージは入力ファイルに出力されないので特殊扱いのファイルから読み取る
    with open(META_INPUT_FILE_PATH, mode="r", encoding=ENCODING) as f:
        lst_meta = json.load(f)
        if lst_meta is None:
            lst_meta = []
        print("load meta input file:", META_INPUT_FILE_PATH)
    lst = lst + lst_meta
    return [Package.from_dict(d) for d in lst]


def _read_requirement_file(requirement_file_path: str) -> list[Requirement]:
    """Requirementファイルを読み取る。

    Args:
        requirement_file_path (str): Requirementファイルまでのパス。

    Returns:
        list[Requirement]: Requirementファイルの内容。Requirement情報。
    """
    with open(requirement_file_path, mode="r", encoding=ENCODING) as f:
        lines = f.readlines()
        print("load requirement file:", requirement_file_path)
        return [Requirement.from_string(line) for line in lines]


def _is_valid_packages(packges: list[Package], requirements: list[Requirement]) -> tuple[bool, str]:
    """バリデーションチェック。

    Args:
        packges (list[PackageIngo]): 検査対象のパッケージ情報。

    Returns:
        tuple[bool, str]: 判定結果(True=適, False=不適)。およびエラーメッセージ。
    """
    is_valid = True
    lst_msg = []
    # インストール済みパッケージを検査
    for pkg in packges:
        # 欠損値があるか
        if pkg.has_nan():
            is_valid = False
            lst_msg.append(f"!!!! found nan pkg: {pkg}")
        # Requirementに含まれていないか
        if pkg.name not in [r.name for r in requirements]:
            is_valid = False
            lst_msg.append(f"!!!! found unrequired pkg: {pkg}")
    # Requirementを検査
    for requirement in requirements:
        # インストール済みパッケージに含まれていないか
        if requirement.name not in [pkg.name for pkg in packges]:
            is_valid = False
            lst_msg.append(f"!!!! found unsatisfied pkg: {requirement}")
    return is_valid, '\n'.join(lst_msg)


def _write_output_file(packages: list[Package], output_file_path: str, target_licenses: list[str]):
    """出力ファイル書き込み。

    Args:
        packages (list[PackageInfo]): 書き込み対象のパッケージ情報。
        output_file_path (str): 出力ファイルまでのパス。
        target_licenses (lost[str]): 書き込み対象のライセンス。
    """
    # 存在している場合は削除
    if os.path.exists(output_file_path):
        os.remove(output_file_path)
    # 書き込み
    with open(output_file_path, mode="w", encoding=ENCODING) as f:
        for target_license in target_licenses:
            # 書き込み対象を抽出
            _pacakges = [pkg for pkg in packages if target_license in pkg.license]
            # ライセンスごとの区切りを出力
            f.write("=" * 80 + "\n")
            f.write(f"Third-party packages under the {target_license} License:\n")
            f.write("=" * 80 + "\n")
            # 各パッケージについて書き込み
            for i, pkg in enumerate(_pacakges):
                # 書き込み
                f.write(f"Package: {pkg.name}\n")
                f.write(f"Version: {pkg.version}\n")
                f.write(f"License: {pkg.license}\n")
                f.write("License Text:\n")
                f.write(pkg.license_text + "\n\n")
                # 最終データ以外は区切り線を出力
                if i != len(_pacakges) - 1:
                    f.write("-" * 80 + "\n")
    print("created output file:", OUTPUT_FILE_PATH)


def gen_license_txt(
    repository: str,
    input_file_path: str = INPUT_FILE_PATH,
    output_file_path: str = OUTPUT_FILE_PATH,
    requirement_file_path: str = REQUIREMENTS_FILE_PATH,
    override_input_file: bool = False,
    target_licenses: list[str] = TARGET_LICENSES
) -> str:
    """LICENSE.txtを生成する。

    環境にインストールされているPythonパッケージを読み取り、「入力ファイル」として出力する。
    入力ファイルを改めて読み取り、Requirementファイル(requirements.txt)との整合性をチェックする。
    入力ファイルの内容に基づき、既定のフォーマットでパッケージのライセンス情報を「出力ファイル」として出力する。

    Attributes:
        repository (str): リポジトリ。対象とする環境。
        input_file_path (str): 入力ファイルまでのパス。
        output_file_path (str): 出力ファイルまでのパス。
        requirement_file_path (str): Requirementファイルまでのパス。
        override_input_file (bool): 入力ファイルの上書きフラグ。
        target_licenses (list[str]): 出力対象のライセンス。

    Returns:
        str: LICENSE.txtまでのパス。
    """
    # 入力ファイル出力
    _write_input_file(repository, input_file_path, override_input_file)
    # 入力ファイル読み込み
    packages = _read_input_file(input_file_path)
    # Requirementファイル読み込み
    requirements = _read_requirement_file(requirement_file_path)
    # 入力チェック
    [is_valid, msg] = _is_valid_packages(packages, requirements)
    if not is_valid:
        print(msg)
    # 対象ライセンスごとに書き込み
    _write_output_file(packages, output_file_path, target_licenses)


def main():
    """メイン処理。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", "-r", type=str)
    parser.add_argument("--input", "-i", default=INPUT_FILE_PATH)
    parser.add_argument("--output", "-o", default=OUTPUT_FILE_PATH)
    parser.add_argument("--require", "-r", default=REQUIREMENTS_FILE_PATH)
    parser.add_argument("--override_input_file", "-O", action="store_true")
    parser.add_argument("--targets", "-t", nargs="+", default=TARGET_LICENSES)
    args = parser.parse_args()

    print("args.repository", args.repository)
    print("args.input:", args.input)
    print("args.output:", args.output)
    print("args.require:", args.require)
    print("args.override_input_file:", args.override_input_file)
    print("args.targets:", args.targets)

    gen_license_txt(
        repository=args.repository,
        input_file_path=args.input,
        output_file_path=args.output,
        requirement_file_path=args.require,
        override_input_file=args.override_input_file,
        target_licenses=args.targets)


if __name__ == "__main__":
    main()
