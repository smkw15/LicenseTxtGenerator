"""メインモジュール。"""
import subprocess
import json
import argparse
import pathlib
import datetime
from models import Package, Requirement
from const import (
    PYTHON_PATH,
    INPUT_FILE_PATH,
    OUTPUT_FILE_PATH,
    META_INPUT_FILE_PATH,
    REQUIREMENTS_FILE_PATH,
    TARGET_LICENSES,
    ENCODING
)


def _write_input_file(python_path: pathlib.Path, dt: datetime.datetime) -> pathlib.Path:
    """入力ファイルを作成する。

    OSに`pip-licenses`を実行させてパッケージ情報をJSONとして書き出す。

    Args:
        python_path (pathlib.Path): 解析対象のPythonまでのパス。
        dt (datetime.datetime): 作成日時。

    Returns:
        pathlib.Path: 入力ファイルまでのパス。
    """
    # 入力ファイルのパスを導出
    input_file_name = pathlib.Path(INPUT_FILE_PATH).stem + "." + dt.strftime("%Y%m%d_%H%M%S_%f") + ".json"
    input_file_path = pathlib.Path(INPUT_FILE_PATH).parent / input_file_name
    # 書き込み関数
    subprocess.run(
        f"pip-licenses --python={python_path} --with-system --with-license-file --format=json --output-file={input_file_path.resolve()}",
        stdout=subprocess.DEVNULL)
    print("load python path:", python_path)
    print("create input file path:", input_file_path)
    return input_file_path


def _read_input_file(input_file_path: pathlib.Path) -> list[Package]:
    """入力ファイルを読み取る。

    Args:
        input_file_path (pathlib.Path): 入力ファイルまでのパス。

    Returns:
        list[Package]: 入力ファイルの内容。パッケージ情報。
    """
    # 入力ファイル読み取り
    with open(input_file_path, mode="r", encoding=ENCODING) as f:
        lst = json.load(f)
        if lst is None:
            lst = []
        print("load input file:", input_file_path)
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


def _write_output_file(packages: list[Package], target_licenses: list[str], dt: datetime.datetime):
    """出力ファイル書き込み。

    Args:
        packages (list[PackageInfo]): 書き込み対象のパッケージ情報。
        target_licenses (lost[str]): 書き込み対象のライセンス。
        dt (datetime.datetime): 作成日時。
    """
    # 出力ファイルまでのパスを導出
    output_file_name = pathlib.Path(OUTPUT_FILE_PATH).stem + "." + dt.strftime("%Y%m%d_%H%M%S_%f") + ".txt"
    output_file_path = pathlib.Path(OUTPUT_FILE_PATH).parent / output_file_name
    # 存在している場合は削除
    if output_file_path.exists():
        output_file_path.unlink(missing_ok=True)
    # 書き込み
    with open(output_file_path.resolve(), mode="w", encoding=ENCODING) as f:
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
    print("created output file:", output_file_path)


def gen_license_txt(
    python_path: pathlib.Path,
    requirement_path: pathlib.Path,
    target_licenses: list[str] = TARGET_LICENSES
) -> str:
    """LICENSE.txtを生成する。

    環境にインストールされているPythonパッケージを読み取り、「入力ファイル」として出力する。
    入力ファイルを改めて読み取り、Requirementファイル(requirements.txt)との整合性をチェックする。
    入力ファイルの内容に基づき、既定のフォーマットでパッケージのライセンス情報を「出力ファイル」として出力する。

    Attributes:
        python_path (pathlib.Path): 解析対象とするPythonまでのパス。
        requirement_path (pathlib.Path): Requirementファイルまでのパス。
        target_licenses (list[str]): 出力対象のライセンス。

    Returns:
        str: LICENSE.txtまでのパス。
    """
    # 作成日時
    dt = datetime.datetime.now()
    # 入力ファイル出力
    input_file_path = _write_input_file(python_path, dt)
    # 入力ファイル読み込み
    packages = _read_input_file(input_file_path)
    # (メンテナンス用)LicenseTxtGenerator自身のリポジトリが対象だった場合は、特殊入力ファイルも読み取る
    if python_path.resolve() == pathlib.Path(PYTHON_PATH).resolve():
        meta_packages = _read_input_file(pathlib.Path(META_INPUT_FILE_PATH))
        packages = packages + meta_packages
    # Requirementファイル読み込み
    requirements = _read_requirement_file(requirement_path)
    # 入力チェック
    [is_valid, msg] = _is_valid_packages(packages, requirements)
    if not is_valid:
        print(msg)
    # 対象ライセンスごとに書き込み
    _write_output_file(packages, target_licenses, dt)


def main():
    """メイン処理。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", "-p", type=str, default=PYTHON_PATH)
    parser.add_argument("--requirement", "-r", type=str, default=REQUIREMENTS_FILE_PATH)
    parser.add_argument("--license", "-l", nargs="+", default=TARGET_LICENSES)
    args = parser.parse_args()
    print("args.python", args.python)
    print("args.requirement", args.requirement)
    print("args.license:", args.license)
    gen_license_txt(
        python_path=pathlib.Path(args.python),
        requirement_path=pathlib.Path(args.requirement),
        target_licenses=args.license)


if __name__ == "__main__":
    main()
