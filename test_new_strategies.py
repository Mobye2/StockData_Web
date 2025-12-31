import sys
sys.path.append('main_app')
from backtest import run_backtest_v2

# 測試長下影線策略
buy_strategies = [
    {
        'indicators': [
            {'type': 'long_lower_shadow', 'params': {'threshold': 0.03}}
        ]
    }
]

sell_strategies = [
    {
        'indicators': [
            {'type': 'take_profit', 'params': {'profit_pct': 5}}
        ]
    }
]

print("測試長下影線策略...")
result, df = run_backtest_v2('2330', buy_strategies, sell_strategies)

print(f"\n初始資金: {result['initial_capital']:,.0f}")
print(f"最終資金: {result['final_value']:,.0f}")
print(f"獲利: {result['profit']:,.0f}")
print(f"報酬率: {result['return_rate']:.2f}%")
print(f"總交易次數: {result['total_trades']}")
print(f"獲利次數: {result['win_trades']}")
print(f"勝率: {result['win_rate']:.2f}%")

if result['trades']:
    print(f"\n前3筆交易:")
    for trade in result['trades'][:3]:
        print(f"  {trade['日期']} {trade['類型']} {trade['價格']:.2f} x {trade['數量']}")
