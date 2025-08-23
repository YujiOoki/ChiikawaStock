#!/usr/bin/env python3
"""
Simplified Chiikawa scraper based on working debug approach
"""

import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from datetime import datetime
import argparse
import logging
from utils import clean_text, parse_price

def setup_logging(verbose=False):
    """ロギング設定を初期化"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )

def scrape_collection(collection_name, max_products=None):
    """指定されたコレクションの商品を取得"""
    base_url = "https://chiikawamarket.jp"
    url = f"{base_url}/collections/{collection_name}?page=1"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # エンコーディングを明示的に設定
        response.encoding = response.apparent_encoding or 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 商品リンクを探す
        product_links = soup.find_all('a', href=re.compile(rf'/collections/{collection_name}/products/'))
        
        logging.info(f"コレクション '{collection_name}' で {len(product_links)} 個の商品リンクを発見")
        
        products = []
        
        for i, link in enumerate(product_links):
            if max_products and i >= max_products:
                break
                
            try:
                href = link.get('href', '')
                product_url = f"{base_url}{href}" if href.startswith('/') else href
                
                # 商品名を取得
                title = clean_text(link.get_text()) if link.get_text().strip() else "商品名不明"
                
                # 親要素から価格情報を探す
                parent = link.parent
                price = None
                
                # 価格を探すため、親要素を遡る
                current = parent
                for _ in range(5):  # 最大5階層まで遡る
                    if current:
                        price_text = current.get_text()
                        if '¥' in price_text:
                            price = parse_price(price_text)
                            if price:
                                break
                        current = current.parent
                    else:
                        break
                
                # 在庫状況を判定
                stock_status = '在庫あり'  # デフォルト
                parent_text = parent.get_text().lower() if parent else ''
                
                if any(pattern in parent_text for pattern in ['売り切れ', 'sold out', '完売']):
                    stock_status = '売り切れ'
                elif '予約' in parent_text:
                    stock_status = '予約商品'
                elif any(pattern in parent_text for pattern in ['new', '新着']):
                    stock_status = '新着商品'
                
                # 商品IDを抽出
                product_id = href.split('/')[-1] if href else f"product_{i+1}"
                
                product_data = {
                    '商品ID': product_id,
                    '商品名': title,
                    '商品URL': product_url,
                    '価格': price,
                    'コレクション': collection_name,
                    '在庫状況': stock_status,
                    '取得日時': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                products.append(product_data)
                logging.debug(f"商品 {i+1}: {title} - ¥{price} ({stock_status})")
                
            except Exception as e:
                logging.warning(f"商品 {i+1} の処理でエラー: {str(e)}")
                continue
        
        return products
        
    except Exception as e:
        logging.error(f"コレクション '{collection_name}' の取得でエラー: {str(e)}")
        return []

def save_to_csv(products, filename):
    """商品データをCSVファイルに保存"""
    if not products:
        logging.warning("保存する商品データがありません")
        return
    
    df = pd.DataFrame(products)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    logging.info(f"CSVファイルに保存しました: {filename}")

def save_to_excel(products, filename):
    """商品データをExcelファイルに保存"""
    if not products:
        logging.warning("保存する商品データがありません")
        return
    
    df = pd.DataFrame(products)
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # メインデータシート
        df.to_excel(writer, sheet_name='商品データ', index=False)
        
        # 統計シート
        stats_data = []
        stats_data.append(['項目', '値'])
        stats_data.append(['総商品数', len(df)])
        stats_data.append(['コレクション数', df['コレクション'].nunique()])
        
        # 在庫状況分布
        stock_dist = df['在庫状況'].value_counts()
        stats_data.append(['', ''])
        stats_data.append(['在庫状況', '商品数'])
        for status, count in stock_dist.items():
            stats_data.append([status, count])
        
        # 価格統計
        if '価格' in df.columns and not df['価格'].isna().all():
            stats_data.append(['', ''])
            stats_data.append(['価格統計', ''])
            stats_data.append(['平均価格', f"¥{df['価格'].mean():.0f}"])
            stats_data.append(['最高価格', f"¥{df['価格'].max():.0f}"])
            stats_data.append(['最低価格', f"¥{df['価格'].min():.0f}"])
        
        stats_df = pd.DataFrame(stats_data)
        stats_df.to_excel(writer, sheet_name='統計情報', index=False, header=False)
    
    logging.info(f"Excelファイルに保存しました: {filename}")

def main():
    parser = argparse.ArgumentParser(description='ちいかわオンラインマーケット 簡易スクレイピングツール')
    parser.add_argument('--collections', '-c', default='newitems', help='取得するコレクション (カンマ区切り)')
    parser.add_argument('--max-products', '-m', type=int, default=50, help='最大取得商品数')
    parser.add_argument('--format', '-f', choices=['csv', 'excel', 'both'], default='csv', help='出力形式')
    parser.add_argument('--output', '-o', help='出力ファイル名')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細ログ')
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    collections = args.collections.split(',')
    all_products = []
    
    for collection in collections:
        collection = collection.strip()
        logging.info(f"コレクション '{collection}' を処理中...")
        products = scrape_collection(collection, args.max_products)
        all_products.extend(products)
    
    if not all_products:
        logging.error("取得できた商品データがありません")
        return
    
    logging.info(f"合計 {len(all_products)} 件の商品データを取得しました")
    
    # 統計を表示
    df = pd.DataFrame(all_products)
    print(f"\n📊 取得結果統計:")
    print(f"🎯 総商品数: {len(df)} 件")
    print(f"📦 在庫状況分布:")
    for status, count in df['在庫状況'].value_counts().items():
        print(f"  {status}: {count} 件")
    
    # ファイル出力
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = args.output or f"chiikawa_products_{timestamp}"
    
    if args.format in ['csv', 'both']:
        csv_filename = f"{base_filename}.csv"
        save_to_csv(all_products, csv_filename)
    
    if args.format in ['excel', 'both']:
        excel_filename = f"{base_filename}.xlsx"
        save_to_excel(all_products, excel_filename)

if __name__ == "__main__":
    main()