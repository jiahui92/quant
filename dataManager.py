import math
import string
from datetime import datetime, time, timedelta
import concurrent.futures

import pandas
import pandas as pd
import tushare as ts
from typing import List

from vnpy.trader.object import OrderData, TradeData, BarData, TickData
# from vnpy.trader.database import database_manager
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.engine import MainEngine
from vnpy_datamanager.engine import ManagerEngine
from vnpy_tushare.tushare_datafeed import to_ts_asset

import utils.index as utils

mainEngine = MainEngine()
dataManagerEngine = ManagerEngine(mainEngine, None)

def download(redownload = True):
    overviews = dataManagerEngine.get_bar_overview()
    existMap = {}

    for overview in overviews:
        key = f"{overview.symbol}.{overview.exchange.value}"
        if redownload:
            existMap[key] = overview
        else:
            existMap[key] = True

    df = utils.getStockDataFrame()
    count = 0
    total = len(df)
    for index, row in df.iterrows():
        count += 1
        # if row['symbol'] != '605111': continue
        # if row['exchange'] != 'BSE': continue
        # delete_one(row)

        # 如果已经下载过了，则直接跳过
        key = utils.get_vn_code(row['ts_code'])
        # 是否为指数: 指数的更新形式暂时为重新下载
        symbol = row['ts_code'].split('.')[0]
        is_index = to_ts_asset(symbol, Exchange[utils.get_exchange(row['ts_code'])]) == "I"
        if not is_index and existMap.get(key) is True:
            continue
        # 先删除再重新下载
        if redownload:
            delete_one(existMap.get(key))

        try:
            bardataCount = dataManagerEngine.download_bar_data(
                symbol=row['symbol'],
                exchange=Exchange[row['exchange']],
                # exchange=Exchange.SSE,
                start=datetime(2015, 1, 1),
                interval=Interval.DAILY,
                output=printError,
            )
            progress = int(round(count / total * 100, 0))
            print(f"{row['ts_code']}.{row['name']}, 进度:{progress}%")
        except:
            print('下载出错: ' + row['ts_code'])

def update():
    overviews = dataManagerEngine.get_bar_overview()
    overviews.sort(key=lambda x: x.end)
    overview = overviews[int(len(overviews)/2)]

    trade_dates = get_trade_dates(overview.end)
    trade_dates.reverse()

    # trade_dates = ['20240506']
    for trade_date in trade_dates:
        print("正在更新交易日：" + trade_date)
        update_one_day(trade_date)

    # overviews = dataManagerEngine.get_bar_overview()
    # total: int = len(overviews)
    # count: int = 0

    # for overview in overviews:
    #     count += 1
    #     # progress = int(round(count / total * 100, 0))
    #     print(f"{overview.symbol}, 进度:{count}/{total}")
    #     update_one(overview, tradeDate)

    # 每次更新时，根据最新的./assets/*.csv下载新股
    download(False)

    # max_parallel = 2
    # # lastStartTime = time.time_ns()
    # for index in range(math.ceil(total / max_parallel)):
    #     # sleepTime = 1000_000_000 - (time.time_ns() - lastStartTime)
    #     # lastStartTime = time.time_ns()
    #     #最大限制1分钟500个
    #     # if sleepTime > 0: time.sleep(sleepTime / 1000_000_000)
    #     count += max_parallel
    #     print(f"{overviews[index*max_parallel].symbol}, 进度:{count}/{total}")
    #     with concurrent.futures.ThreadPoolExecutor() as executor:
    #         # 提交函数执行任务，并获得 Future 对象列表
    #         futures = [executor.submit(update_one, get_item_by_index(overviews, index*max_parallel+i), tradeDate) for i in range(max_parallel)]
    #         # 获取每个任务的结果
    #         results = [future.result() for future in concurrent.futures.as_completed(futures)]

def update_one_day(trade_date: str):
    pro = ts.pro_api()
    # 每次最多1W条数据，需要区分股票、基金、指数分别进行请求
    df_stock = pro.daily(trade_date=trade_date)  # 股票
    # 指数: 暂时在download，因为symbol必传，无法优化
    # df_index = pro.index_daily(trade_date=trade_date)
    df_fund = pro.fund_daily(trade_date=trade_date)  # 基金
    # df_fund = df_fund[df_fund['market'] == 'E']
    # df_fund = df_fund[df_fund['status'] == 'L']

    df = pd.concat([df_stock, df_fund])
    df.reset_index()


    bars: List[BarData] = []

    # print(f"stock:{len(df_stock)}, index:{len(df_index)}, fund:{df_fund}")
    print(f"stock:{len(df_stock)}, fund:{len(df_fund)}")
    if len(df) == 0: return

    overviews = dataManagerEngine.get_bar_overview()
    existMap = {}
    for overview in overviews:
        key = f"{overview.symbol}.{overview.exchange.value}"
        existMap[key] = True

    for index, row in df.iterrows():
        symbol = row['ts_code'].split('.')[0]
        exchange = Exchange[utils.get_exchange(row['ts_code'])]

        print(f"{row['ts_code']}, {index}/{len(df)}")

        key = utils.get_vn_code(row['ts_code'])
        if existMap.get(key) is None:
            continue

        bar: BarData = BarData(
            symbol=symbol,
            exchange=exchange,
            datetime=utils.get_datetime(trade_date),
            interval=Interval.DAILY,
            volume=float(row['vol']),
            open_price=float(row['open']),
            high_price=float(row['high']),
            low_price=float(row['low']),
            close_price=float(row['close']),
            turnover=float(row['amount']),
            open_interest=float(0),
            gateway_name="DB",
        )
        # 内部不支持批量更新不同的symbol的overview，暂时只能循环遍历更新先（大概耗时1min）
        dataManagerEngine.database.save_bar_data([bar])


