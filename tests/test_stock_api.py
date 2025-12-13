import sys
import os
sys.path.append(os.path.join(os.getcwd(), '..', 'twstock'))

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from twstock import Stock

# 測試幾支可能有問題的股票
test_stocks = [
    ('6163', '華電網'),
    ('4979', '華星光'),
    ('3105', '穩懋'),
    ('2330', '台積電'),  # 對照組，確定有資料
]

print("測試 twstock API")
print("=" * 80)

for code, name in test_stocks:
    print(f"\n測試 {code} {name}:")
    print(f"  建立 Stock 物件...")
    
    try:
        stock = Stock(code)
        print(f"  呼叫 fetch_from(2024, 8)...")
        stock.fetch_from(2024, 8)
        
        print(f"  API 回應完成")
        print(f"  stock.data 類型: {type(stock.data)}")
        print(f"  stock.data 長度: {len(stock.data) if stock.data else 0}")
        
        if stock.data and len(stock.data) > 0:
            print(f"  [OK] 有資料！共 {len(stock.data)} 筆")
            print(f"  第一筆: {stock.data[0].date} - 收盤價: {stock.data[0].close}")
            print(f"  最後一筆: {stock.data[-1].date} - 收盤價: {stock.data[-1].close}")
        else:
            print(f"  [NG] 無資料")
            print(f"  stock.data 內容: {stock.data}")
            
            # 嘗試不同的時間範圍
            print(f"\n  嘗試更早的時間 (2021, 1)...")
            stock2 = Stock(code)
            stock2.fetch_from(2021, 1)
            if stock2.data and len(stock2.data) > 0:
                print(f"  [OK] 從 2021/1 開始有資料！共 {len(stock2.data)} 筆")
            else:
                print(f"  [NG] 從 2021/1 開始也無資料")
                
    except Exception as e:
        print(f"  [FAIL] 錯誤: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("測試完成")
