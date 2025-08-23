# Chiikawa Online Market Scraper

ちいかわオンラインマーケット（chiikawamarket.jp）の商品在庫情報を取得するPythonスクレイピングツール

## 機能

- **在庫状況による商品分類**: 在庫あり、売り切れ、新着商品、予約商品
- **複数の出力形式**: CSV、Excel（統計シート付き）
- **コレクション別フィルタリング**: 特定の店舗・コレクションのみ取得
- **詳細な商品情報**: 商品ID、名前、URL、価格、コレクション、在庫状況
- **高度なエラーハンドリング**: リトライ機能、タイムアウト対応
- **レート制限**: サーバーに負荷をかけない配慮

## 使用方法

### 基本的な使い方

```bash
# CSV形式で全商品を取得
python main.py --format csv

# Excel形式で特定のコレクションを取得
python main.py --collections newitems --format excel

# 在庫あり商品のみをフィルタ
python main.py --status in_stock --format both

# 詳細ログ付きで実行
python main.py --verbose --delay 2.0
```

### オプション

- `--format {csv,excel,both}`: 出力形式の選択
- `--output FILE`: 出力ファイル名の指定
- `--collections LIST`: 取得するコレクション（カンマ区切り）
- `--status LIST`: フィルタする在庫状況
- `--max-products NUM`: 取得する最大商品数
- `--delay SECONDS`: リクエスト間の遅延秒数
- `--verbose`: 詳細ログの表示

## インストール

```bash
pip install requests beautifulsoup4 pandas openpyxl
```

## ファイル構成

- `main.py`: メインアプリケーション
- `scraper.py`: スクレイピングエンジン
- `data_processor.py`: データ処理・分析
- `config.py`: 設定管理
- `utils.py`: ユーティリティ関数

## ライセンス

個人利用目的のみ。商用利用は禁止。