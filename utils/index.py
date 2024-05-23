import re

import numpy
import pandas
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from vnpy_ctastrategy.backtesting import load_bar_data
from vnpy.trader.object import OrderData, TradeData, BarData, TickData
from vnpy.trader.constant import (
    Direction,
    Offset,
    Exchange,
    Interval,
    Status,
)
from typing import Callable, List, Dict, Optional, Type
from datetime import datetime, timedelta
import time
import tushare as ts


# 支持中文
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# print(mpf.available_styles())
mpf_style = mpf.make_mpf_style(
    base_mpf_style='yahoo',
    rc={'font.family': 'SimHei', 'axes.unicode_minus': 'False'},
    marketcolors=mpf.make_marketcolors(up='red', down='green', inherit=True)
)

def get_percent(nowPrice: float, aimPrice: float):
    num = (aimPrice - nowPrice) / nowPrice
    return round(num * 100, 1)

def get_ma_price(series: pandas.Series, ma_num: int):
    last_index = series.count()
    if ma_num > last_index:
        last_index = ma_num
    return series[last_index-ma_num: last_index].mean()

def list_include(list, key: str, value):
    for item in list:
        if item[key] == value:
            return True
    return False

def getDataFrame(history_data):
    bar_data_dict_list = []
    for index, bardata in enumerate(history_data):
        bar_dict = {
            "index": index,
            "datetime": bardata.datetime,
            "open_price": bardata.open_price,
            "close_price": bardata.close_price,
            "low_price": bardata.low_price,
            "high_price": bardata.high_price,
            "turnover": bardata.turnover, # 成交额
            "volume": bardata.volume, # 成交额
        }
        bar_data_dict_list.append(bar_dict)
    df = pandas.DataFrame(bar_data_dict_list)
    # df['date'] = df['datetime']
    return df

def getStockDataFrame(only_stock = False):
    pro = ts.pro_api()

    # df1 = pd.read_csv('./assets/tushare_stock_basic.csv', dtype={'symbol': str})
    df1 = pro.stock_basic(exchange='', list_status='L', fields=[
        "ts_code", "symbol", "name", "area", "industry", "cnspell", "market", "list_date",
        "act_name", "act_ent_type", "list_status"
    ])

    # 此接口每天只能访问20次，报错时改为读取本地文件
    try:
        df2 = pro.bak_basic(limit=len(df1), fields=[
        "trade_date", "ts_code", "name", "industry", "area", "pe", "float_share", "total_share",
        "total_assets", "liquid_assets", "fixed_assets", "reserved", "reserved_pershare", "eps",
        "bvps", "pb", "list_date", "undp", "per_undp", "rev_yoy", "profit_yoy", "gpr", "npr",
        "holder_num"
        ])
        df2.to_csv('./assets/temp_tushare_bak_basic.csv', index=False, encoding='GBK')
    except Exception as e:
        print('bak_basic接口请求出错了，切换为读取本地文件：', e)
        df2 = pd.read_csv('./assets/temp_tushare_bak_basic.csv', dtype={'symbol': str}, encoding='GBK')

    df1 = df1.drop_duplicates(subset="ts_code")
    df2 = df2.drop_duplicates(subset="ts_code")
    # df['symbol'] = df['ts_code'].apply(lambda str: str.split('.')[0])
    df_stock = pd.merge(df1, df2, on='ts_code', how='inner', suffixes=('','_delete'))
    # 过滤掉退市股 和 ST
    df_stock = df_stock[df_stock['list_status'] == 'L']
    df_stock = df_stock[~df_stock['name'].str.contains('ST')]

    # 删掉merge时重复的列
    for column in df_stock.columns.tolist():
        if column.find("_delete") != -1:
            df_stock.drop(column, axis=1, inplace=True)

    if not only_stock:
        # 获取指数列表信息（接口返回8000多个，用不了这么多，暂时先通过列表维护需要用到的指数）
        df_index = pd.read_excel('./assets/tushare_index_basic.xlsx', dtype={'symbol': str})
        # 获取ETF基金列表信息
        df_fund = pro.fund_basic(market="E", status="L", fields=[
            "ts_code", "name", "management", "custodian", "fund_type", "list_date",
            "issue_amount", "status", "market", "m_fee", "c_fee", "p_value"
        ])

        df = pd.concat([df_stock, df_fund, df_index], ignore_index=True)
    else:
        df = df_stock

    # 动态计算symbol,exchange列
    new_symbol_cols = []
    new_exchange_cols = []
    for index, row in df.iterrows():
        symbol = row['ts_code'].split('.')[0]
        exchange = row['ts_code'].split('.')[1]
        if exchange_map.get(exchange) is not None:
            exchange = exchange_map[exchange]
        new_symbol_cols.append(symbol)
        new_exchange_cols.append(exchange)
    df['symbol'] = new_symbol_cols
    df['exchange'] = new_exchange_cols


    # 类型: ts_code, trade_date, open, close, pe
    return df

