"""
測試外資持股 API 回傳的欄位
"""

from FinMind.data import DataLoader
import os
from dotenv import load_dotenv

load_dotenv()
api = DataLoader()
api.login_by_token(api_token=os.getenv('Finmind_token'))

# 測試台積電
stock_id = '2330'
start_date = '2024-12-01'

print(f'測試股票: {stock_id}')
print(f'日期範圍: {start_date} ~ 今日\n')

# 測試1: taiwan_stock_holding_shares_per
print('=== 測試 taiwan_stock_holding_shares_per ===')
try:
    df = api.taiwan_stock_holding_shares_per(
        stock_id=stock_id,
        start_date=start_date
    )
    if df is not None and len(df) > 0:
        print(f'✓ 成功取得 {len(df)} 筆資料')
        print('欄位:', df.columns.tolist())
        print(df.head())
    else:
        print('✗ 無資料')
except Exception as e:
    print(f'✗ 錯誤: {e}')

# 測試2: taiwan_stock_shareholding
print('\n=== 測試 taiwan_stock_shareholding ===')
try:
    df2 = api.taiwan_stock_shareholding(
        stock_id=stock_id,
        start_date=start_date
    )
    if df2 is not None and len(df2) > 0:
        print(f'✓ 成功取得 {len(df2)} 筆資料')
        print('欄位:', df2.columns.tolist())
        print(df2.head())
    else:
        print('✗ 無資料')
except Exception as e:
    print(f'✗ 錯誤: {e}')
