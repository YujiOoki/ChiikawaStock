#!/usr/bin/env python3
"""
ちいかわオンラインマーケット商品在庫情報スクレイピングツール
Chiikawa Online Market Product Inventory Scraping Tool

使用方法:
python main.py --format csv --output products.csv
python main.py --format excel --output products.xlsx --collections all
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from scraper import ChiikawaMarketScraper
from data_processor import DataProcessor
from config import ScrapingConfig


def setup_logging(verbose=False):
    """ロギング設定を初期化"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'scraping_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )


def parse_arguments():
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(
        description='ちいかわオンラインマーケット商品在庫情報スクレイピングツール',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python main.py --format csv
  python main.py --format excel --output products.xlsx
  python main.py --collections newitems,chiikawarestaurant --format both
  python main.py --status in_stock,sold_out --verbose
        """
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['csv', 'excel', 'both'],
        default='csv',
        help='出力形式を選択 (デフォルト: csv)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='出力ファイル名 (デフォルト: 自動生成)'
    )
    
    parser.add_argument(
        '--collections', '-c',
        type=str,
        default='all',
        help='取得するコレクション (カンマ区切り、デフォルト: all)'
    )
    
    parser.add_argument(
        '--status', '-s',
        type=str,
        default='all',
        help='フィルタする在庫状況 (in_stock,sold_out,new_items、デフォルト: all)'
    )
    
    parser.add_argument(
        '--max-products', '-m',
        type=int,
        default=None,
        help='取得する最大商品数 (デフォルト: 制限なし)'
    )
    
    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=1.0,
        help='リクエスト間の遅延秒数 (デフォルト: 1.0)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='詳細なログ出力を有効化'
    )
    
    return parser.parse_args()


def generate_output_filename(format_type, collections):
    """出力ファイル名を自動生成"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    collections_str = collections.replace(',', '_') if collections != 'all' else 'all'
    
    if format_type == 'csv':
        return f"chiikawa_products_{collections_str}_{timestamp}.csv"
    elif format_type == 'excel':
        return f"chiikawa_products_{collections_str}_{timestamp}.xlsx"
    else:
        return f"chiikawa_products_{collections_str}_{timestamp}"


def main():
    """メイン実行関数"""
    args = parse_arguments()
    setup_logging(args.verbose)
    
    logger = logging.getLogger(__name__)
    logger.info("ちいかわオンラインマーケット スクレイピング開始")
    
    try:
        # 設定を初期化
        config = ScrapingConfig(
            delay=args.delay,
            max_products=args.max_products,
            collections=args.collections.split(',') if args.collections != 'all' else None,
            status_filter=args.status.split(',') if args.status != 'all' else None
        )
        
        # スクレイパーを初期化
        scraper = ChiikawaMarketScraper(config)
        
        # 商品データを取得
        logger.info("商品データの取得を開始...")
        products_data = scraper.scrape_all_products()
        
        if not products_data:
            logger.warning("取得できた商品データがありません")
            return
        
        logger.info(f"合計 {len(products_data)} 件の商品データを取得しました")
        
        # データ処理器を初期化
        processor = DataProcessor(products_data)
        
        # データを処理・分析
        processed_data = processor.process_data()
        
        # 出力ファイル名を決定
        if not args.output:
            base_filename = generate_output_filename(args.format, args.collections)
        else:
            base_filename = args.output
        
        # データを出力
        if args.format in ['csv', 'both']:
            csv_filename = base_filename if base_filename.endswith('.csv') else f"{Path(base_filename).stem}.csv"
            processor.export_to_csv(csv_filename)
            logger.info(f"CSVファイルを出力しました: {csv_filename}")
        
        if args.format in ['excel', 'both']:
            excel_filename = base_filename if base_filename.endswith('.xlsx') else f"{Path(base_filename).stem}.xlsx"
            processor.export_to_excel(excel_filename)
            logger.info(f"Excelファイルを出力しました: {excel_filename}")
        
        # 統計情報を表示
        processor.print_statistics()
        
        logger.info("スクレイピング処理が正常に完了しました")
        
    except KeyboardInterrupt:
        logger.info("ユーザーによって処理が中断されました")
        sys.exit(1)
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
