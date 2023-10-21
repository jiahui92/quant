import numpy
import pandas
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt


# 支持中文
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

print(mpf.available_styles())
mpf_style = mpf.make_mpf_style(
    base_mpf_style='yahoo',
    rc={'font.family': 'SimHei', 'axes.unicode_minus': 'False'},
    marketcolors=mpf.make_marketcolors(up='red', down='green', inherit=True)
)

def getStockDataFrame():
    return pd.read_csv('./assets/tushare_stock_basic_20231014193537.csv', dtype={'symbol': str})
    # for index, row in df.iterrows():
    #     callback(row)

def getStockPlot(df, title, savePath, dotArr):

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
