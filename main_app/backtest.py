import sqlite3
import pandas as pd
import os
from datetime import datetime

class BacktestStrategy:
    def __init__(self, stock_code, initial_capital=1000000):
        self.stock_code = stock_code
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0
        self.trades = []
        self.buy_records = []
        
    def load_data(self):
        import os
        # 強制使用根目錄的資料庫
        db_path = os.path.join(os.path.dirname(__file__), '..', 'stock.db')
        conn = sqlite3.connect(db_path)
        query = f"SELECT * FROM stock_{self.stock_code} ORDER BY 日期"
        self.df = pd.read_sql_query(query, conn)
        conn.close()
        return self.df
    
    def calculate_ma(self, period):
        return self.df['收盤價'].rolling(window=period).mean()
    
    def high_volume_filter(self, volume_period=20, volume_multiplier=3):
        self.df['Volume_MA'] = self.df['成交量'].rolling(window=volume_period).mean()
        self.df['High_Volume'] = self.df['成交量'] > (self.df['Volume_MA'] * volume_multiplier)
        return self.df['High_Volume']

    def combined_strategy(self, buy_strategies, sell_strategies, buy_logic='and', sell_logic='or'):
        buy_signals = []
        sell_signals = []
        
        for strategy_config in buy_strategies:
            strategy_type = strategy_config['type']
            params = strategy_config.get('params', {})
            
            if strategy_type == 'ma_crossover':
                ma_period = params.get('ma_period', 20)
                hold_days = params.get('hold_days', 3)
                self.df['MA'] = self.calculate_ma(ma_period)
                self.df['Above_MA'] = self.df['收盤價'] > self.df['MA']
                
                above_count = [0] * len(self.df)
                below_count = [0] * len(self.df)
                for i in range(1, len(self.df)):
                    if self.df.iloc[i]['Above_MA']:
                        above_count[i] = above_count[i-1] + 1
                        below_count[i] = 0
                    else:
                        below_count[i] = below_count[i-1] + 1
                        above_count[i] = 0
                
                buy_sig = [above_count[i] >= hold_days for i in range(len(self.df))]
                buy_signals.append(buy_sig)
            
            elif strategy_type == 'rsi':
                rsi_period = params.get('rsi_period', 14)
                oversold = params.get('oversold', 30)
                overbought = params.get('overbought', 70)
                
                delta = self.df['收盤價'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
                rs = gain / loss
                self.df['RSI'] = 100 - (100 / (1 + rs))
                
                buy_sig = [self.df.iloc[i]['RSI'] < oversold if not pd.isna(self.df.iloc[i]['RSI']) else False for i in range(len(self.df))]
                buy_signals.append(buy_sig)
            
            elif strategy_type == 'high_volume':
                volume_period = params.get('volume_period', 20)
                volume_multiplier = params.get('volume_multiplier', 3)
                high_vol = self.high_volume_filter(volume_period, volume_multiplier)
                buy_signals.append(high_vol.tolist())
            
            elif strategy_type == 'ma_slope':
                slope_threshold = params.get('slope_threshold', 0.2)
                hold_days = params.get('hold_days', 3)
                self.df['MA5'] = self.calculate_ma(5)
                self.df['MA10'] = self.calculate_ma(10)
                self.df['MA20'] = self.calculate_ma(20)
                self.df['MA20_slope'] = self.df['MA20'].diff()
                self.df['MA10_slope'] = self.df['MA10'].diff()
                
                above_count = [0] * len(self.df)
                for i in range(1, len(self.df)):
                    ma20_slope = self.df.iloc[i]['MA20_slope'] if not pd.isna(self.df.iloc[i]['MA20_slope']) else 0
                    if ma20_slope > slope_threshold:
                        above_count[i] = above_count[i-1] + 1
                    else:
                        above_count[i] = 0
                
                buy_sig = [above_count[i] >= hold_days for i in range(len(self.df))]
                buy_signals.append(buy_sig)
        
        for strategy_config in sell_strategies:
            strategy_type = strategy_config['type']
            params = strategy_config.get('params', {})
            
            if strategy_type == 'ma_crossover':
                ma_period = params.get('ma_period', 20)
                hold_days = params.get('hold_days', 3)
                self.df['MA'] = self.calculate_ma(ma_period)
                self.df['Above_MA'] = self.df['收盤價'] > self.df['MA']
                
                below_count = [0] * len(self.df)
                for i in range(1, len(self.df)):
                    if not self.df.iloc[i]['Above_MA']:
                        below_count[i] = below_count[i-1] + 1
                    else:
                        below_count[i] = 0
                
                sell_sig = [below_count[i] >= hold_days for i in range(len(self.df))]
                sell_signals.append(sell_sig)
            
            elif strategy_type == 'rsi':
                rsi_period = params.get('rsi_period', 14)
                overbought = params.get('overbought', 70)
                
                delta = self.df['收盤價'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
                rs = gain / loss
                self.df['RSI'] = 100 - (100 / (1 + rs))
                
                sell_sig = [self.df.iloc[i]['RSI'] > overbought if not pd.isna(self.df.iloc[i]['RSI']) else False for i in range(len(self.df))]
                sell_signals.append(sell_sig)
            
            elif strategy_type == 'high_volume':
                volume_period = params.get('volume_period', 20)
                volume_multiplier = params.get('volume_multiplier', 3)
                high_vol = self.high_volume_filter(volume_period, volume_multiplier)
                sell_signals.append(high_vol.tolist())
            
            elif strategy_type == 'ma_slope':
                self.df['MA5'] = self.calculate_ma(5)
                self.df['MA10'] = self.calculate_ma(10)
                self.df['MA10_slope'] = self.df['MA10'].diff()
                
                sell_sig = []
                for i in range(len(self.df)):
                    ma10_slope = self.df.iloc[i]['MA10_slope'] if not pd.isna(self.df.iloc[i]['MA10_slope']) else 0
                    ma5 = self.df.iloc[i]['MA5'] if not pd.isna(self.df.iloc[i]['MA5']) else 0
                    ma10 = self.df.iloc[i]['MA10'] if not pd.isna(self.df.iloc[i]['MA10']) else 0
                    
                    if i > 0:
                        prev_ma5 = self.df.iloc[i-1]['MA5'] if not pd.isna(self.df.iloc[i-1]['MA5']) else 0
                        prev_ma10 = self.df.iloc[i-1]['MA10'] if not pd.isna(self.df.iloc[i-1]['MA10']) else 0
                        cross_down = (prev_ma5 > prev_ma10 and ma5 < ma10)
                        sell_condition = (ma10_slope > 0 and cross_down)
                    else:
                        sell_condition = False
                    
                    sell_sig.append(sell_condition)
                
                sell_signals.append(sell_sig)
            
            elif strategy_type == 'ma_slope_down':
                slope_threshold = params.get('slope_threshold', -0.2)
                hold_days = params.get('hold_days', 3)
                self.df['MA20'] = self.calculate_ma(20)
                self.df['MA20_slope'] = self.df['MA20'].diff()
                
                below_count = [0] * len(self.df)
                for i in range(1, len(self.df)):
                    ma20_slope = self.df.iloc[i]['MA20_slope'] if not pd.isna(self.df.iloc[i]['MA20_slope']) else 0
                    if ma20_slope < slope_threshold:
                        below_count[i] = below_count[i-1] + 1
                    else:
                        below_count[i] = 0
                
                sell_sig = [below_count[i] >= hold_days for i in range(len(self.df))]
                sell_signals.append(sell_sig)
            
            elif strategy_type == 'profit_target':
                target_percent = params.get('target_percent', 10)
                sell_sig = [False] * len(self.df)
                sell_signals.append(sell_sig)
        
        equity_curve = []
        realized_profit = 0
        
        for i in range(len(self.df)):
            price = self.df.iloc[i]['收盤價']
            date = self.df.iloc[i]['日期']
            
            equity_curve.append({'日期': date, '已實現損益': realized_profit})
            
            if buy_logic == 'and':
                all_buy = all(signals[i] for signals in buy_signals) if buy_signals else False
            else:
                all_buy = any(signals[i] for signals in buy_signals) if buy_signals else False
            
            if sell_logic == 'and':
                all_sell = all(signals[i] for signals in sell_signals) if sell_signals else False
            else:
                all_sell = any(signals[i] for signals in sell_signals) if sell_signals else False
            
            # 檢查報酬率賣出(停利/停損)
            profit_target_sell = False
            if self.position > 0:
                has_profit_target = any(s['type'] == 'profit_target' for s in sell_strategies)
                if has_profit_target:
                    for strategy_config in sell_strategies:
                        if strategy_config['type'] == 'profit_target':
                            target_percent = float(strategy_config['params'].get('target_percent', 10))
                            total_cost = sum(r['金額'] for r in self.buy_records)
                            current_value = self.position * price
                            current_return = ((current_value - total_cost) / total_cost * 100) if total_cost > 0 else 0
                            # 正數為停利，負數為停損
                            if target_percent >= 0 and current_return >= target_percent:
                                profit_target_sell = True
                                break
                            elif target_percent < 0 and current_return <= target_percent:
                                profit_target_sell = True
                                break
            
            if all_buy and self.position == 0:
                # 固定買入1000股，不考慮資金限制
                shares = 1000
                cost = shares * price
                self.capital -= cost  # 允許資金變負數
                self.position += shares
                
                indicators = {}
                for strategy_config in buy_strategies:
                    if strategy_config['type'] == 'ma_slope':
                        slope_val = round(self.df.iloc[i]['MA20_slope'], 2) if not pd.isna(self.df.iloc[i]['MA20_slope']) else 0
                        threshold = strategy_config['params'].get('slope_threshold', 0.2)
                        indicators['MA20斜率'] = f"{slope_val}(閾:{threshold})"
                    elif strategy_config['type'] == 'rsi':
                        rsi_val = round(self.df.iloc[i]['RSI'], 2) if not pd.isna(self.df.iloc[i]['RSI']) else 0
                        indicators['RSI'] = rsi_val
                    elif strategy_config['type'] == 'high_volume':
                        vol_ratio = self.df.iloc[i]['成交量'] / self.df.iloc[i]['Volume_MA'] if not pd.isna(self.df.iloc[i]['Volume_MA']) and self.df.iloc[i]['Volume_MA'] > 0 else 0
                        indicators['量倍數'] = round(vol_ratio, 2)
                
                self.buy_records.append({'日期': date, '價格': price, '數量': shares, '金額': cost})
                self.trades.append({'日期': date, '類型': '買入', '價格': price, '數量': shares, '金額': cost, '餘額': self.capital, '指標': indicators})
            
            elif (all_sell or profit_target_sell) and self.position > 0:
                revenue = self.position * price
                total_cost = sum(r['金額'] for r in self.buy_records)
                profit = revenue - total_cost
                return_rate = (profit / total_cost * 100) if total_cost > 0 else 0
                realized_profit += profit
                
                self.capital += revenue
                if profit_target_sell:
                    for strategy_config in sell_strategies:
                        if strategy_config['type'] == 'profit_target':
                            target = strategy_config['params'].get('target_percent', 10)
                            sell_reason = f"{'停利' if target >= 0 else '停損'}{target}%"
                            break
                else:
                    sell_reason = '策略信號'
                self.trades.append({'日期': date, '類型': '賣出', '價格': price, '數量': self.position, '金額': revenue, '餘額': self.capital, '獲利': profit, '報酬率': return_rate, '買入記錄': self.buy_records.copy(), '賣出原因': sell_reason})
                self.position = 0
                self.buy_records = []
        
        if self.position > 0:
            last_price = self.df.iloc[-1]['收盤價']
            last_date = self.df.iloc[-1]['日期']
            revenue = self.position * last_price
            total_cost = sum(r['金額'] for r in self.buy_records)
            profit = revenue - total_cost
            return_rate = (profit / total_cost * 100) if total_cost > 0 else 0
            realized_profit += profit
            
            self.capital += revenue
            self.trades.append({'日期': last_date, '類型': '賣出', '價格': last_price, '數量': self.position, '金額': revenue, '餘額': self.capital, '獲利': profit, '報酬率': return_rate, '買入記錄': self.buy_records.copy()})
            self.position = 0
            equity_curve[-1]['已實現損益'] = realized_profit
        
        final_value = self.capital
        sell_trades = [t for t in self.trades if t['類型'] == '賣出']
        win_trades = [t for t in sell_trades if t['獲利'] > 0]
        win_rate = len(win_trades) / len(sell_trades) * 100 if len(sell_trades) > 0 else 0
        
        return {
            'trades': self.trades,
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'profit': final_value - self.initial_capital,
            'return_rate': (final_value - self.initial_capital) / self.initial_capital * 100,
            'equity_curve': equity_curve,
            'win_rate': win_rate,
            'total_trades': len(sell_trades),
            'win_trades': len(win_trades)
        }

    def combined_strategy_v2(self, buy_strategies, sell_strategies):
        """策略=多指標AND組合，多策略OR觸發"""
        buy_strategy_signals = []
        sell_strategy_signals = []
        
        # 處理買進策略（每個策略內的指標用AND）
        for strategy in buy_strategies:
            indicator_signals = []
            for indicator in strategy['indicators']:
                ind_type = indicator['type']
                params = indicator['params']
                
                if ind_type == 'ma_crossover':
                    short_window = params.get('short_window', 5)
                    long_window = params.get('long_window', 20)
                    self.df['MA_short'] = self.calculate_ma(short_window)
                    self.df['MA_long'] = self.calculate_ma(long_window)
                    # 黃金交叉：前一日短MA <= 長MA，當日短MA > 長MA
                    sig = []
                    for i in range(len(self.df)):
                        if i == 0:
                            sig.append(False)
                        else:
                            prev_short = self.df.iloc[i-1]['MA_short']
                            prev_long = self.df.iloc[i-1]['MA_long']
                            curr_short = self.df.iloc[i]['MA_short']
                            curr_long = self.df.iloc[i]['MA_long']
                            if pd.isna(prev_short) or pd.isna(prev_long) or pd.isna(curr_short) or pd.isna(curr_long):
                                sig.append(False)
                            else:
                                # 黃金交叉：前一日短MA在下方，當日短MA在上方
                                sig.append(prev_short <= prev_long and curr_short > curr_long)
                    indicator_signals.append(sig)
                
                elif ind_type == 'rsi':
                    period = params.get('period', 14)
                    buy_threshold = params.get('buy_threshold', 30)
                    delta = self.df['收盤價'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                    rs = gain / loss
                    self.df['RSI'] = 100 - (100 / (1 + rs))
                    sig = (self.df['RSI'] < buy_threshold).fillna(False).tolist()
                    indicator_signals.append(sig)
                
                elif ind_type == 'high_volume':
                    volume_period = params.get('volume_period', 20)
                    volume_multiplier = params.get('volume_multiplier', 2.0)
                    consecutive_days = params.get('consecutive_days', 1)
                    self.df['Volume_MA'] = self.df['成交量'].rolling(window=volume_period).mean()
                    count = [0] * len(self.df)
                    for i in range(1, len(self.df)):
                        vol_ma = self.df.iloc[i]['Volume_MA']
                        vol = self.df.iloc[i]['成交量']
                        if not pd.isna(vol_ma) and vol_ma > 0 and vol > vol_ma * volume_multiplier:
                            count[i] = count[i-1] + 1
                        else:
                            count[i] = 0
                    sig = [count[i] >= consecutive_days for i in range(len(self.df))]
                    indicator_signals.append(sig)
                
                elif ind_type == 'low_volume':
                    volume_period = params.get('volume_period', 20)
                    volume_multiplier = params.get('volume_multiplier', 0.5)
                    consecutive_days = params.get('consecutive_days', 1)
                    self.df['Volume_MA'] = self.df['成交量'].rolling(window=volume_period).mean()
                    count = [0] * len(self.df)
                    for i in range(1, len(self.df)):
                        vol_ma = self.df.iloc[i]['Volume_MA']
                        vol = self.df.iloc[i]['成交量']
                        if not pd.isna(vol_ma) and vol_ma > 0 and vol < vol_ma * volume_multiplier:
                            count[i] = count[i-1] + 1
                        else:
                            count[i] = 0
                    sig = [count[i] >= consecutive_days for i in range(len(self.df))]
                    indicator_signals.append(sig)
                
                elif ind_type == 'ma_above':
                    ma_period = params.get('ma_period', 20)
                    self.df['MA'] = self.calculate_ma(ma_period)
                    sig = (self.df['收盤價'] > self.df['MA']).fillna(False).tolist()
                    indicator_signals.append(sig)
                
                elif ind_type == 'ma_below':
                    ma_period = params.get('ma_period', 20)
                    self.df['MA'] = self.calculate_ma(ma_period)
                    sig = (self.df['收盤價'] < self.df['MA']).fillna(False).tolist()
                    indicator_signals.append(sig)
                
                elif ind_type == 'ma_slope_up':
                    window = params.get('window', 20)
                    threshold = params.get('threshold', 0.02)
                    self.df['MA'] = self.calculate_ma(window)
                    self.df['MA_slope_pct'] = (self.df['MA'].diff() / self.df['MA'].shift(1)) * 100
                    sig = [(self.df.iloc[i]['MA_slope_pct'] > threshold if not pd.isna(self.df.iloc[i]['MA_slope_pct']) else False) for i in range(len(self.df))]
                    indicator_signals.append(sig)
                
                elif ind_type == 'ma_slope_down':
                    window = params.get('window', 20)
                    threshold = params.get('threshold', -0.05)
                    self.df['MA'] = self.calculate_ma(window)
                    self.df['MA_slope_pct'] = (self.df['MA'].diff() / self.df['MA'].shift(1)) * 100
                    sig = [(self.df.iloc[i]['MA_slope_pct'] < threshold if not pd.isna(self.df.iloc[i]['MA_slope_pct']) else False) for i in range(len(self.df))]
                    indicator_signals.append(sig)
                
                elif ind_type == 'foreign_consecutive_buy':
                    days = params.get('days', 3)
                    count = [0] * len(self.df)
                    for i in range(1, len(self.df)):
                        val = self.df.iloc[i].get('外資買賣超', 0)
                        if val and val > 0:
                            count[i] = count[i-1] + 1
                        else:
                            count[i] = 0
                    sig = [count[i] >= days for i in range(len(self.df))]
                    indicator_signals.append(sig)
                
                elif ind_type == 'trust_consecutive_buy':
                    days = params.get('days', 3)
                    count = [0] * len(self.df)
                    for i in range(1, len(self.df)):
                        val = self.df.iloc[i].get('投信買賣超', 0)
                        if val and val > 0:
                            count[i] = count[i-1] + 1
                        else:
                            count[i] = 0
                    sig = [count[i] >= days for i in range(len(self.df))]
                    indicator_signals.append(sig)
                
                elif ind_type == 'dealer_consecutive_buy':
                    days = params.get('days', 3)
                    count = [0] * len(self.df)
                    for i in range(1, len(self.df)):
                        val = self.df.iloc[i].get('自營商買賣超', 0)
                        if val and val > 0:
                            count[i] = count[i-1] + 1
                        else:
                            count[i] = 0
                    sig = [count[i] >= days for i in range(len(self.df))]
                    indicator_signals.append(sig)
                
                elif ind_type == 'foreign_holding_high':
                    threshold = params.get('threshold', 30)
                    sig = [(self.df.iloc[i].get('外資持股比', 0) or 0) >= threshold for i in range(len(self.df))]
                    indicator_signals.append(sig)
                
                elif ind_type == 'foreign_holding_low':
                    threshold = params.get('threshold', 10)
                    sig = [(self.df.iloc[i].get('外資持股比', 0) or 0) <= threshold for i in range(len(self.df))]
                    indicator_signals.append(sig)
                
                elif ind_type == 'trust_volume_ratio':
                    days = params.get('days', 5)
                    volume_ratio = params.get('volume_ratio', 10)
                    sig = []
                    for i in range(len(self.df)):
                        if i >= days - 1:
                            # 計算前N日投信買入總張數
                            trust_buy_sum = 0
                            volume_sum = 0
                            for j in range(i - days + 1, i + 1):
                                trust_val = self.df.iloc[j].get('投信買賣超', 0) or 0
                                if trust_val > 0:  # 只計算買入
                                    trust_buy_sum += trust_val
                                volume_sum += self.df.iloc[j].get('成交量', 0) or 0
                            
                            # 計算投信買入占交易量比例
                            if volume_sum > 0:
                                ratio = (trust_buy_sum / volume_sum) * 100
                                sig.append(ratio >= volume_ratio)
                            else:
                                sig.append(False)
                        else:
                            sig.append(False)
                    indicator_signals.append(sig)
                
                elif ind_type == 'w_bottom':
                    lookback = params.get('lookback', 40)
                    bottom_diff = params.get('bottom_diff', 0.07)
                    w_height = params.get('w_height', 0.10)
                    breakout_pct = params.get('breakout_pct', 0.01)
                    sig = []
                    for i in range(len(self.df)):
                        if i < lookback:
                            sig.append(False)
                            continue
                        
                        window_data = self.df.iloc[i-lookback:i+1]
                        lows = window_data['最低價'].values
                        highs = window_data['最高價'].values
                        closes = window_data['收盤價'].values
                        
                        # 找局部低點
                        min_idx = []
                        for j in range(2, len(lows)-2):
                            if (lows[j] <= lows[j-1] and lows[j] <= lows[j-2] and 
                                lows[j] <= lows[j+1] and lows[j] <= lows[j+2]):
                                min_idx.append(j)
                        
                        # 找局部高點
                        max_idx = []
                        for j in range(2, len(highs)-2):
                            if (highs[j] >= highs[j-1] and highs[j] >= highs[j-2] and 
                                highs[j] >= highs[j+1] and highs[j] >= highs[j+2]):
                                max_idx.append(j)
                        
                        # 需要至少兩個低點和兩個高點
                        if len(min_idx) >= 2 and len(max_idx) >= 2:
                            # 找最後兩個間隔足夠的低點
                            valid_pair = None
                            for k in range(len(min_idx)-1, 0, -1):
                                if min_idx[k] - min_idx[k-1] >= 5:
                                    valid_pair = (min_idx[k-1], min_idx[k])
                                    break
                            
                            if valid_pair:
                                left_idx, right_idx = valid_pair
                                left_low = lows[left_idx]
                                right_low = lows[right_idx]
                                
                                # 檢查兩個低點是否接近
                                if abs(left_low - right_low) / left_low <= bottom_diff:
                                    # 找左底之後、右底之前的高點（第一次反彈）
                                    peak1_candidates = [idx for idx in max_idx if left_idx < idx < right_idx]
                                    # 找右底之後的高點（第二次反彈）
                                    peak2_candidates = [idx for idx in max_idx if idx > right_idx]
                                    
                                    if peak1_candidates and peak2_candidates:
                                        peak1_idx = peak1_candidates[0]  # 第一個反彈高點
                                        peak2_idx = peak2_candidates[0]  # 第二個反彈高點
                                        peak1_high = highs[peak1_idx]
                                        peak2_high = highs[peak2_idx]
                                        
                                        # 頸線 = 兩個反彈高點的平均
                                        neckline = (peak1_high + peak2_high) / 2
                                        
                                        # 檢查當前位置是否在第二次反彈之後（W底形成後才能突破）
                                        current_idx_in_window = len(window_data) - 1
                                        if current_idx_in_window > peak2_idx:
                                            # 檢查左底之前是否有從頸線之上下跌（使用left_idx作為回溯範圍）
                                            lookback_window = min(left_idx, lookback // 2)  # 使用lookback的一半或左底位置，取較小者
                                            if lookback_window >= 3:
                                                before_left = highs[max(0, left_idx-lookback_window):left_idx]
                                                if len(before_left) > 0 and max(before_left) > neckline:
                                                    # 頸線必須明顯高於兩個低點（使用w_height參數）
                                                    if neckline > max(left_low, right_low) * (1 + w_height):
                                                        # 當前價格突破頸線（使用breakout_pct參數）
                                                        if closes[-1] > neckline * (1 + breakout_pct):
                                                            # print(f"[W_BOTTOM] {self.df.iloc[i]['日期']} 觸發 (收盤={closes[-1]:.2f}, 頸線={neckline:.2f})")
                                                            sig.append(True)
                                                        else:
                                                            sig.append(False)
                                                    else:
                                                        sig.append(False)
                                                else:
                                                    sig.append(False)
                                            else:
                                                sig.append(False)
                                        else:
                                            sig.append(False)
                                    else:
                                        sig.append(False)
                                else:
                                    sig.append(False)
                            else:
                                sig.append(False)
                        else:
                            sig.append(False)
                    indicator_signals.append(sig)
                

                elif ind_type == 'volume_ratio':
                    days = params.get('days', 5)
                    threshold = params.get('threshold', 1.5)
                    sig = []
                    for i in range(len(self.df)):
                        if i < days:
                            sig.append(False)
                            continue
                        
                        current_vol = self.df.iloc[i]['成交量']
                        prev_vol = self.df.iloc[i-days]['成交量']
                        
                        if prev_vol > 0:
                            ratio = current_vol / prev_vol
                            sig.append(ratio >= threshold)
                        else:
                            sig.append(False)
                    indicator_signals.append(sig)
                
                elif ind_type == 'below_institutional_cost':
                    days = params.get('days', 20)
                    threshold_pct = params.get('threshold_pct', 5)
                    sig = []
                    for i in range(len(self.df)):
                        if i < days:
                            sig.append(False)
                            continue
                        
                        # 計算N日法人平均成本（買入扣除賣出）
                        total_cost = 0
                        total_shares = 0
                        for j in range(i - days + 1, i + 1):
                            # 法人 = 外資 + 投信 + 自營商
                            foreign = self.df.iloc[j].get('外資買賣超', 0) or 0
                            trust = self.df.iloc[j].get('投信買賣超', 0) or 0
                            dealer = self.df.iloc[j].get('自營商買賣超', 0) or 0
                            institutional_shares = foreign + trust + dealer
                            
                            # 買賣超正數=買入，負數=賣出
                            price = self.df.iloc[j]['收盤價']
                            total_cost += institutional_shares * price
                            total_shares += institutional_shares
                        
                        if total_shares > 0:
                            avg_cost = total_cost / total_shares
                            current_price = self.df.iloc[i]['收盤價']
                            # 檢查當前價格是否低於平均成本的X%
                            threshold_price = avg_cost * (1 - threshold_pct / 100)
                            is_below = current_price < threshold_price
                            
                            # 印出調試資訊
                            if i % 20 == 0 or is_below:  # 每20筆或觸發時印出
                                print(f"[{self.df.iloc[i]['日期']}] 法人成本={avg_cost:.2f}, 當前價={current_price:.2f}, 門檻={threshold_price:.2f}, 觸發={'YES' if is_below else 'NO'}")
                            
                            sig.append(is_below)
                        else:
                            sig.append(False)
                    indicator_signals.append(sig)
                
                elif ind_type == 'price_rise':
                    days = params.get('days', 1)
                    threshold_pct = params.get('threshold_pct', 5)
                    sig = []
                    for i in range(len(self.df)):
                        if i - days < 0:
                            sig.append(False)
                            continue
                        
                        prev_price = self.df.iloc[i-days]['收盤價']
                        current_price = self.df.iloc[i]['收盤價']
                        if prev_price > 0:
                            change_pct = ((current_price - prev_price) / prev_price) * 100
                            sig.append(change_pct >= threshold_pct)
                        else:
                            sig.append(False)
                    indicator_signals.append(sig)
                
                elif ind_type == 'long_lower_shadow':
                    threshold = params.get('threshold', 0.03)
                    sig = []
                    for i in range(len(self.df)):
                        open_price = self.df.iloc[i]['開盤價']
                        close_price = self.df.iloc[i]['收盤價']
                        low_price = self.df.iloc[i]['最低價']
                        if open_price > 0:
                            if open_price > close_price:
                                shadow = (close_price - low_price) / open_price
                            else:
                                shadow = (open_price - low_price) / open_price
                            sig.append(shadow > threshold)
                        else:
                            sig.append(False)
                    indicator_signals.append(sig)
                
                elif ind_type == 'long_upper_shadow':
                    threshold = params.get('threshold', 0.03)
                    sig = []
                    for i in range(len(self.df)):
                        open_price = self.df.iloc[i]['開盤價']
                        close_price = self.df.iloc[i]['收盤價']
                        high_price = self.df.iloc[i]['最高價']
                        if open_price > 0:
                            if open_price > close_price:
                                shadow = (high_price - open_price) / open_price
                            else:
                                shadow = (high_price - close_price) / open_price
                            sig.append(shadow > threshold)
                        else:
                            sig.append(False)
                    indicator_signals.append(sig)
                
                elif ind_type == 'ma_support':
                    ma_period = params.get('ma_period', 20)
                    ma_col = f'MA_{ma_period}'
                    if ma_col not in self.df.columns:
                        self.df[ma_col] = self.calculate_ma(ma_period)
                    sig = []
                    for i in range(len(self.df)):
                        if i < 3:
                            sig.append(False)
                            continue
                        ma_i = self.df.iloc[i][ma_col]
                        ma_i1 = self.df.iloc[i-1][ma_col]
                        ma_i2 = self.df.iloc[i-2][ma_col]
                        if pd.isna(ma_i) or pd.isna(ma_i1) or pd.isna(ma_i2):
                            sig.append(False)
                            continue
                        cond1 = ma_i2 < self.df.iloc[i-2]['收盤價']
                        cond2 = ma_i1 < self.df.iloc[i-1]['收盤價']
                        cond3 = self.df.iloc[i]['最低價'] < ma_i < self.df.iloc[i]['收盤價']
                        sig.append(cond1 and cond2 and cond3)
                    indicator_signals.append(sig)
                
                elif ind_type == 'ma_golden_cross':
                    short_window = params.get('short_window', 5)
                    long_window = params.get('long_window', 20)
                    days = params.get('days', 4)
                    short_col = f'MA_{short_window}'
                    long_col = f'MA_{long_window}'
                    if short_col not in self.df.columns:
                        self.df[short_col] = self.calculate_ma(short_window)
                    if long_col not in self.df.columns:
                        self.df[long_col] = self.calculate_ma(long_window)
                    sig = []
                    for i in range(len(self.df)):
                        if i < days + 1:
                            sig.append(False)
                            continue
                        gap_narrowing = True
                        for j in range(days):
                            idx_curr = i - j
                            idx_prev = i - j - 1
                            if pd.isna(self.df.iloc[idx_curr][short_col]) or pd.isna(self.df.iloc[idx_curr][long_col]) or \
                               pd.isna(self.df.iloc[idx_prev][short_col]) or pd.isna(self.df.iloc[idx_prev][long_col]):
                                gap_narrowing = False
                                break
                            gap_current = self.df.iloc[idx_curr][long_col] - self.df.iloc[idx_curr][short_col]
                            gap_prev = self.df.iloc[idx_prev][long_col] - self.df.iloc[idx_prev][short_col]
                            if gap_current >= gap_prev:
                                gap_narrowing = False
                                break
                        if gap_narrowing:
                            gap_prev = self.df.iloc[i-1][long_col] - self.df.iloc[i-1][short_col]
                            gap_current = self.df.iloc[i][long_col] - self.df.iloc[i][short_col]
                            if gap_prev > 0 and gap_current < 0:
                                sig.append(True)
                            else:
                                sig.append(False)
                        else:
                            sig.append(False)
                    indicator_signals.append(sig)
                
                elif ind_type == 'price_drop':
                    days = params.get('days', 1)
                    threshold_pct = params.get('threshold_pct', -5)
                    sig = []
                    for i in range(len(self.df)):
                        if i - days < 0:
                            sig.append(False)
                            continue
                        
                        prev_price = self.df.iloc[i-days]['收盤價']
                        current_price = self.df.iloc[i]['收盤價']
                        if prev_price > 0:
                            change_pct = ((current_price - prev_price) / prev_price) * 100
                            sig.append(change_pct <= threshold_pct)
                        else:
                            sig.append(False)
                    indicator_signals.append(sig)
            
            # 策略內所有指標都要達標（AND）
            if indicator_signals:
                strategy_signal = [all(signals[i] for signals in indicator_signals) for i in range(len(self.df))]
                buy_strategy_signals.append(strategy_signal)
        
        # 處理賣出策略（每個策略內的指標用AND）
        for strategy in sell_strategies:
            indicator_signals = []
            for indicator in strategy['indicators']:
                ind_type = indicator['type']
                params = indicator['params']
                
                if ind_type == 'ma_crossover':
                    short_window = params.get('short_window', 5)
                    long_window = params.get('long_window', 20)
                    self.df['MA_short'] = self.calculate_ma(short_window)
                    self.df['MA_long'] = self.calculate_ma(long_window)
                    # 死亡交叉：前一日短MA >= 長MA，當日短MA < 長MA
                    sig = []
                    for i in range(len(self.df)):
                        if i == 0:
                            sig.append(False)
                        else:
                            prev_short = self.df.iloc[i-1]['MA_short']
                            prev_long = self.df.iloc[i-1]['MA_long']
                            curr_short = self.df.iloc[i]['MA_short']
                            curr_long = self.df.iloc[i]['MA_long']
                            if pd.isna(prev_short) or pd.isna(prev_long) or pd.isna(curr_short) or pd.isna(curr_long):
                                sig.append(False)
                            else:
                                # 死亡交叉：前一日短MA在上方，當日短MA在下方
                                sig.append(prev_short >= prev_long and curr_short < curr_long)
                    indicator_signals.append(sig)
                
                elif ind_type == 'rsi':
                    period = params.get('period', 14)
                    sell_threshold = params.get('sell_threshold', 70)
                    delta = self.df['收盤價'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                    rs = gain / loss
                    self.df['RSI'] = 100 - (100 / (1 + rs))
                    sig = (self.df['RSI'] > sell_threshold).fillna(False).tolist()
                    indicator_signals.append(sig)
                
                elif ind_type == 'ma_slope_down':
                    window = params.get('window', 20)
                    threshold = params.get('threshold', -0.05)
                    self.df['MA'] = self.calculate_ma(window)
                    self.df['MA_slope_pct'] = (self.df['MA'].diff() / self.df['MA'].shift(1)) * 100
                    sig = [(self.df.iloc[i]['MA_slope_pct'] < threshold if not pd.isna(self.df.iloc[i]['MA_slope_pct']) else False) for i in range(len(self.df))]
                    indicator_signals.append(sig)
                
                elif ind_type == 'take_profit':
                    # 停利在執行時檢查
                    indicator_signals.append([False] * len(self.df))
                
                elif ind_type == 'stop_loss':
                    # 停損在執行時檢查
                    indicator_signals.append([False] * len(self.df))
                
                elif ind_type == 'foreign_consecutive_sell':
                    days = params.get('days', 3)
                    count = [0] * len(self.df)
                    for i in range(1, len(self.df)):
                        val = self.df.iloc[i].get('外資買賣超', 0)
                        if val and val < 0:
                            count[i] = count[i-1] + 1
                        else:
                            count[i] = 0
                    sig = [count[i] >= days for i in range(len(self.df))]
                    indicator_signals.append(sig)
                
                elif ind_type == 'trust_consecutive_sell':
                    days = params.get('days', 3)
                    count = [0] * len(self.df)
                    for i in range(1, len(self.df)):
                        val = self.df.iloc[i].get('投信買賣超', 0)
                        if val and val < 0:
                            count[i] = count[i-1] + 1
                        else:
                            count[i] = 0
                    sig = [count[i] >= days for i in range(len(self.df))]
                    indicator_signals.append(sig)
                
                elif ind_type == 'price_drop':
                    days = params.get('days', 1)
                    threshold_pct = params.get('threshold_pct', -5)
                    sig = []
                    for i in range(len(self.df)):
                        if i - days < 0:
                            sig.append(False)
                            continue
                        
                        prev_price = self.df.iloc[i-days]['收盤價']
                        current_price = self.df.iloc[i]['收盤價']
                        if prev_price > 0:
                            change_pct = ((current_price - prev_price) / prev_price) * 100
                            sig.append(change_pct <= threshold_pct)
                        else:
                            sig.append(False)
                    indicator_signals.append(sig)
                
                elif ind_type == 'price_rise':
                    days = params.get('days', 1)
                    threshold_pct = params.get('threshold_pct', 5)
                    sig = []
                    for i in range(len(self.df)):
                        if i - days < 0:
                            sig.append(False)
                            continue
                        
                        prev_price = self.df.iloc[i-days]['收盤價']
                        current_price = self.df.iloc[i]['收盤價']
                        if prev_price > 0:
                            change_pct = ((current_price - prev_price) / prev_price) * 100
                            sig.append(change_pct >= threshold_pct)
                        else:
                            sig.append(False)
                    indicator_signals.append(sig)
                
                elif ind_type == 'high_volume':
                    volume_period = params.get('volume_period', 20)
                    volume_multiplier = params.get('volume_multiplier', 2.0)
                    consecutive_days = params.get('consecutive_days', 1)
                    self.df['Volume_MA'] = self.df['成交量'].rolling(window=volume_period).mean()
                    count = [0] * len(self.df)
                    for i in range(1, len(self.df)):
                        vol_ma = self.df.iloc[i]['Volume_MA']
                        vol = self.df.iloc[i]['成交量']
                        if not pd.isna(vol_ma) and vol_ma > 0 and vol > vol_ma * volume_multiplier:
                            count[i] = count[i-1] + 1
                        else:
                            count[i] = 0
                    sig = [count[i] >= consecutive_days for i in range(len(self.df))]
                    indicator_signals.append(sig)
                
                elif ind_type == 'low_volume':
                    volume_period = params.get('volume_period', 20)
                    volume_multiplier = params.get('volume_multiplier', 0.5)
                    consecutive_days = params.get('consecutive_days', 1)
                    self.df['Volume_MA'] = self.df['成交量'].rolling(window=volume_period).mean()
                    count = [0] * len(self.df)
                    for i in range(1, len(self.df)):
                        vol_ma = self.df.iloc[i]['Volume_MA']
                        vol = self.df.iloc[i]['成交量']
                        if not pd.isna(vol_ma) and vol_ma > 0 and vol < vol_ma * volume_multiplier:
                            count[i] = count[i-1] + 1
                        else:
                            count[i] = 0
                    sig = [count[i] >= consecutive_days for i in range(len(self.df))]
                    indicator_signals.append(sig)
                
                elif ind_type == 'long_upper_shadow':
                    threshold = params.get('threshold', 0.03)
                    sig = []
                    for i in range(len(self.df)):
                        open_price = self.df.iloc[i]['開盤價']
                        close_price = self.df.iloc[i]['收盤價']
                        high_price = self.df.iloc[i]['最高價']
                        if open_price > 0:
                            if open_price > close_price:
                                shadow = (high_price - open_price) / open_price
                            else:
                                shadow = (high_price - close_price) / open_price
                            sig.append(shadow > threshold)
                        else:
                            sig.append(False)
                    indicator_signals.append(sig)
            
            # 策略內所有指標都要達標（AND）
            if indicator_signals:
                strategy_signal = [all(signals[i] for signals in indicator_signals) for i in range(len(self.df))]
                sell_strategy_signals.append(strategy_signal)
        
        # 執行回測
        equity_curve = []
        realized_profit = 0
        trade_counter = 0
        
        for i in range(len(self.df)):
            price = self.df.iloc[i]['收盤價']
            date = self.df.iloc[i]['日期']
            equity_curve.append({'日期': date, '已實現損益': realized_profit})
            
            # 任一買進策略達標就買進（OR）
            should_buy = any(signals[i] for signals in buy_strategy_signals) if buy_strategy_signals else False
            
            # 任一賣出策略達標就賣出（OR）
            should_sell = any(signals[i] for signals in sell_strategy_signals) if sell_strategy_signals else False
            
            # 檢查停利停損
            profit_target_sell = False
            sell_reason = '策略信號'
            if self.position > 0:
                for strategy in sell_strategies:
                    for indicator in strategy['indicators']:
                        if indicator['type'] in ['take_profit', 'stop_loss']:
                            target_pct = indicator['params'].get('profit_pct' if indicator['type'] == 'take_profit' else 'loss_pct', 0)
                            total_cost = sum(r['金額'] for r in self.buy_records)
                            current_value = self.position * price
                            current_return = ((current_value - total_cost) / total_cost * 100) if total_cost > 0 else 0
                            if indicator['type'] == 'take_profit' and current_return >= target_pct:
                                profit_target_sell = True
                                sell_reason = f"停利{target_pct}%"
                                break
                            elif indicator['type'] == 'stop_loss' and current_return <= target_pct:
                                profit_target_sell = True
                                sell_reason = f"停損{target_pct}%"
                                break
                    if profit_target_sell:
                        break
            
            if should_buy and self.position == 0 and i < len(self.df) - 1:
                # 隔天開盤價買入，不受資金限制
                next_price = self.df.iloc[i+1]['開盤價']
                next_date = self.df.iloc[i+1]['日期']
                # 固定買入1000股，不考慮資金限制
                shares = 1000
                trade_counter += 1
                cost = shares * next_price
                self.capital -= cost  # 允許資金變負數
                self.position += shares
                triggered_strategies = [idx+1 for idx, signals in enumerate(buy_strategy_signals) if signals[i]]
                self.buy_records.append({'日期': next_date, '價格': next_price, '數量': shares, '金額': cost})
                self.trades.append({'日期': next_date, '類型': '買入', '價格': next_price, '數量': shares, '金額': cost, '餘額': self.capital, '策略編號': triggered_strategies, '交易編號': trade_counter})
            
            elif (should_sell or profit_target_sell) and self.position > 0 and i < len(self.df) - 1:
                # 隔天開盤價賣出
                next_price = self.df.iloc[i+1]['開盤價']
                next_date = self.df.iloc[i+1]['日期']
                revenue = self.position * next_price
                total_cost = sum(r['金額'] for r in self.buy_records)
                profit = revenue - total_cost
                return_rate = (profit / total_cost * 100) if total_cost > 0 else 0
                realized_profit += profit
                self.capital += revenue
                if profit_target_sell:
                    triggered_strategies = []
                    for idx, strategy in enumerate(sell_strategies):
                        for indicator in strategy['indicators']:
                            if indicator['type'] in ['take_profit', 'stop_loss']:
                                triggered_strategies.append(idx+1)
                                break
                else:
                    triggered_strategies = [idx+1 for idx, signals in enumerate(sell_strategy_signals) if signals[i]]
                self.trades.append({'日期': next_date, '類型': '賣出', '價格': next_price, '數量': self.position, '金額': revenue, '餘額': self.capital, '獲利': profit, '報酬率': return_rate, '買入記錄': self.buy_records.copy(), '賣出原因': sell_reason, '策略編號': triggered_strategies})
                self.position = 0
                self.buy_records = []
        
        # 最後沒賣出就不算數，直接還回資金
        if self.position > 0:
            self.capital += sum(r['金額'] for r in self.buy_records)
            self.position = 0
            self.buy_records = []
        
        final_value = self.capital
        sell_trades = [t for t in self.trades if t['類型'] == '賣出']
        win_trades = [t for t in sell_trades if t['獲利'] > 0]
        win_rate = len(win_trades) / len(sell_trades) * 100 if len(sell_trades) > 0 else 0
        
        return {
            'trades': self.trades,
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'profit': final_value - self.initial_capital,
            'return_rate': (final_value - self.initial_capital) / self.initial_capital * 100,
            'equity_curve': equity_curve,
            'win_rate': win_rate,
            'total_trades': len(sell_trades),
            'win_trades': len(win_trades)
        }

def run_backtest(stock_code, buy_strategies, sell_strategies, buy_logic='and', sell_logic='or', initial_capital=1000000):
    bt = BacktestStrategy(stock_code, initial_capital)
    bt.load_data()
    result = bt.combined_strategy(buy_strategies, sell_strategies, buy_logic, sell_logic)
    return result, bt.df

def run_backtest_v2(stock_code, buy_strategies, sell_strategies, initial_capital=1000000):
    bt = BacktestStrategy(stock_code, initial_capital)
    bt.load_data()
    result = bt.combined_strategy_v2(buy_strategies, sell_strategies)
    return result, bt.df
