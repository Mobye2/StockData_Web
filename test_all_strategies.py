import sys
sys.path.append('main_app')
from backtest import run_backtest_v2

strategies_to_test = [
    ('長下影線', [{'type': 'long_lower_shadow', 'params': {'threshold': 0.03}}]),
    ('長上影線', [{'type': 'long_upper_shadow', 'params': {'threshold': 0.03}}]),
    ('均線支撐', [{'type': 'ma_support', 'params': {'ma_period': 20}}]),
    ('均線黃金交叉', [{'type': 'ma_golden_cross', 'params': {'short_window': 5, 'long_window': 20, 'days': 4}}]),
    ('回檔打底', [{'type': 'pullback_correction', 'params': {'slope_40_threshold': 0.15, 'slope_5_range': 0.2}}]),
]

sell_strategies = [
    {
        'indicators': [
            {'type': 'take_profit', 'params': {'profit_pct': 5}}
        ]
    }
]

for name, indicators in strategies_to_test:
    print(f"\n{'='*50}")
    print(f"測試策略: {name}")
    print('='*50)
    
    buy_strategies = [{'indicators': [indicators[0]]}]
    
    try:
        result, df = run_backtest_v2('2330', buy_strategies, sell_strategies)
        
        print(f"報酬率: {result['return_rate']:.2f}%")
        print(f"總交易: {result['total_trades']} 次")
        print(f"勝率: {result['win_rate']:.2f}%")
        
        if result['trades']:
            buy_trades = [t for t in result['trades'] if t['類型'] == '買入']
            if buy_trades:
                print(f"首次買入: {buy_trades[0]['日期']} @ {buy_trades[0]['價格']:.2f}")
    except Exception as e:
        print(f"錯誤: {str(e)}")
