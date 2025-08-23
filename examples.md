# ちいかわオンラインマーケット スクレイピングツール 使用例

## 基本的な使用方法

### 1. CSV形式で新着商品を取得
```bash
python main.py --format csv --collections newitems
```

### 2. Excel形式で全商品を取得
```bash
python main.py --format excel --output chiikawa_products.xlsx
```

### 3. 在庫あり・売り切れ商品のみをフィルタ
```bash
python main.py --status in_stock,sold_out --format both
```

### 4. 特定のコレクションを指定
```bash
python main.py --collections chiikawarestaurant,tokyomiyage --format excel
```

### 5. 詳細ログ付きで実行
```bash
python main.py --verbose --format csv --max-products 50
```

## 出力ファイル例

### CSV出力
- `chiikawa_products_20250823_141530.csv`
- 商品ID, 商品名, 商品URL, 価格, コレクション, 在庫状況, 取得日時

### Excel出力（複数シート）
- **商品データ**: 全商品の詳細情報
- **統計情報**: 在庫状況分布、価格統計など
- **コレクション別**: 各コレクションごとの商品リスト

## 高度な設定

### レート制限の調整
```bash
python main.py --delay 2.0  # 2秒間隔でリクエスト
```

### 最大商品数の制限
```bash
python main.py --max-products 100  # 最大100商品まで
```

### カスタムファイル名指定
```bash
python main.py --output my_products --format both
# → my_products.csv と my_products.xlsx を生成
```

## 利用可能なコレクション
- newitems (新着商品)
- chiikawarestaurant (ちいかわレストラン)
- tokyomiyage (東京土産)
- magicalchiikawa (まじかるちいかわ)
- その他多数

## フィルター設定
- `in_stock`: 在庫あり商品のみ
- `sold_out`: 売り切れ商品のみ  
- `new_items`: 新着商品のみ
- `all`: 全商品（デフォルト）