# twstock 台灣股市股票價格擷取套件

## 專案概述
- **專案名稱**: twstock
- **版本**: 1.4.0
- **作者**: Louie Lu
- **授權**: MIT License
- **GitHub**: https://github.com/mlouielu/twstock
- **文檔**: http://twstock.readthedocs.io/zh_TW/latest

## 功能特色
擷取台灣證券交易所之股價資料，重新製作 toomore/grs 之功能

### 資料來源
- 證券交易所 (TWSE): http://www.twse.com.tw
- 證券櫃台買賣中心 (TPEX): http://www.tpex.org.tw

**注意**: TWSE 有 request limit，每 5 秒鐘 3 個 request，超過會被 ban

## 系統需求
- Python 3.5+
- requests
- lxml (可選)

## 安裝方式

### 透過 PyPI
```bash
python -m pip install --user twstock
```

### 透過原始碼
```bash
git clone https://github.com/mlouielu/twstock
cd twstock
pipenv install
```

## 核心模組

### 1. Stock 類別 (stock.py)
主要的股票資料擷取類別

**主要功能**:
- 擷取股票歷史資料
- 支援 TWSE 和 TPEX 兩個交易所
- 提供多種資料屬性存取

**重要屬性**:
- `price`: 收盤價列表
- `capacity`: 成交量列表
- `high`: 最高價列表
- `low`: 最低價列表
- `open`: 開盤價列表
- `date`: 日期列表
- `change`: 漲跌幅列表

**重要方法**:
- `fetch(year, month)`: 擷取指定年月資料
- `fetch_from(year, month)`: 擷取從指定年月至今的資料
- `fetch_31()`: 擷取最近31天資料

### 2. 即時資料模組 (realtime.py)
提供即時股票資訊查詢

**主要功能**:
- 擷取即時股價
- 支援單檔或多檔查詢
- 提供買賣五檔資訊

### 3. 技術分析模組 (analytics.py)
提供股票技術分析功能

**Analytics 類別方法**:
- `moving_average(data, days)`: 計算移動平均
- `continuous(data)`: 計算連續天數
- `ma_bias_ratio(day1, day2)`: 計算乖離率

**BestFourPoint 類別**:
- 四大買賣點分析
- `best_four_point_to_buy()`: 判斷買點
- `best_four_point_to_sell()`: 判斷賣點

### 4. 股票代碼模組 (codes/)
- 包含 TWSE 和 TPEX 所有股票代碼
- 提供股票基本資訊查詢

## 使用範例

### 基本股票資料擷取
```python
from twstock import Stock

# 擷取台積電股價
stock = Stock('2330')
print(stock.price)      # 收盤價
print(stock.capacity)   # 成交量
print(stock.high)       # 最高價
```

### 技術分析
```python
# 計算移動平均
ma_5 = stock.moving_average(stock.price, 5)    # 5日均價
ma_20 = stock.moving_average(stock.price, 20)  # 20日均價

# 計算乖離率
bias = stock.ma_bias_ratio(5, 10)  # 5日、10日乖離值
```

### 四大買賣點分析
```python
from twstock import BestFourPoint

bfp = BestFourPoint(stock)
buy_signal = bfp.best_four_point_to_buy()    # 買點判斷
sell_signal = bfp.best_four_point_to_sell()  # 賣點判斷
```

### 即時資料查詢
```python
import twstock

# 單檔查詢
realtime_data = twstock.realtime.get('2330')

# 多檔查詢
multi_data = twstock.realtime.get(['2330', '2337', '2409'])
```

### 股票代碼查詢
```python
import twstock

# 查詢所有股票代碼
print(twstock.codes)

# 查詢特定股票資訊
print(twstock.codes['2330'])        # 台積電資訊
print(twstock.codes['2330'].name)   # 股票名稱
print(twstock.codes['2330'].start)  # 上市日期
```

## CLI 工具

### 四大買賣點判斷
```bash
twstock -b 2330 6223
```

### 股價資訊查詢
```bash
twstock -s 2330 6223
```

### 更新股票代碼
```bash
twstock -U
```

## 專案結構
```
twstock/
├── twstock/
│   ├── __init__.py          # 主要匯入模組
│   ├── stock.py             # 股票資料擷取
│   ├── realtime.py          # 即時資料
│   ├── analytics.py         # 技術分析
│   ├── proxy.py             # 代理伺服器支援
│   ├── codes/               # 股票代碼資料
│   └── cli/                 # 命令列工具
├── test/                    # 測試檔案
├── docs/                    # 文檔
└── README.md
```

## 開發注意事項

1. **API 限制**: 注意 TWSE 的請求頻率限制
2. **錯誤處理**: 網路請求可能失敗，需要適當的重試機制
3. **資料格式**: 不同交易所的資料格式略有差異
4. **代理支援**: 支援 HTTP 代理伺服器設定

## 相關資源
- 官方文檔: http://twstock.readthedocs.io/zh_TW/latest
- GitHub Issues: https://github.com/mlouielu/twstock/issues
- Gitter 聊天室: https://gitter.im/twstock/Lobby