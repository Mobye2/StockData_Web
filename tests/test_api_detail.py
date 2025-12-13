import requests
import json

# 直接測試證交所 API
test_codes = ['6163', '3105', '2330']

print("直接測試證交所 API")
print("=" * 80)

for code in test_codes:
    print(f"\n測試 {code}:")
    
    # 證交所 API URL (2024年12月)
    url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date=20241201&stockNo={code}"
    
    try:
        print(f"  URL: {url}")
        response = requests.get(url, verify=False, timeout=10)
        print(f"  HTTP 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  回應 keys: {data.keys()}")
            
            if 'stat' in data:
                print(f"  stat: {data['stat']}")
            
            if 'data' in data:
                print(f"  data 筆數: {len(data['data'])}")
                if len(data['data']) > 0:
                    print(f"  [OK] 有資料")
                else:
                    print(f"  [NG] data 是空的")
            else:
                print(f"  [NG] 沒有 data 欄位")
            
            if 'notes' in data:
                print(f"  notes: {data['notes']}")
                
        else:
            print(f"  [FAIL] HTTP 錯誤")
            
    except Exception as e:
        print(f"  [FAIL] 異常: {e}")

print("\n" + "=" * 80)
