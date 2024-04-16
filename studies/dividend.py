## 数据准备
##  获取近n年的分红，看是否稳定
##  获取近几年的利润
import time
from datetime import datetime

import pandas

# 预测分红率 = 预测分红 / 当日股价
# 预测分红 = （1 + 预测利润率）* 上期分红  （这里假设股利率稳定）
# 预测利润率 = 根据近三年利润增速预测 或者 研报增速


## 分红计算公式（利润加权）
##    近期利润的预测？？？这样计算不准确
##    券商未来利润的估计

# 查看指标
# 近期分红率是否稳定
# 近期利润增率是否稳定

from utils.index import getStockDataFrame, get_latest_bar_data
import utils.index as utils
import tushare as ts


pro = ts.pro_api()
def dividendStart():

    stock_data_frame = getStockDataFrame()
    df = pandas.DataFrame(columns=stock_data_frame.columns)
    for index, row in stock_data_frame.iterrows():
        # if index > 100: continue
        if row['pe'] > 50 or row['pe'] < 0 or row['profit_yoy'] < -10:
            # print(f"{row['ts_code']}: pe不符合要求，已过滤")
            continue

        div, end_date = getDividend(row)
        if div > 0.05:
            print(f"{row['name']}.{row['ts_code']}: {round(div*100,2)}%")
            new_row  = pandas.Series(row, index=stock_data_frame.columns)
            new_row["dividend"] = round(div*100,2)
            new_row["end_date"] = end_date
            df = pandas.concat([df, new_row.to_frame().T ], axis=0, ignore_index=True)

    cols = ['dividend', 'end_date']
    # 行排序
    df = df.sort_values(by=cols, ascending=False)
    # 栏目排序
    new_order = cols + [col for col in df if col not in cols]
    df = df.reindex(columns=new_order)

    print(df.head(50))
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    df.to_csv(f"./temp_dividend_{current_time}.csv", index=False, encoding='GBK')

def getDividend(row: pandas.DataFrame):
    # 获取分红数据
    df = pro.dividend(**{
        "ts_code": row['ts_code'],
        "limit": "20",
    }, fields=[
        "ts_code",
        "end_date",  # 分送年度
        "ann_date",
        "div_proc",  # 实施进度
        "cash_div_tax",  # 每股分红（税前）
        "record_date",
        "ex_date",
        "pay_date",
    ])
    # 接口限制300个/min
    time.sleep(0.2)

    # 往期分红率 = 分红 / 当时股价
    # xxx

    # 最低分红率 = 上期分红 / 当日股价
    div_rows = df[df['div_proc'] == '预案'].head(2)
    cash_div_tax = div_rows['cash_div_tax'].sum()

    bar_data = utils.get_latest_bar_data(row)
    if bar_data is None:
        print(f"缺少{row['ts_code']}.{row['name']}的BarData")
        return 0, ''

    # 分红率
    # todo: 有高送转的情况下，偏差率会很大
    cash_div_tax_percent = round(cash_div_tax / bar_data.close_price, 4)
    return cash_div_tax_percent, div_rows.iloc[0]['end_date']
