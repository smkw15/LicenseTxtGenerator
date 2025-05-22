# gen-license-txt

- gen-license-txtは、ユーザの環境にインストールされたPythonパッケージを読み取り、ライセンス情報として出力するスクリプトです。
- gen-license-txtで出力されたライセンス情報は、 *LICENSE.txt* として公開されることを想定しています。

## 開発環境

- Windows 11
- Python 3.10.6
- VSCode
- PEP8

## 環境構築方法

- 仮想環境:

```sh
# 仮想環境構築
python -m venv env

# 仮想環境起動
.\env\Scripts\activate

# pip更新
python.exe -m pip install --upgrade pip

# Python依存パッケージのインストール(初回のみ)
pip install -r requirements.txt

# 仮想環境終了(仮想環境内で)
deactivate
```

- ディレクトリ構造:

```txt
./
├─env
│　├─Scripts
│　│　├─activate.bat 👈仮想環境起動バッチ
│　│　└─deactivate.bat 👈仮想環境終了バッチ
│　└─... 👈その他仮想環境設定ファイル
├─*.py 👈Pythonソースコード
├─.flake8.py 👈flake8設定ファイル
├─license.json 👈入力ファイル
├─license.meta.json 👈特殊入力ファイル
├─LICENSE.txt 👈ライセンス情報ファイル
└─requirements.txt 👈依存ライブラリ
```

## 動作仕様

- gen-license-txtは、環境にインストールされているPythonパッケージを読み取り、「入力ファイル」として出力します。
- その後、入力ファイルを改めて読み取り、リクワイアメントファイル(一般的に*requirements.txt*と呼ばれているものです)との整合性をチェックします。
- 整合性に問題があるファイルがあった場合、それらのファイルを警告として標準出力します。
- 入力ファイルの内容に基づき、既定のフォーマットでパッケージのライセンス情報を「出力ファイル」として出力します。
- なお、gen-license-txtは、環境にインストールされているPythonパッケージの読み取りにサードパーティライブラリとしてpip-licensesを利用していますが、pip-licensesは自信の依存パッケージを出力しません。gen-license-txtでは、この点を補完するために、pip-licensesの依存パッケージのライセンス情報を「特殊入力ファイル」として用意しています。特殊入力ファイルの内容は、入力ファイルの内容と実行時に結合され、一連のデータとして扱われます。

## 使用方法

1. 以下を実行。

```sh
# 仮想環境内で
python main.py
```

2. *LICENSE.txt*ファイルが出力されます。
3. main.pyには、*gen-license-txt*の動作を制御する引数を渡すことが出来ます。

| 引数名 | ショートハンド | 型 | 説明 |
| -- | -- | -- | -- |
| `--input` | `-i` | 文字列 | 入力ファイルまでのパス。 | 
| `--output` | `-o` | 文字列 | 出力ファイルまでのパス。 |
| `--require` | `-r` | 文字列 | リクワイアメントファイルまでのパス。 |
| `--override_input_file` | `-O` | 真偽値 | 入力ファイルの上書きを許可する。 |
| `--targets` | `-t` | 配列(文字列) | 出力対象のライセンス。MIT,BSDなど。スペース区切りで渡す。 |
