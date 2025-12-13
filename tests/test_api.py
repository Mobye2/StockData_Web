import requests
import json

print("測試 API 端點")
print("=" * 80)

# 測試股票列表 API
print("\n1. 測試 /api/stocks")
try:
    response = requests.get('http://localhost:5000/api/stocks')
    if response.status_code == 200:
        stocks = response.json()
        print(f"   成功！返回 {len(stocks)} 支股票")
        # 檢查鴻海是否在列表中
        honhai = next((s for s in stocks if s['code'] == '2317'), None)
        if honhai:
            print(f"   ✓ 鴻海在列表中: {honhai}")
        else:
            print(f"   ✗ 鴻海不在列表中")
        # 顯示前5支
        print(f"\n   前5支股票:")
        for stock in stocks[:5]:
            print(f"     {stock['code']} {stock['name']}")
    else:
        print(f"   失敗！狀態碼: {response.status_code}")
except Exception as e:
    print(f"   錯誤: {e}")
    print("   請確認 Flask 應用程式是否正在運行 (python web_app.py)")

# 測試鴻海資料 API
print("\n2. 測試 /api/data/2317 (鴻海)")
try:
    response = requests.get('http://localhost:5000/api/data/2317')
    if response.status_code == 200:
        data = response.json()
        print(f"   成功！返回 {len(data)} 筆資料")
        if len(data) > 0:
            print(f"\n   最新一筆資料:")
            latest = data[-1]
            print(f"     日期: {latest.get('日期')}")
            print(f"     開盤價: {latest.get('開盤價')}")
            print(f"     收盤價: {latest.get('收盤價')}")
            print(f"     成交量: {latest.get('成交量')}")
    else:
        print(f"   失敗！狀態碼: {response.status_code}")
except Exception as e:
    print(f"   錯誤: {e}")

print("\n" + "=" * 80)
