"""
可重用的「單檔股票抓取」核心邏輯（供網站 API 與腳本共用）

抽取自 fetch_all_stocks.py（K線）與 fetch_chip_data.py（籌碼），
行為與原本腳本一致，差別只在改成「針對單一股票代號」的函式形式，
方便 web_app.py 針對使用者「指定的股票」逐檔抓取。

需要環境變數 Finmind_token（與現有腳本一致，注意是小寫開頭）。
"""

import sqlite3
import time
from datetime import datetime, timedelta

DB_PATH = "stock.db"

# K線表的完整欄位定義（與 fetch_all_stocks.py 一致）
_CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS {table} (
        日期 TEXT PRIMARY KEY,
        開盤價 REAL,
        最高價 REAL,
        最低價 REAL,
        收盤價 REAL,
        成交量 INTEGER,
        成交金額 INTEGER,
        漲跌 REAL,
        成交筆數 INTEGER,
        融資買進 INTEGER,
        融資賣出 INTEGER,
        融券買進 INTEGER,
        融券賣出 INTEGER,
        外資買賣超 INTEGER,
        投信買賣超 INTEGER,
        自營商買賣超 INTEGER,
        外資持股比 REAL
    )
"""

_CHIP_COLUMNS = [
    "融資買進 INTEGER", "融資賣出 INTEGER", "融券買進 INTEGER", "融券賣出 INTEGER",
    "外資買賣超 INTEGER", "投信買賣超 INTEGER", "自營商買賣超 INTEGER", "外資持股比 REAL",
]


def _get_api():
    """建立 FinMind DataLoader 並登入（讀取環境變數 Finmind_token）。"""
    import os
    from FinMind.data import DataLoader
    from dotenv import load_dotenv
    load_dotenv()
    token = os.getenv("Finmind_token")
    api = DataLoader()
    if token:
        api.login_by_token(api_token=token)
    return api


def get_stock_name(api, code):
    """用 FinMind 查股票中文名稱；查不到則回傳空字串。"""
    try:
        info = api.taiwan_stock_info()
        row = info[info["stock_id"] == str(code)]
        if len(row) > 0:
            return str(row.iloc[0]["stock_name"])
    except Exception as e:
        print(f"  查詢股票名稱失敗 {code}: {e}", flush=True)
    return ""


def _target_date():
    """決定抓取的結束日期（20點後用今天，否則用昨天），與原腳本一致。"""
    now = datetime.now()
    return now.date() if now.hour >= 20 else (now - timedelta(days=1)).date()


def fetch_one_kline(api, code, start_date="2021-01-01", name=None):
    """
    抓取單一股票的 K 線（OHLCV）資料並寫入 stock_{code} 表，同步更新 stock_list。
    增量：若表內已有資料，從最後一天的隔天開始抓。
    回傳 dict：{code, name, inserted, status, message}
    """
    code = str(code).strip()
    table = f"stock_{code}"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(_CREATE_TABLE_SQL.format(table=table))

        # 查最後一筆日期，決定增量起點
        cursor.execute(f"SELECT MAX(日期) FROM {table}")
        last_date = cursor.fetchone()[0]
        end_date = _target_date()

        if last_date:
            last_dt = datetime.strptime(last_date, "%Y-%m-%d")
            if last_dt.date() >= end_date:
                conn.close()
                return {"code": code, "name": name or "", "inserted": 0,
                        "status": "skip", "message": f"已是最新（{last_date}）"}
            fetch_start = (last_dt + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            fetch_start = start_date

        df = api.taiwan_stock_daily(
            stock_id=code,
            start_date=fetch_start,
            end_date=end_date.strftime("%Y-%m-%d"),
        )

        if df is None or len(df) == 0:
            conn.close()
            return {"code": code, "name": name or "", "inserted": 0,
                    "status": "nodata", "message": "無資料（可能已下市或暫停交易）"}

        inserted = 0
        for _, row in df.iterrows():
            cursor.execute(f"""
                INSERT OR REPLACE INTO {table}
                (日期, 開盤價, 最高價, 最低價, 收盤價, 成交量, 成交金額, 漲跌, 成交筆數)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["date"], row["open"], row["max"], row["min"], row["close"],
                row["Trading_Volume"], row["Trading_money"], row["spread"],
                row["Trading_turnover"],
            ))
            inserted += 1

        # 更新 stock_list（讓新股票出現在選單）
        if name:
            cursor.execute(
                "INSERT OR REPLACE INTO stock_list (code, name) VALUES (?, ?)",
                (code, name),
            )

        conn.commit()
        conn.close()
        return {"code": code, "name": name or "", "inserted": inserted,
                "status": "ok", "message": f"新增/更新 {inserted} 筆"}
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"code": code, "name": name or "", "inserted": 0,
                "status": "fail", "message": str(e)}


def _add_chip_columns(cursor, table):
    for col in _CHIP_COLUMNS:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col}")
        except Exception:
            pass


