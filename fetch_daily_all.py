import requests
import sqlite3
import time
from datetime import datetime

def fetch_twse_all_stocks(date_str):
    """抓取上市股票當日所有資料"""
    url = f'https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date={date_str}&type=ALLBUT0999'
    response = requests.get(url)
    return response.json()

def fetch_tpex_all_stocks(date_str):
    """抓取上櫃股票當日所有資料"""
    # 轉換日期格式為民國年
    dt = datetime.strptime(date_str, '%Y%m%d')
    roc_date = f'{dt.year - 1911}/{dt.month:02d}/{dt.day:02d}'
    url = f'https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&d={roc_date}&se=AL'
    response = requests.get(url)
    return response.json()

# 使用範例
date = datetime.now().strftime('%Y%m%d')  # 今天日期 20240101

# 上市
twse_data = fetch_twse_all_stocks(date)
if twse_data.get('stat') == 'OK':
    print(f"上市股票數量: {len(twse_data['data9'])}")
    # data9 欄位: [代號, 名稱, 成交股數, 成交金額, 開盤價, 最高價, 最低價, 收盤價, 漲跌, 成交筆數, ...]
    for stock in twse_data['data9'][:3]:  # 顯示前3筆
        print(stock)

time.sleep(3)  # 避免請求過快

# 上櫃
tpex_data = fetch_tpex_all_stocks(date)
if tpex_data.get('aaData'):
    print(f"\n上櫃股票數量: {len(tpex_data['aaData'])}")
    # aaData 欄位: [代號, 名稱, 收盤價, 漲跌, 開盤價, 最高價, 最低價, 成交量(千股), ...]
    for stock in tpex_data['aaData'][:3]:
        print(stock)
