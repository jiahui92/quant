from studies.wave import find_wave, plot_wave
from studies.maBoll import maBollStart
from studies.dividend import dividendStart
from utils.index import getStockDataFrame
import utils.index as utils
import tushare as ts
from datetime import datetime


# for index, row in getStockDataFrame().iterrows():
#     plot_wave(row)
#

# 计算zixuan相关
# utils.calculate_function_runtime(maBollStart)

# 计算股息率相关
utils.calculate_function_runtime(dividendStart)

def test_all():
    pro = ts.pro_api()
    df = pro.trade_cal(exchange='SSE', start_date='20230101', end_date='20231231')

    for index, row in getStockDataFrame().iterrows():
        if row['is_open'] == 1:
            nowDate = datetime(row['cal_date'])
            df, isWave, withdrawal, withdrawaled, profit, dotArr = find_wave(row, nowDate, 60, 0)
            arr = []
            if isWave and -10 < withdrawal < 10 and withdrawaled > 40:
                arr.append({
                    'row': row,
                    'price': df.iloc[-1]['close_price'],
                    'withdrawaled': withdrawaled,
                })

            # 多组和策略

            # 优先级排序
            # 调仓计算
                # 顺便结算利润
