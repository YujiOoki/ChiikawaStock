"""
データ処理・分析モジュール
Data Processing and Analysis Module
"""

import logging
from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

import pandas as pd
from utils import clean_text


class DataProcessor:
    """商品データの処理・分析・出力クラス"""
    
    def __init__(self, products_data: List[Dict[str, Any]]):
        self.products_data = products_data
        self.df = None
        self.logger = logging.getLogger(__name__)
        self._create_dataframe()
    
    def _create_dataframe(self):
        """商品データからDataFrameを作成"""
        if not self.products_data:
            self.df = pd.DataFrame()
            return
        
        try:
            self.df = pd.DataFrame(self.products_data)
            
            # データ型を最適化
            if 'price' in self.df.columns:
                self.df['price'] = pd.to_numeric(self.df['price'], errors='coerce')
            
            if 'extracted_at' in self.df.columns:
                self.df['extracted_at'] = pd.to_datetime(self.df['extracted_at'])
            
            self.logger.info(f"DataFrame作成完了: {len(self.df)} 行, {len(self.df.columns)} 列")
            
        except Exception as e:
            self.logger.error(f"DataFrame作成エラー: {str(e)}")
            self.df = pd.DataFrame()
    
    def process_data(self) -> pd.DataFrame:
        """データの処理・クリーニング・拡張"""
        if self.df.empty:
            return self.df
        
        try:
            # 重複除去
            initial_count = len(self.df)
            self.df = self.df.drop_duplicates(subset=['id', 'url'], keep='first')
            if len(self.df) < initial_count:
                self.logger.info(f"重複商品を除去: {initial_count - len(self.df)} 件")
            
            # テキストのクリーニング
            text_columns = ['title', 'description', 'detailed_title']
            for col in text_columns:
                if col in self.df.columns:
                    self.df[col] = self.df[col].apply(lambda x: clean_text(x) if pd.notna(x) else x)
            
            # カテゴリ分析
            self._analyze_categories()
            
            # 価格帯分析
            self._analyze_price_ranges()
            
            # 在庫状況の統一
            self._standardize_stock_status()
            
            # 商品名からキーワード抽出
            self._extract_keywords()
            
            self.logger.info("データ処理完了")
            
        except Exception as e:
            self.logger.error(f"データ処理エラー: {str(e)}")
        
        return self.df
    
    def _analyze_categories(self):
        """カテゴリ分析を実行"""
        if 'collection' not in self.df.columns:
            return
        
        # コレクション別統計
        collection_stats = self.df.groupby('collection').agg({
            'id': 'count',
            'price': ['mean', 'min', 'max'],
            'stock_status': lambda x: x.value_counts().to_dict()
        }).round(2)
        
        self.collection_stats = collection_stats
    
    def _analyze_price_ranges(self):
        """価格帯分析を実行"""
        if 'price' not in self.df.columns or self.df['price'].isna().all():
            return
        
        # 価格帯の定義
        price_ranges = [
            (0, 500, '500円未満'),
            (500, 1000, '500-1000円'),
            (1000, 2000, '1000-2000円'),
            (2000, 5000, '2000-5000円'),
            (5000, 10000, '5000-10000円'),
            (10000, float('inf'), '10000円以上')
        ]
        
        def categorize_price(price):
            if pd.isna(price):
                return '価格不明'
            for min_price, max_price, label in price_ranges:
                if min_price <= price < max_price:
                    return label
            return '価格不明'
        
        self.df['price_range'] = self.df['price'].apply(categorize_price)
    
    def _standardize_stock_status(self):
        """在庫状況の表記を統一"""
        if 'stock_status' not in self.df.columns:
            return
        
        status_mapping = {
            'in_stock': '在庫あり',
            'sold_out': '売り切れ',
            'new_items': '新着商品',
            'pre_order': '予約商品'
        }
        
        self.df['stock_status_ja'] = self.df['stock_status'].map(status_mapping).fillna('不明')
    
    def _extract_keywords(self):
        """商品名からキーワードを抽出"""
        if 'title' not in self.df.columns:
            return
        
        # よく使われるキーワードを抽出
        keywords = []
        for title in self.df['title'].dropna():
            if 'ぬいぐるみ' in title:
                keywords.append('ぬいぐるみ')
            if 'マスコット' in title:
                keywords.append('マスコット')
            if 'フィギュア' in title:
                keywords.append('フィギュア')
            if 'グッズ' in title:
                keywords.append('グッズ')
            if 'ステッカー' in title or 'シール' in title:
                keywords.append('ステッカー・シール')
            if 'バッグ' in title:
                keywords.append('バッグ')
            if 'Tシャツ' in title or 'シャツ' in title:
                keywords.append('アパレル')
        
        # キーワード統計を保存
        self.keyword_stats = Counter(keywords)
    
    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        if self.df is None or self.df.empty:
            return {}
        
        stats = {
            'total_products': len(self.df),
            'collections_count': self.df['collection'].nunique() if 'collection' in self.df.columns else 0,
            'stock_status_distribution': self.df['stock_status_ja'].value_counts().to_dict() if 'stock_status_ja' in self.df.columns else {},
            'price_statistics': {
                'mean': self.df['price'].mean() if 'price' in self.df.columns else 0,
                'median': self.df['price'].median() if 'price' in self.df.columns else 0,
                'min': self.df['price'].min() if 'price' in self.df.columns else 0,
                'max': self.df['price'].max() if 'price' in self.df.columns else 0,
            } if 'price' in self.df.columns and not self.df['price'].isna().all() else {},
            'extraction_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if hasattr(self, 'keyword_stats'):
            stats['top_keywords'] = dict(self.keyword_stats.most_common(10))
        
        if 'price_range' in self.df.columns:
            stats['price_range_distribution'] = self.df['price_range'].value_counts().to_dict()
        
        return stats
    
    def export_to_csv(self, filename: str):
        """CSVファイルに出力"""
        try:
            if self.df is None or self.df.empty:
                self.logger.warning("出力するデータがありません")
                return
            
            # 出力用データフレームを準備
            output_df = self.df.copy()
            
            # 日本語列名を追加
            column_mapping = {
                'id': '商品ID',
                'title': '商品名',
                'url': '商品URL',
                'price': '価格',
                'collection': 'コレクション',
                'stock_status_ja': '在庫状況',
                'price_range': '価格帯',
                'extracted_at': '取得日時'
            }
            
            # 出力列を選択・並び替え
            output_columns = []
            for eng_col, ja_col in column_mapping.items():
                if eng_col in output_df.columns:
                    output_df[ja_col] = output_df[eng_col]
                    output_columns.append(ja_col)
            
            # 詳細情報があれば追加
            detail_columns = ['detailed_title', 'description', 'sku']
            for col in detail_columns:
                if col in output_df.columns:
                    output_columns.append(col)
            
            # CSV出力
            output_df[output_columns].to_csv(
                filename, 
                index=False, 
                encoding='utf-8-sig'  # Excel対応
            )
            
            self.logger.info(f"CSVファイル出力完了: {filename}")
            
        except Exception as e:
            self.logger.error(f"CSV出力エラー: {str(e)}")
    
    def export_to_excel(self, filename: str):
        """Excelファイルに出力"""
        try:
            if self.df is None or self.df.empty:
                self.logger.warning("出力するデータがありません")
                return
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # メインデータシート
                self._write_main_sheet(writer)
                
                # 統計シート
                self._write_statistics_sheet(writer)
                
                # コレクション別シート
                self._write_collection_sheets(writer)
            
            self.logger.info(f"Excelファイル出力完了: {filename}")
            
        except Exception as e:
            self.logger.error(f"Excel出力エラー: {str(e)}")
    
    def _write_main_sheet(self, writer):
        """メインデータシートを書き込み"""
        if self.df is None:
            return
        output_df = self.df.copy()
        
        # 日本語列名を設定
        column_mapping = {
            'id': '商品ID',
            'title': '商品名',
            'url': '商品URL',
            'price': '価格',
            'collection': 'コレクション',
            'stock_status_ja': '在庫状況',
            'price_range': '価格帯',
            'extracted_at': '取得日時'
        }
        
        for eng_col, ja_col in column_mapping.items():
            if eng_col in output_df.columns:
                output_df[ja_col] = output_df[eng_col]
        
        # 出力列を選択
        output_columns = [ja_col for eng_col, ja_col in column_mapping.items() if eng_col in output_df.columns]
        
        output_df[output_columns].to_excel(writer, sheet_name='全商品データ', index=False)
    
    def _write_statistics_sheet(self, writer):
        """統計シートを書き込み"""
        stats = self.get_statistics()
        
        # 統計データをDataFrameに変換
        stats_data = []
        
        stats_data.append(['項目', '値'])
        stats_data.append(['総商品数', stats.get('total_products', 0)])
        stats_data.append(['コレクション数', stats.get('collections_count', 0)])
        stats_data.append(['取得日時', stats.get('extraction_time', '')])
        
        # 在庫状況分布
        stats_data.append(['', ''])
        stats_data.append(['在庫状況', '商品数'])
        for status, count in stats.get('stock_status_distribution', {}).items():
            stats_data.append([status, count])
        
        # 価格統計
        price_stats = stats.get('price_statistics', {})
        if price_stats:
            stats_data.append(['', ''])
            stats_data.append(['価格統計', ''])
            stats_data.append(['平均価格', f"¥{price_stats.get('mean', 0):.0f}"])
            stats_data.append(['最高価格', f"¥{price_stats.get('max', 0):.0f}"])
            stats_data.append(['最低価格', f"¥{price_stats.get('min', 0):.0f}"])
        
        # 価格帯分布
        price_range_dist = stats.get('price_range_distribution', {})
        if price_range_dist:
            stats_data.append(['', ''])
            stats_data.append(['価格帯', '商品数'])
            for price_range, count in price_range_dist.items():
                stats_data.append([price_range, count])
        
        stats_df = pd.DataFrame(stats_data)
        stats_df.to_excel(writer, sheet_name='統計情報', index=False, header=False)
    
    def _write_collection_sheets(self, writer):
        """コレクション別シートを書き込み"""
        if 'collection' not in self.df.columns:
            return
        
        for collection in self.df['collection'].unique()[:10]:  # 最大10コレクション
            collection_df = self.df[self.df['collection'] == collection].copy()
            
            # 列を整理
            columns_to_include = ['title', 'price', 'stock_status_ja', 'url']
            columns_to_include = [col for col in columns_to_include if col in collection_df.columns]
            
            if columns_to_include:
                sheet_name = collection[:30]  # シート名は30文字まで
                collection_df[columns_to_include].to_excel(
                    writer, 
                    sheet_name=sheet_name, 
                    index=False
                )
    
    def print_statistics(self):
        """統計情報をコンソールに表示"""
        stats = self.get_statistics()
        
        print("\n" + "="*50)
        print("📊 スクレイピング結果統計")
        print("="*50)
        
        print(f"🎯 総商品数: {stats.get('total_products', 0):,} 件")
        print(f"📂 コレクション数: {stats.get('collections_count', 0)} 個")
        print(f"⏰ 取得日時: {stats.get('extraction_time', '')}")
        
        # 在庫状況分布
        stock_dist = stats.get('stock_status_distribution', {})
        if stock_dist:
            print("\n📦 在庫状況分布:")
            for status, count in stock_dist.items():
                percentage = (count / stats['total_products']) * 100
                print(f"  {status}: {count:,} 件 ({percentage:.1f}%)")
        
        # 価格統計
        price_stats = stats.get('price_statistics', {})
        if price_stats:
            print("\n💰 価格統計:")
            print(f"  平均価格: ¥{price_stats.get('mean', 0):,.0f}")
            print(f"  最高価格: ¥{price_stats.get('max', 0):,.0f}")
            print(f"  最低価格: ¥{price_stats.get('min', 0):,.0f}")
        
        # トップキーワード
        top_keywords = stats.get('top_keywords', {})
        if top_keywords:
            print("\n🔤 人気キーワード:")
            for keyword, count in list(top_keywords.items())[:5]:
                print(f"  {keyword}: {count} 件")
        
        print("="*50 + "\n")
