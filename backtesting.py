from datetime import datetime

from vnpy.trader.optimize import OptimizationSetting
from vnpy_ctastrategy.backtesting import BacktestingEngine
from vnpy_ctastrategy.strategies.atr_rsi_strategy import AtrRsiStrategy

import sys,os
sys.path.append(os.getcwd())
from strategies.template import JiahuiTestBoll

engine = BacktestingEngine()

engine.set_parameters(
    vt_symbol="300308.SZSE",
    interval="d",
    start=datetime(2022, 1, 1),
    end=datetime(2022, 12, 30),
    rate=1.5/10000, # 佣金
    slippage=0, # 滑点
    size= 100, # 合约乘数(买入卖出最小数量)
    pricetick=0.01, # 价格最小单位
    capital=1_000_000, # 回测资金
)
# 设置策略入参
engine.add_strategy(JiahuiTestBoll, {})
engine.load_data()
engine.run_backtesting()
df = engine.calculate_result()
engine.calculate_statistics()
engine.show_chart()
setting = OptimizationSetting()
setting.set_target("sharpe_ratio")
setting.add_parameter("atr_length", 25, 27, 1)
setting.add_parameter("atr_ma_length", 10, 30, 10)

# engine.run_ga_optimization(setting)
# engine.run_bf_optimization(setting)













# from datetime import datetime

# from vnpy.trader.optimize import OptimizationSetting
# from vnpy_ctastrategy.backtesting import BacktestingEngine
# from vnpy_ctastrategy.strategies.atr_rsi_strategy import AtrRsiStrategy

# from .strategies.template import AtrRsiStrategy
# engine = BacktestingEngine()

# engine.set_parameters(
#     vt_symbol="300308.SZSE",
#     interval="d",
#     start=datetime(2022, 1, 1),
#     end=datetime(2022, 12, 30),
#     rate=0.3/10000,
#     slippage=0.2,
#     size=300,
#     pricetick=0.2,
#     capital=1_000_000,
# )
# engine.add_strategy(AtrRsiStrategy, {})
# engine.load_data()
# engine.run_backtesting()
# df = engine.calculate_result()
# engine.calculate_statistics()
# engine.show_chart()
# setting = OptimizationSetting()
# setting.set_target("sharpe_ratio")
# setting.add_parameter("atr_length", 25, 27, 1)
# setting.add_parameter("atr_ma_length", 10, 30, 10)

# # engine.run_ga_optimization(setting)
# # engine.run_bf_optimization(setting)