def getStockPlot(df, dotArr, title, axtitle, savePath):

    df['date']=df['datetime']
    df['open']=df['open_price']
    df['high']=df['high_price']
    df['low']=df['low_price']
    df['close']=df['close_price']
    df.set_index('date', inplace=True)

    plots = []
    for dot in dotArr:
        ap = mpf.make_addplot(dot['dotSeries'],  color=dot['color'], scatter=True, markersize=20, marker='o', panel=0)
        plots.append(ap)


    mpf.plot(
        df, type='candle',
        style=mpf_style, ylabel='Price', ylabel_lower='Volume',
        mav=(5, 10 , 30),
        volume=True,
        title=title,
        axtitle=axtitle,
        savefig=savePath,
        addplot=plots,
    )




    # plt.figure(figsize=(24, 12))
    # plt.title(title)
    #
    # fig, (ax1, ax2) = plt.subplots(2,1, sharex="row")
    # ax1.plot(df['datetime'], df['close_price'], label='close_price')
    # ax1.set_xlabel('Date')
    # ax1.set_ylabel('Price')
    #
    # ax2.bar(df['datetime'], df['volume'], label='volume', color='tab:green', alpha=0.3)
    # ax2.set_xticks([])
    # ax2.set_yticks([])

    # plt.legend()
    # plt.tight_layout()
    # plt.scatter(arc_points_df['datetime'], arc_points_df['close_price'], color='red', label='Arc Top')
    # return plt, ax1
    return plt

def makeSingleDotSeries(series:pandas.Series, index):
    res = pandas.Series([numpy.NAN] * len(series))
    res[index] = series[index]
    return res

def plotStock(title, df):
    plt = getStockPlot(title, df)
    plt.show()

exchange_map = {'SH': 'SSE', 'SZ': 'SZSE', 'BJ': 'BSE'}

def get_exchange(code: str) -> str | None:
    """code是ts_code或者symbol"""
    exchange = ''
    if code.find(".") != -1: exchange = code.split('.')[1]
    elif re.search('^[1|0|3]', code): exchange = "SZ"
    elif re.search('^[5|6]', code): exchange = "SH"
    elif re.search('^[4|8]', code): exchange = "BJ"
    # 基金 or 指数
    return exchange_map.get(exchange)

def get_vn_code(ts_code) -> str:
    symbol = ts_code.split('.')[0]
    exchange = get_exchange(ts_code)
    # 如果已经下载过了，则直接跳过
    return f"{symbol}.{exchange}"

# 获取最新的行情数据
def get_latest_bar_data(row):
    nowDate = datetime.now()
    # todo 获取最近30天的数据（貌似不能直接获取最后一条数据），再取最后一天
    start = nowDate - timedelta(30)
    history_data: List[BarData] = load_bar_data(
        symbol=row['symbol'],
        exchange=Exchange[row['exchange']],
        start=start,
        end=nowDate,
        interval=Interval.DAILY,
    )
    if len(history_data) == 0: return None
    return history_data[len(history_data) - 1]


# 计算函数的运行时间
def calculate_function_runtime(func):
    start_time = time.time()  # 记录开始时间
    func()  # 调用函数
    end_time = time.time()  # 记录结束时间

    # 计算运行时间（单位：秒）
    runtime_seconds = end_time - start_time

    # 将秒转换为分钟
    runtime_minutes = runtime_seconds / 60

    print("Function runtime:", runtime_minutes, "minutes")

def safe_division(a, b):
    try:
        result = a / b
    except ZeroDivisionError:
        return None
    return result

def get_datetime(time_str: str, time_format = '%Y%m%d'):
    # 根据时间字符串和格式初始化 datetime 对象
    return datetime.strptime(time_str, time_format)

# 获取股票的分红
def get_dividend_pct(ts_code: str, nowPrice: float, ttm = True) -> tuple[float, str]:
    df = pandas.read_csv("./assets/temp_dividendData.csv", dtype={ "end_date": str })
    df = df[df["ts_code"] == ts_code]
    year = datetime.now().year
    # df = df[df["end_date"].str.contains(f"{year-1}|{year}")]
    if ttm:
        df = df[df["end_date"].str.startswith(str(year-1), str(year))]
    else:
        df = df[df["end_date"].str.startswith(str(year))]
    df = df.sort_values(by="end_date", ascending = False)

    # 计算TTM的分红
    if ttm:
        date_flag = {}
        new_df = pandas.DataFrame()
        for index, item in df.iterrows():
            date = item["end_date"][4:]
            if date_flag.get(date) is None:
                new_df = new_df._append(item)
                date_flag[date] = True
    else:
        new_df = df

    if len(new_df) == 0:
        return 0, ''
    div_pct = round(new_df["cash_div_tax"].sum() / nowPrice, 3)
    end_date = new_df.iloc[0]["end_date"]
    return div_pct, end_date
