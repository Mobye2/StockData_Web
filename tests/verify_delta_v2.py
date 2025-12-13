import sqlite3
import pandas as pd
import sys
sys.path.append('..')
from backtest import BacktestStrategy

def verify_delta_v2():
    """驗證台達電回測結果 - 使用相對斜率"""
    
    print("=" * 80)
    print("台達電 (2308) 回測驗證 - 相對斜率版本")
    print("=" * 80)
    
    # 設定策略
    buy_strategies = [{
        'indicators': [{
            'type': 'ma_slope_up',
            'params': {'window': 20, 'threshold': 30, 'hold_days': 1}
        }]
    }]
    
    sell_strategies = [
        {
            'indicators': [{
                'type': 'ma_slope_down',
                'params': {'window': 20, 'threshold': -15, 'hold_days': 5}
            }]
        },
        {
            'indicators': [{
                'type': 'stop_loss',
                'params': {'loss_pct': -8}
            }]
        },
        {
            'indicators': [{
                'type': 'ma_slope_down',
                'params': {'window': 10, 'threshold': -40, 'hold_days': 2}
            }]
        }
    ]
    
    # 執行回測
    import os
    os.chdir('..')
    bt = BacktestStrategy('2308', 1000000)
    bt.load_data()
    result = bt.combined_strategy_v2(buy_strategies, sell_strategies)
    
    # 計算指標
    bt.df['MA20'] = bt.df['收盤價'].rolling(window=20).mean()
    bt.df['MA20_slope_pct'] = (bt.df['MA20'].diff() / bt.df['MA20'].shift(1)) * 100
    bt.df['MA10'] = bt.df['收盤價'].rolling(window=10).mean()
    bt.df['MA10_slope_pct'] = (bt.df['MA10'].diff() / bt.df['MA10'].shift(1)) * 100
    
    print(f"\n回測結果摘要:")
    print(f"初始資金: {result['initial_capital']:,}")
    print(f"最終價值: {result['final_value']:,}")
    print(f"獲利: {result['profit']:,}")
    print(f"報酬率: {result['return_rate']:.2f}%")
    print(f"交易次數: {result['total_trades']}")
    print(f"勝率: {result['win_rate']:.2f}%")
    
    # 分析買入交易
    buy_trades = [t for t in result['trades'] if t['類型'] == '買入']
    print(f"\n\n{'=' * 80}")
    print(f"買入交易驗證 (共 {len(buy_trades)} 筆)")
    print(f"{'=' * 80}\n")
    
    for idx, trade in enumerate(buy_trades[:5], 1):
        date = trade['日期']
        price = trade['價格']
        trade_num = trade.get('交易編號', idx)
        
        date_idx = bt.df[bt.df['日期'] == date].index[0]
        
        print(f"交易 #{trade_num} | 日期: {date} | 買入價: {price:.2f}")
        print(f"  策略編號: {trade.get('策略編號', [])}")
        
        # 檢查買入條件：MA20向上 (threshold=30%, hold_days=1)
        threshold = 30 / 100  # 0.3%
        slope_pct = bt.df.iloc[date_idx]['MA20_slope_pct']
        ma20 = bt.df.iloc[date_idx]['MA20']
        ma20_prev = bt.df.iloc[date_idx-1]['MA20'] if date_idx > 0 else 0
        
        print(f"  買入條件檢查:")
        print(f"    MA20今天 = {ma20:.2f}")
        print(f"    MA20昨天 = {ma20_prev:.2f}")
        print(f"    MA20斜率% = {slope_pct:.4f}% (閾值 = {threshold:.4f}%)")
        
        # 檢查連續天數
        above_count = 0
        for j in range(date_idx, max(-1, date_idx-5), -1):
            s = bt.df.iloc[j]['MA20_slope_pct']
            if not pd.isna(s) and s > threshold:
                above_count += 1
            else:
                break
        
        print(f"    連續達標天數 = {above_count} (需要 >= 1)")
        print(f"    [{'OK' if above_count >= 1 else 'NG'}] 買入條件")
        print()
    
    # 分析賣出交易
    sell_trades = [t for t in result['trades'] if t['類型'] == '賣出']
    print(f"\n{'=' * 80}")
    print(f"賣出交易驗證 (共 {len(sell_trades)} 筆)")
    print(f"{'=' * 80}\n")
    
    for idx, trade in enumerate(sell_trades[:5], 1):
        date = trade['日期']
        price = trade['價格']
        sell_reason = trade.get('賣出原因', '-')
        strategy_nums = trade.get('策略編號', [])
        
        date_idx = bt.df[bt.df['日期'] == date].index[0]
        
        buy_records = trade.get('買入記錄', [])
        if buy_records:
            buy_date = buy_records[0]['日期']
            buy_price = buy_records[0]['價格']
            buy_trade = next((t for t in buy_trades if t['日期'] == buy_date), None)
            trade_num = buy_trade.get('交易編號', idx) if buy_trade else idx
        else:
            trade_num = idx
        
        print(f"交易 #{trade_num} | 賣出日期: {date} | 賣出價: {price:.2f}")
        print(f"  賣出原因: {sell_reason}")
        print(f"  觸發策略: {strategy_nums}")
        print(f"  獲利: {trade['獲利']:,} | 報酬率: {trade['報酬率']:.2f}%")
        
        # 驗證賣出條件
        if '停損' in sell_reason:
            total_cost = sum(r['金額'] for r in buy_records)
            current_value = trade['數量'] * price
            return_rate = ((current_value - total_cost) / total_cost * 100) if total_cost > 0 else 0
            print(f"  停損驗證: 報酬率 {return_rate:.2f}% <= -8% ? {return_rate <= -8}")
        
        elif '策略' in sell_reason or strategy_nums:
            print(f"  賣出條件檢查:")
            
            # 策略1: MA20向下 (threshold=-15%, hold_days=5)
            if 1 in strategy_nums:
                threshold1 = -15 / 100
                below_count1 = 0
                for j in range(date_idx, max(-1, date_idx-10), -1):
                    s = bt.df.iloc[j]['MA20_slope_pct']
                    if not pd.isna(s) and s < threshold1:
                        below_count1 += 1
                    else:
                        break
                print(f"    策略1 (MA20向下): 連續{below_count1}天 < {threshold1:.4f}% (需要>=5) [{'OK' if below_count1 >= 5 else 'NG'}]")
            
            # 策略3: MA10向下 (threshold=-40%, hold_days=2)
            if 3 in strategy_nums:
                threshold3 = -40 / 100
                below_count3 = 0
                for j in range(date_idx, max(-1, date_idx-5), -1):
                    s = bt.df.iloc[j]['MA10_slope_pct']
                    if not pd.isna(s) and s < threshold3:
                        below_count3 += 1
                    else:
                        break
                print(f"    策略3 (MA10向下): 連續{below_count3}天 < {threshold3:.4f}% (需要>=2) [{'OK' if below_count3 >= 2 else 'NG'}]")
        
        print()

if __name__ == '__main__':
    verify_delta_v2()
    print("\n驗證完成！")
