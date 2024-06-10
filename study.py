from studies.wave import find_wave, plot_wave
from studies.maBoll import zixuan_start
from studies.kdj_realtime import kdj_realtime_start
from studies.kdj_daily import kdj_daily_start
from studies.dividend import dividendStart
from utils.index import getStockDataFrame
from dataManager import update
import utils.index as utils
import tushare as ts
from datetime import datetime
import argparse


# for index, row in getStockDataFrame().iterrows():
#     plot_wave(row)
#

def main():
    parser = argparse.ArgumentParser(description="Choose which function to call.")
    # 添加一个命令行参数
    parser.add_argument(
        'function',
        choices=['zixuan_start', 'kdj_daily_start', 'kdj_realtime_start', 'dividendStart', 'daily_task'],
        help="Choose a function to execute"
    )
    args = parser.parse_args()

    if args.function == 'zixuan_start':
        utils.calculate_function_runtime(zixuan_start)
    elif args.function == 'kdj_daily_start':
        utils.calculate_function_runtime(kdj_daily_start)
    elif args.function == 'kdj_realtime_start':
        utils.calculate_function_runtime(kdj_realtime_start)
    elif args.function == 'daily_task':
        # win 每日自动执行任务
        utils.calculate_function_runtime(update)  # 更新股票数据
        utils.calculate_function_runtime(zixuan_start)  # 计算自选数据
        utils.calculate_function_runtime(kdj_daily_start)  # 计算全市场kdj相关信息
    elif args.function == 'dividendStart':
        # 计算股息率相关(一般分红时才需要计算一次)
        utils.calculate_function_runtime(dividendStart)
    else:
        print('函数名称输入错误')


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

if __name__ == "__main__":
    main()