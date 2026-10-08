"""
stock.db 的 S3 同步工具（最小化）

做兩件事：
1. ensure_db()  —— 程式啟動時，從 S3 把 stock.db 下載到固定路徑 'stock.db'
2. upload_db()  —— 抓完資料後，把 'stock.db' 傳回 S3（覆蓋）

因為下載到固定路徑 'stock.db'，原本的 sqlite3.connect('stock.db') 完全不用改。

bucket 請保持「私有」，用 AWS 金鑰授權存取、不要公開，
這樣就不會被外部狂打，流量費只來自你自己的程式。

環境變數（寫在 .env 或 Codespaces Secrets）：
- STOCK_DB_S3_BUCKET : S3 bucket 名稱（留空則略過 S3，直接用本地 stock.db）
- STOCK_DB_S3_KEY    : 物件路徑（預設 stock.db）
- AWS_REGION         : 區域（預設 ap-northeast-1 東京）
- AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY : 由 boto3 自動讀取
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

DB_PATH = "stock.db"  # 固定路徑，與原本程式一致
S3_BUCKET = os.getenv("STOCK_DB_S3_BUCKET")
S3_KEY = os.getenv("STOCK_DB_S3_KEY", "stock.db")
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-1")


class S3NotConfigured(Exception):
    """未設定 S3（沒有 STOCK_DB_S3_BUCKET）。"""
    pass


def ensure_db(force=False):
    """
    從 S3 下載 stock.db 到固定路徑 'stock.db'。

    - force=False（預設）：本地已有 stock.db 就不下載（重啟 app 時省流量）；本地沒有才下載。
    - force=True：一律從 S3 重新下載最新版（網站「下載」按鈕用這個）。

    未設定 S3 時：
    - 抓資料腳本（force=False）：安靜略過，沿用本地檔案。
    - 網站按鈕（force=True）：丟出 S3NotConfigured，讓前端顯示「尚未設定 S3」。
    """
    if not S3_BUCKET:
        if force:
            raise S3NotConfigured("尚未設定 STOCK_DB_S3_BUCKET，無法從雲端下載。")
        return

    if not force and os.path.exists(DB_PATH):
        print(f"[db_config] 本地已有 {DB_PATH}，略過下載。")
        return

    import boto3
    s3 = boto3.client("s3", region_name=AWS_REGION)
    print(f"[db_config] 從 s3://{S3_BUCKET}/{S3_KEY} 下載 -> {DB_PATH}")
    s3.download_file(S3_BUCKET, S3_KEY, DB_PATH)
    print("[db_config] 下載完成。")


def upload_db():
    """把本地 stock.db 傳回 S3（覆蓋）。單人使用不會有並發覆蓋問題。"""
    if not S3_BUCKET:
        raise S3NotConfigured("尚未設定 STOCK_DB_S3_BUCKET，無法上傳到雲端。")
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"找不到本地 {DB_PATH}，無法上傳。")

    import boto3
    s3 = boto3.client("s3", region_name=AWS_REGION)
    print(f"[db_config] 上傳 {DB_PATH} -> s3://{S3_BUCKET}/{S3_KEY}")
    s3.upload_file(DB_PATH, S3_BUCKET, S3_KEY)
    print("[db_config] 上傳完成。")
