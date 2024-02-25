import string
import time
from datetime import datetime

# from vnpy.trader.database import database_manager
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.engine import MainEngine
from vnpy_datamanager.engine import ManagerEngine
from utils.index import getStockDataFrame

mainEngine = MainEngine()
dataManagerEngine = ManagerEngine(mainEngine, None)

def download():
    df = getStockDataFrame()
    count = 0
    total = len(df)
    for index, row in df.iterrows():
        # if row['symbol'] != '605111': continue
        try:
            bardataCount = dataManagerEngine.download_bar_data(
                symbol=row['symbol'],
                exchange=Exchange[row['exchange']],
                # exchange=Exchange.SSE,
                start=datetime(2015, 1, 1),
                interval=Interval.DAILY,
                output=printError,
            )
            count += 1
            progress = int(round(count / total * 100, 0))
            print(f"{row['symbol']} {bardataCount}, 进度:{progress}%")
        except:
            print('下载出错: ' + row['symbol'] + " " + row['exchange'])

def update():
    overviews = dataManagerEngine.get_bar_overview()
    total: int = len(overviews)
    count: int = 0
    for overview in overviews:
        count += 1
        # progress = int(round(count / total * 100, 0))
        print(f"{overview.symbol}, 进度:{count}/{total}")

        try:
            dataManagerEngine.download_bar_data(
                overview.symbol,
                overview.exchange,
                overview.interval,
                overview.end,
                printError
            )
        except:
            print('更新出错，删除数据后重新下载')
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


def delete():
    dataManagerEngine.delete_bar_data(
        symbol='000018',
        exchange=Exchange.SSE,
        interval=Interval.DAILY,
    )
    print('deleted')

def printError(msg):
    print(msg)

# download()
update()
# delete()