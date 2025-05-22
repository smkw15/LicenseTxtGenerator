"""データモデルモジュール。"""
import dataclasses
from piplicenses import LICENSE_UNKNOWN
from enum import Enum


class Operator(Enum):
    """パッケージ要求の演算子を示す列挙子。"""
    EE = "=="
    NE = "!="
    GE = ">="
    LE = "<="
    G = ">"
    L = "<"
    TE = "~="
    U = ""  # 演算子なし


@dataclasses.dataclass
class Package:
    """パッケージ情報。

    Attribute:
        name (str): パッケージ名。
        version (str): パッケージのバージョン。
        license (str): ライセンス名。
        license_text (str): ライセンスのテキスト。
    """
    name: str
    version: str
    license: str
    license_text: str

    @classmethod
    def from_dict(cls, d: dict) -> 'Package':
        """辞書からインスタンスを生成する。

        Args:
            d (dict): パッケージ情報を格納した辞書。

        Returns:
            PackageInfo: パッケージ情報のインスタンス。
        """
        name = d.get("Name")
        version = d.get("Version")
        license = d.get("License")
        license_text = d.get("LicenseText")
        if license_text is not None and isinstance(license_text, str):
            license_text = license_text.strip()
        return cls(name, version, license, license_text)

    def has_nan(self) -> bool:
        """欠損値が存在するか。

        Returns:
            bool: 判定結果(True=欠損値あり, False=欠損値なし)
        """
        def predicate(val: str):
            return (val is None) or (val == "") or (LICENSE_UNKNOWN in val)
        return predicate(self.name) \
            or predicate(self.version) \
            or predicate(self.license) \
            or predicate(self.license_text)

    def __repr__(self) -> str:
        """標準出力の文字列を返却する。

        Returns:
            str: 標準出力用文字列。
        """
        _license_text = self.license_text if len(self.license_text) < 20 else self.license_text[:17] + "..."
        return f"name={self.name}, version={self.version}, license={self.license}, license_text={_license_text}"


@dataclasses.dataclass
class Requirement:
    """依存関係情報。

    Attributes:
        name (str): パッケージ名。
        version (str): パッケージのバージョン。
    """
    name: str = None
    version: str = ""
    operator: Operator = Operator.U

    @classmethod
    def from_string(cls, string: str) -> 'Requirement':
        """文字列からインスタンスを生成する。

        Args:
            string (str): 依存関係情報の文字列。

        Returns:
            Requirement: 依存関係情報のインスタンス。
        """
        string = string.strip()  # 改行をトリム
        # `==`で分割
        if Operator.EE.value in string:
            splited_line = string.split(Operator.EE.value)
            name = splited_line[0]
            version = splited_line[1]
            operator = Operator.EE
        # `!=`で分割
        elif Operator.NE.value in string:
            splited_line = string.split(Operator.NE.value)
            name = splited_line[0]
            version = splited_line[1]
            operator = Operator.EE
        # `>=`で分割
        elif Operator.GE.value in string:
            splited_line = string.split(Operator.GE.value)
            name = splited_line[0]
            version = splited_line[1]
            operator = Operator.GE
        # `<=`で分割
        elif Operator.LE.value in string:
            splited_line = string.split(Operator.LE.value)
            name = splited_line[0]
            version = splited_line[1]
            operator = Operator.LE
        # `>`で分割
        elif Operator.G.value in string:
            splited_line = string.split(Operator.G.value)
            name = splited_line[0]
            version = splited_line[1]
            operator = Operator.G
        # `<`で分割
        elif Operator.L.value in string:
            splited_line = string.split(Operator.L.value)
            name = splited_line[0]
            version = splited_line[1]
            operator = Operator.L
        # `~=`で分割
        elif Operator.TE.value in string:
            splited_line = string.split(Operator.TE.value)
            name = splited_line[0]
            version = splited_line[1]
            operator = Operator.TE
        # 演算子なし
        else:
            name = string
            version = ""
            operator = Operator.U
        return cls(name, version, operator)

    def validate(self, pkg: Package) -> bool:
        """パッケージが適切か判定する。

        Args:
            pkg: パッケージ情報。

        Returns:
            bool: 判定結果(True=適, False=不適)
        """
        if self.version == "" or self.version is None:
            return self.name == pkg.name
        else:
            if self.operator == Operator.EE.value:
                return self.name == pkg.name and self.version == pkg.version
            elif self.operator == Operator.NE.value:
                return self.name == pkg.name and self.version != pkg.version
            else:
                # TODO: オペレータに応じたバージョン判定を実装する
                return self.name == pkg.name

    def __repr__(self) -> str:
        """標準出力用の文字列を返却する。

        Returns:
            str: 標準出力用文字列。
        """
        if self.operator == Operator.U:
            return f"{self.name} {self.version}"
        else:
            return f"{self.name}{self.operator.value}{self.version}"