def fetch_one_chip(api, code, start_date="2021-01-01"):
    """
    抓取單一股票的籌碼（融資融券、三大法人、外資持股比）並更新 stock_{code} 表。
    沿用 fetch_chip_data.py 的欄位對應與寫入邏輯。
    回傳 dict：{code, updated, status, message}
    """
    code = str(code).strip()
    table = f"stock_{code}"

    # 抓三種籌碼資料
    def _try(fn):
        try:
            df = fn()
            return df if (df is not None and len(df) > 0) else None
        except Exception:
            return None

    margin_df = _try(lambda: api.taiwan_stock_margin_purchase_short_sale(
        stock_id=code, start_date=start_date))
    inst_df = _try(lambda: api.taiwan_stock_institutional_investors(
        stock_id=code, start_date=start_date))
    foreign_df = _try(lambda: api.taiwan_stock_shareholding(
        stock_id=code, start_date=start_date))

    if margin_df is None and inst_df is None and foreign_df is None:
        return {"code": code, "updated": 0, "status": "nodata", "message": "無籌碼資料"}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(_CREATE_TABLE_SQL.format(table=table))
        _add_chip_columns(cursor, table)

        updated = 0

        # 收集所有需要處理的日期，缺的先建空記錄
        all_dates = set()
        if margin_df is not None:
            all_dates.update(margin_df["date"].tolist())
        if inst_df is not None:
            all_dates.update(inst_df["date"].unique().tolist())
        if foreign_df is not None:
            all_dates.update(foreign_df["date"].tolist())

        for date in all_dates:
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE 日期 = ?", (date,))
            if cursor.fetchone()[0] == 0:
                cursor.execute(f"""
                    INSERT INTO {table} (日期, 開盤價, 最高價, 最低價, 收盤價, 成交量, 成交金額, 漲跌, 成交筆數)
                    VALUES (?, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
                """, (date,))
        conn.commit()

        # 融資融券
        if margin_df is not None:
            for _, row in margin_df.iterrows():
                cursor.execute(f"""
                    UPDATE {table} SET 融資買進=?, 融資賣出=?, 融券買進=?, 融券賣出=?
                    WHERE 日期=?
                """, (row.get("MarginPurchaseBuy", 0), row.get("MarginPurchaseSell", 0),
                      row.get("ShortSaleBuy", 0), row.get("ShortSaleSell", 0), row.get("date")))
                updated += cursor.rowcount

        # 三大法人
        if inst_df is not None:
            for date in inst_df["date"].unique():
                dd = inst_df[inst_df["date"] == date]
                fo = dd[dd["name"] == "Foreign_Investor"]
                tr = dd[dd["name"] == "Investment_Trust"]
                de = dd[dd["name"] == "Dealer_self"]
                fo_net = int(fo["buy"].iloc[0] - fo["sell"].iloc[0]) if len(fo) > 0 else 0
                tr_net = int(tr["buy"].iloc[0] - tr["sell"].iloc[0]) if len(tr) > 0 else 0
                de_net = int(de["buy"].iloc[0] - de["sell"].iloc[0]) if len(de) > 0 else 0
                cursor.execute(f"""
                    UPDATE {table} SET 外資買賣超=?, 投信買賣超=?, 自營商買賣超=?
                    WHERE 日期=?
                """, (fo_net, tr_net, de_net, date))
                updated += cursor.rowcount

        # 外資持股比
        if foreign_df is not None:
            for _, row in foreign_df.iterrows():
                value = row.get("ForeignInvestmentRemainRatio")
                if value is not None:
                    cursor.execute(f"""
                        UPDATE {table} SET 外資持股比=? WHERE 日期=?
                    """, (value, row.get("date")))
                    updated += cursor.rowcount

        conn.commit()
        conn.close()
        return {"code": code, "updated": updated, "status": "ok",
                "message": f"更新 {updated} 筆籌碼"}
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"code": code, "updated": 0, "status": "fail", "message": str(e)}


def fetch_stocks(codes, start_date="2021-01-01", fetch_kline=True,
                 fetch_chip=False, delay=2.0, name_lookup=True):
    """
    針對指定股票代號清單逐檔抓取。
    回傳每檔的結果列表。
    """
    api = _get_api()
    results = []
    for code in codes:
        code = str(code).strip()
        if not code:
            continue
        entry = {"code": code, "name": "", "kline": None, "chip": None, "status": "ok"}

        # 查名稱（供寫入 stock_list / 顯示）
        name = get_stock_name(api, code) if name_lookup else ""
        entry["name"] = name

        if fetch_kline:
            k = fetch_one_kline(api, code, start_date=start_date, name=name)
            entry["kline"] = k["message"]
            if k["status"] == "fail":
                entry["status"] = "fail"

        if fetch_chip:
            c = fetch_one_chip(api, code, start_date=start_date)
            entry["chip"] = c["message"]
            if c["status"] == "fail":
                entry["status"] = "fail"

        results.append(entry)
        time.sleep(delay)  # 禮貌延遲，避免打太快

    return results
