import math
import string
from datetime import datetime, time, timedelta
import concurrent.futures

import pandas
import tushare as ts
from typing import List

from vnpy.trader.object import OrderData, TradeData, BarData, TickData
# from vnpy.trader.database import database_manager
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.engine import MainEngine
from vnpy_datamanager.engine import ManagerEngine
import utils.index as utils

mainEngine = MainEngine()
dataManagerEngine = ManagerEngine(mainEngine, None)

def download():
    overviews = dataManagerEngine.get_bar_overview()
    existMap = {}
    for overview in overviews:
        existMap[overview.symbol] = True

    df = utils.getStockDataFrame()
    count = 0
    total = len(df)
    for index, row in df.iterrows():
        count += 1
        # if row['symbol'] != '605111': continue
        # if row['exchange'] != 'BSE': continue
        # delete_one(row)

        # 如果已经下载过了，则直接跳过
        if existMap.get(row['ts_code'].split('.')[0]): continue

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
            print(f"{row['symbol']}.{row['name']}, 进度:{progress}%")
        except:
            print('下载出错: ' + row['symbol'] + " " + row['exchange'])

def update():
    overviews = dataManagerEngine.get_bar_overview()
    overviews.sort(key=lambda x: x.end)
    overview = overviews[int(len(overviews)/2)]

    trade_dates = get_trade_dates(overview.end)
    trade_dates.reverse()
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
    download()

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


def update_one_day(tradeDate: str):
    pro = ts.pro_api()
    # 每次最多1W条数据，需要区分股票、基金、指数分别进行请求
    df = pro.daily(**{
        "trade_date": tradeDate,
    }, fields=[
        "ts_code", "trade_date", "open", "high", "low", "close", "pre_close", "change", "pct_chg", "vol", "amount"
    ])

    bars: List[BarData] = []

    print(f"count:{len(df)}")
    if len(df) == 0: return

    for index, row in df.iterrows():
        symbol = row['ts_code'].split('.')[0]
        bar: BarData = BarData(
            symbol=symbol,
            exchange=Exchange[utils.get_exchange(row['ts_code'])],
            datetime=utils.get_datetime(tradeDate),
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
        exchange=Exchange[overview.exchange],
        interval=Interval.DAILY,
    )
    print('deleted')

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
