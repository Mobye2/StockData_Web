import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

url = 'https://tw.stock.yahoo.com/rank/turnover'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# 找到所有包含股票資訊的 li 標籤
stock_items = soup.find_all('li', class_='List(n)')

stocks = []
for item in stock_items:
    # 找股票名稱和代碼
    name_div = item.find('div', class_=re.compile('Lh\\(20px\\) Fw\\(600\\)'))
    code_span = item.find('span', class_=re.compile('Fz\\(14px\\) C\\(#979ba7\\)'))
    
    if name_div and code_span:
        name = name_div.text.strip()
        code_text = code_span.text.strip()
        # 移除 .TW 或 .TWO 後綴
        code = code_text.replace('.TW', '').replace('.TWO', '')
        
        stocks.append({
            'code': code,
            'name': name
        })

# 轉換為 DataFrame
stock_list = pd.DataFrame(stocks)

# 儲存為 CSV
stock_list.to_csv('stock_list.csv', index=False, encoding='utf-8-sig')

print(f"已更新 {len(stock_list)} 支股票")
print(stock_list.head(10))
