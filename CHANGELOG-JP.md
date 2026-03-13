# 変更履歴

このファイルでは、このプロジェクトの主な変更点を管理します。

## [0.1.0] - 2026-03-14

### 変更

- 配布名とコンテナ向けのプロダクト名を `ndlocr-lite-adapter` に変更
- ドキュメントを、新プロダクト名のまま Immich 用 OCR アダプタである内容に整理
- OCR バックエンドの前提を `ndlkotenocr-lite` から `ndlocr-lite` に切り替え

### 追加

- FastAPI ベースの Immich machine-learning 互換 OCR アダプタ
- NDLOCR-Lite subprocess ランナーと Immich OCR 変換処理
- Dockerfile、Compose 例、GitHub Actions ワークフロー
- README、日本語 README、NOTICE、依存ライセンス概要
