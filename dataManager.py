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

# 沪市 [600000,605600]
# 科创 [688001,688982]

# 深市 [000001,003817]
# 创业板 [300001,301559]

# 北交所 [x,x]

def printError(msg):
    print(msg)


for index, row in getStockDataFrame().iterrows():
    if row['symbol'] < '301559': continue
    count = dataManagerEngine.download_bar_data(
        symbol=row['symbol'],
        exchange=Exchange[row['exchange']],
        # exchange=Exchange.SSE,
        start=datetime(2015, 1, 1),
        interval=Interval.DAILY,
        output=printError,
    )
    print(row['symbol'], count)
    # time.sleep(0.01)



# get all stock info
## 沪深、科创、北证
# for get
