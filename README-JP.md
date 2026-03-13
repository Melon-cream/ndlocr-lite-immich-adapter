# ndlocr-lite-adapter

`ndlocr-lite-adapter` は、Immich 向けの `machine-learning` API 互換 OCR 専用アダプタです。OCR 推論は `NDLOCR-Lite` (`ndlocr-lite`) に委譲し、その出力を Immich 互換 JSON に変換して返します。

公開コンテナイメージには `ndlocr-lite` を同梱せず、初回起動時に公式 upstream リポジトリから取得して利用する構成です。

## できること

- `GET /ping` と `POST /predict` を提供
- Immich の `multipart/form-data` OCR リクエストを受信
- NDLOCR-Lite の JSON 出力を `text`, `box`, `boxScore`, `textScore` に変換
- Immich の OCR 保存、オーバーレイ表示、検索インデックスにそのまま使える形式で返却

## 対応範囲

- 対応タスク: `ocr`
- 非対応タスク: `clip`, `facial-recognition` など。受信時は `501` を返します
- 初期ターゲット: CPU 実行

## 主な配置

- `src/ndlocr_lite_adapter`: FastAPI アプリ本体と NDLOCR-Lite ランナー
- `tests`: API とレスポンス変換のテスト
- `Dockerfile`: adapter bootstrap 用コンテナ定義
- `docker-compose.example.yml`: Compose 利用例

## クイックスタート

### 1. イメージをビルド

```bash
podman build -t ndlocr-lite-immich-adapter .
```

### 2. アダプタを起動

```bash
podman run --rm -p 3003:3003 ndlocr-lite-immich-adapter
```

初回起動時には `ndlocr-lite` を upstream から直接取得し、`/opt/ndlocr-lite-venv` に専用 virtualenv を作って依存パッケージを導入します。

### 3. Immich 側 URL を差し替え

Immich の machine-learning URL に次を設定します。

```text
http://ndlocr-lite-immich-adapter:3003
```

単体起動の場合は、Immich から到達可能なホスト名や IP に置き換えてください。

## Compose 利用例

[`docker-compose.example.yml`](https://github.com/Melon-cream/ndlocr-lite-immich-adapter/blob/main/docker-compose.example.yml) をベースにしてください。サービスは `3003` を公開し、container 再作成後も upstream checkout と virtualenv を再利用できるよう named volume を使います。

## 環境変数

- `HOST`: バインドアドレス。既定値 `0.0.0.0`
- `PORT`: 待受ポート。既定値 `3003`
- `LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- `DEVICE`: NDLOCR-Lite の `--device` に渡す値。既定値 `cpu`
- `MODEL_DIR`: コンテナ内のモデルディレクトリ。既定値 `/opt/ndlocr-lite/src/model`
- `MAX_IMAGE_PIXELS`: 画像総画素数の上限。超過時は縮小
- `REQUEST_TIMEOUT`: NDLOCR-Lite CLI のタイムアウト秒数
- `NDL_OCR_LITE_DIR`: upstream リポジトリの配置先
- `NDL_OCR_LITE_VENV_DIR`: upstream 実行用 virtualenv の配置先
- `NDL_OCR_LITE_REPO`: bootstrap に使う upstream Git リポジトリ
- `NDL_OCR_LITE_REF`: 取得する upstream の branch または tag
- `BOOTSTRAP_NDL_OCR_LITE`: `false` にすると bootstrap を無効化し、事前配置を必須にする
- `NDL_OCR_LITE_BOOTSTRAP_TIMEOUT`: bootstrap 時の clone と依存導入に適用するタイムアウト秒数
- `NDL_OCR_LITE_PYTHON`: upstream CLI 実行に使う Python

## 互換仕様メモ

- `entries` は `ocr` のみ受け付けます
- `box` は `0.0-1.0` の正規化座標で返します
- 点順は Immich OCR 互換の順に並べ替えます
- `textScore` は upstream JSON に独立値がないため、confidence 値を代用しています

## 動作確認

最低限の構文確認:

```bash
python3 -m compileall src tests
```

Lint とテストは GitHub Actions に含めています。

## ライセンスと帰属

このリポジトリは `NDLOCR-Lite` そのものではなく、Immich 接続用のアダプタです。

- adapter 部分のライセンス: MIT
- upstream: `ndlocr-lite`
- bootstrap 元: `NDL_OCR_LITE_REPO` で指定する公式 upstream
- 帰属と変更点: [`NOTICE.md`](https://github.com/Melon-cream/ndlocr-lite-immich-adapter/blob/main/NOTICE.md)
- 依存ライセンス概要: [`THIRD_PARTY_LICENSES.md`](https://github.com/Melon-cream/ndlocr-lite-immich-adapter/blob/main/THIRD_PARTY_LICENSES.md)

公開コンテナイメージには upstream リポジトリ内容を含めません。運用時には upstream 側のライセンスも確認してください。
