# ifcopenshell-ifc-annotation-to-gltf

[プログマのプログラマ日記](https://rhikos-prgm.hatenablog.com/)の記事の

[ifcの注記もglTFに変換しようとして、今度こそうまくいった話](https://rhikos-prgm.hatenablog.com/entry/2023/02/14/193012)

関連のソースコードを共有するためのリポジトリです。

IfcOpenShellを利用してifc(Industry Foundation Class)ファイルからIfcAnnotationを抽出し、annotationに含まれるテキスト情報をglTFに変換するプロジェクトです。  
glTFはテキストのバウンディングボックスの座標でいたポリゴンを生成して、テキストを画像化したテクスチャを貼り付けることで生成します。  

## 動作確認バージョン

このプロジェクトは以下の環境で動作確認済みです。

- Windows11
- Python: 3.10.10

## 環境構築

以下の手順で環境構築してください。
コマンドで依存ライブラリをインストールしてください。

### 仮想環境作成（必要に応じて）

以下のコマンドで仮想環境を作成してactivateします。  

```terminal
python -m venv .venv
./venv/Scripts/activate
```

### 依存ライブラリのインストール

```terminal
pip -r requirements.txt
```

## プロジェクトの実行方法

### Pythonスクリプトの実行

annotation_text_to_gltf.pyを実行します。  

成功すると以下の結果が得られます：

- output/annotations.glbが出力される

