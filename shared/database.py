"""共用資料庫連接模組"""
import sqlite3
import os
from typing import Optional, List, Dict, Any

class DatabaseManager:
    def __init__(self, db_path: str = "stock.db"):
        self.db_path = db_path
    
    def get_connection(self) -> sqlite3.Connection:
        """取得資料庫連接"""
        return sqlite3.connect(self.db_path)
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """執行查詢並返回結果"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """執行更新操作並返回影響的行數"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount