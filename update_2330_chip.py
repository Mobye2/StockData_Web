from fetch_chip_data import fetch_margin_data, fetch_institutional_data, fetch_foreign_holding, save_chip_data

stock_id = '2330'
print(f'更新 {stock_id} 籌碼資料...')

margin_df = fetch_margin_data(stock_id, '2024-01-01')
institutional_df = fetch_institutional_data(stock_id, '2024-01-01')
foreign_df = fetch_foreign_holding(stock_id, '2024-01-01')

print(f'融資融券: {len(margin_df) if margin_df is not None else 0} 筆')
print(f'三大法人: {len(institutional_df["date"].unique()) if institutional_df is not None else 0} 天')
print(f'外資持股: {len(foreign_df) if foreign_df is not None else 0} 筆')

updated = save_chip_data(stock_id, margin_df, institutional_df, foreign_df)
print(f'完成！更新 {updated} 筆')

# 驗證
import sqlite3
conn = sqlite3.connect('stock.db')
cursor = conn.cursor()
cursor.execute('SELECT 日期, 外資買賣超, 投信買賣超, 自營商買賣超 FROM stock_2330 WHERE 日期="2024-12-02"')
print(f'\n驗證 2024-12-02: {cursor.fetchone()}')
conn.close()
