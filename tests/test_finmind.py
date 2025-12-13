from FinMind.data import DataLoader
import time
import os
from dotenv import load_dotenv

load_dotenv()
api = DataLoader()
api.login_by_token(api_token=os.getenv('Finmind_token'))

start_time = time.time()

data = api.taiwan_stock_daily(
    stock_id='6163',
    start_date='2023-01-01',
    end_date='2024-12-31'
)

end_time = time.time()

print(f"資料筆數: {len(data)}")
print(f"\n前5筆:")
print(data.head())
print(f"\n後5筆:")
print(data.tail())
print(f"\n花費時間: {end_time - start_time:.2f} 秒")