def update_one(overview, tradeDate: str):
    if overview == None: return
    # 已经更新到最新交易日了
    if overview.end.strftime("%Y%m%d") == tradeDate: return
    # 上年的退市股不再更新
    if overview.end.strftime("%Y%m%d") < "20231231":
        delete_one(overview)
        print(overview.symbol + ': 删除退市股')
        return

    try:
        dataManagerEngine.download_bar_data(
            overview.symbol,
            overview.exchange,
            overview.interval,
            overview.end,
            printError
        )
        # print(overview.symbol + ': 更新成功')
    except Exception as e:
        print(overview.symbol + ': 更新出错，删除数据后重新下载 ' + str(e))
        dataManagerEngine.delete_bar_data(
            overview.symbol,
            overview.exchange,
            overview.interval,
        )
        dataManagerEngine.download_bar_data(
            symbol=overview.symbol,
            exchange=overview.exchange,
            interval=overview.interval,
            start=datetime(2015, 1, 1),
            output=printError
        )

def delete_one(overview):
    dataManagerEngine.delete_bar_data(
        symbol=overview.symbol,
        exchange=overview.exchange,
        interval=Interval.DAILY,
    )
    print('deleted')


# 下载近三年的分红数据
def downloadDividendData():
    file_path = "./assets/temp_dividendData.csv"
    cols = {"ts_code": str, "end_date": str}
    try:
        dividend_df = pandas.read_csv(file_path, dtype=cols)
    except:
        dividend_df = pandas.DataFrame(columns=cols.keys())
    stock_data_frame = utils.getStockDataFrame(True)
    count = 0
    start_date = "20210101"
    end_date = "202301231"
    for index, row in stock_data_frame.iterrows():
        # if count > 2000: break
        count += 1
        print(f"{count}/{len(stock_data_frame)}")

        # 如果已存在了就不请求
        dividend_df_stock = dividend_df[dividend_df["ts_code"] == row["ts_code"]]
        dividend_df_filter = dividend_df_stock[dividend_df_stock["end_date"] >= end_date]
        if len(dividend_df_filter) > 0:
            continue

        # 接口限制300个/min
        time.sleep(0.2)
        df = ts.pro_api().dividend(**{
            "ts_code": row['ts_code'],
            "limit": "100",
        }, fields=[
            "ts_code",
            "end_date",  # 分送年度
            # "ann_date",  # 公告日
            "stk_div",  # 每股送转
            "div_proc",  # 实施进度
            "cash_div_tax",  # 每股分红（税前）
            # "record_date",  # 登记日
            # "ex_date",  # 除权日
            # "pay_date",  # 派息日
        ])

        # 计算上次已经更新到的时间
        if len(dividend_df_stock) > 0:
            length = len(dividend_df_stock)
            update_date = dividend_df_stock.iloc[length - 1]["end_date"]
        else:
            update_date = "20770101"
        df_filter = df[df["end_date"] >= start_date]
        df_filter = df_filter[df_filter["end_date"] < update_date]
        # df_filter = df_filter[df_filter["cash_div_tax"] != 0]
        df_filter = df_filter[df_filter["div_proc"].isin(["预案"])]  # "实施"
        df_filter = df_filter.sort_values(by="end_date")

        if len(df_filter) == 0:
            print(f"{row['ts_code']} {row['name']}: 没有分红数据")
            continue

        if len(dividend_df) > 0:
            dividend_df = dividend_df._append(df_filter, True)
        else:
            dividend_df = df_filter

        dividend_df.to_csv(file_path)

def printError(msg):
    print(msg)

# 获取最近一次的交易日
def get_trade_dates(start: datetime) -> List[str]:
    pro = ts.pro_api()
    start_date = (start + timedelta(days=1)).strftime("%Y%m%d")
    df: pandas.DataFrame = pro.trade_cal(exchange='SSE', start_date= start_date, end_date=datetime.now().strftime("%Y%m%d"), is_open=1)
    return df['cal_date'].tolist()

    # if df["is_open"].iloc[0] == 1:
    #     current_date = datetime.now().date().strftime("%Y%m%d")
    #     open_date = df["cal_date"].iloc[0]
    #     # 当天未开市：tushare在17:00更新当天股市信息
    #     if open_date == current_date and datetime.now().time() > time(17, 1, 0):
    #         return open_date
    #
    # return df["pretrade_date"].iloc[0]


def get_item_by_index(arr, index):
    try:
        return arr[index]
    except IndexError:
        return None

# delete()
utils.calculate_function_runtime(update)
# utils.calculate_function_runtime(download)
