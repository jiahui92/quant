import math
import string
from datetime import datetime, time
import concurrent.futures

import pandas
import tushare as ts

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
    tradeDate = getLatestTradeDate()
    print("更新交易日为：" + tradeDate)

    overviews = dataManagerEngine.get_bar_overview()
    total: int = len(overviews)
    count: int = 0

    for overview in overviews:
        count += 1
        # progress = int(round(count / total * 100, 0))
        print(f"{overview.symbol}, 进度:{count}/{total}")
        update_one(overview, tradeDate)

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
def getLatestTradeDate() -> str:
    pro = ts.pro_api()
    df: pandas.DataFrame = pro.trade_cal(exchange='SSE', cal_date=datetime.now().strftime("%Y%m%d"), limit=1, isopen=1)
    if df["is_open"].iloc[0] == 1:
        current_date = datetime.now().date().strftime("%Y%m%d")
        open_date = df["cal_date"].iloc[0]
        # 当天未开市：tushare在17:30更新当天股市信息
        if open_date == current_date and datetime.now().time() > time(17, 30, 0):
            return open_date

    return df["pretrade_date"].iloc[0]


def get_item_by_index(arr, index):
    try:
        return arr[index]
    except IndexError:
        return None

# delete()
utils.calculate_function_runtime(update)
# utils.calculate_function_runtime(download)
