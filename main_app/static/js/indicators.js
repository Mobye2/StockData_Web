// 共用指標配置
const indicatorConfigs = {
    ma_crossover: { name: 'MA均線交叉', category: '技術類', params: { short_window: 5, long_window: 20 }, units: { short_window: '日', long_window: '日' } },
    ma_above: { name: '超過均線', category: '技術類', params: { ma_period: 20 }, units: { ma_period: '日' } },
    ma_below: { name: '跌破均線', category: '技術類', params: { ma_period: 20 }, units: { ma_period: '日' } },
    rsi: { name: 'RSI指標', category: '技術類', params: { period: 14, buy_threshold: 30, sell_threshold: 70 }, units: { period: '日', buy_threshold: '', sell_threshold: '' } },
    high_volume: { name: '爆量', category: '技術類', params: { volume_multiplier: 2.0 }, units: { volume_multiplier: '倍' } },
    ma_slope_up: { name: 'MA向上', category: '技術類', params: { window: 20, threshold: 10, hold_days: 3 }, units: { window: '日', threshold: '%', hold_days: '日' } },
    ma_slope_down: { name: 'MA向下', category: '技術類', params: { window: 20, threshold: -10, hold_days: 3 }, units: { window: '日', threshold: '%', hold_days: '日' } },
    w_bottom: { name: 'W底型態', category: '型態類', params: { lookback: 60, bottom_diff: 0.07, w_height: 0.10, breakout_pct: 0.01 }, units: { lookback: '日', bottom_diff: '', w_height: '', breakout_pct: '' } },
    take_profit: { name: '停利', category: '風控類', params: { profit_pct: 10 }, units: { profit_pct: '%' } },
    stop_loss: { name: '停損', category: '風控類', params: { loss_pct: -5 }, units: { loss_pct: '%' } },
    foreign_consecutive_buy: { name: '外資連續買超', category: '籌碼類', params: { days: 3 }, units: { days: '日' } },
    trust_consecutive_buy: { name: '投信連續買超', category: '籌碼類', params: { days: 3 }, units: { days: '日' } },
    dealer_consecutive_buy: { name: '自營商連續買超', category: '籌碼類', params: { days: 3 }, units: { days: '日' } },
    foreign_consecutive_sell: { name: '外資連續賣超', category: '籌碼類', params: { days: 3 }, units: { days: '日' } },
    trust_consecutive_sell: { name: '投信連續賣超', category: '籌碼類', params: { days: 3 }, units: { days: '日' } },
    foreign_holding_high: { name: '外資持股比高', category: '籌碼類', params: { threshold: 30 }, units: { threshold: '%' } },
    foreign_holding_low: { name: '外資持股比低', category: '籌碼類', params: { threshold: 10 }, units: { threshold: '%' } },
    trust_volume_ratio: { name: '投信買入占交易量比', category: '籌碼類', params: { days: 5, volume_ratio: 10 }, units: { days: '日', volume_ratio: '%' } }
};