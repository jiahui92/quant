import os
d = os.path.dirname(__file__)  # 获取当前路径
parent_path = os.path.dirname(d)  # 获取上一级路径
os.sys.path.append(parent_path)    # 如果要导入到包在上一级

import time
from datetime import datetime
import pandas

import utils.index as utils
import tushare as ts

# 预测分红率 = 预测分红 / 当日股价
# 预测分红 = （1 + 预测利润率）* 上期分红  （这里假设股利率稳定）
# 预测利润率 = 根据近三年利润增速预测 或者 研报增速

# 分红走势图

## 分红计算公式（利润加权）
##    近期利润的预测？？？这样计算不准确
##    券商未来利润的估计


# todo: 获取的数据貌似有问题（分红年度、分红率的计算）
pro = ts.pro_api()
def dividendStart():

    stock_data_frame = utils.getStockDataFrame()
    df = pandas.DataFrame(columns=stock_data_frame.columns)

    count = 0
    for index, row in stock_data_frame.iterrows():
        count += 1
        # if index > 10: continue
        if row['pe'] > 50 or row['pe'] < 0 or row['profit_yoy'] < -10 or row['rev_yoy'] < -10:
            # print(f"{row['ts_code']}: pe不符合要求，已过滤")
            continue

        peg = utils.safe_division(row['pe'], row['profit_yoy'])
        if peg is None or peg > 1 or peg < 0:
            continue

        # todo 盈利是否稳定
        # todo 分红是否稳定

        # todo 地产链置灰
        # todo 今天更新的标红


        bar_data = utils.get_latest_bar_data(row)
        div, end_date = getDividend(row, bar_data)
        if div > 0.05:
            print(f"{row['ts_code']}.{row['name']}: {round(div*100,2)}% {end_date}   进度:{count}/{len(stock_data_frame)}")
            new_row = pandas.Series(row, index=stock_data_frame.columns)
            new_row["end_date"] = end_date
            new_row["dividend"] = round(div*100,1)
            new_row["profit_yoy"] = round(new_row['profit_yoy'], 0)
            new_row["peg"] = round(peg, 1)
            new_row["total_mv"] = int(bar_data.close_price * new_row['total_share'])  # 总市值
            new_row["float_mv"] = int(bar_data.close_price * new_row['float_share'])  # 流通市值
            df = pandas.concat([df, new_row.to_frame().T], axis=0, ignore_index=True)

    # 行排序
    df = df.sort_values(by=['end_date', 'dividend'], ascending=False)
    # 栏目排序
    cols = [
        'end_date', 'dividend', 'peg', 'float_mv', 'total_mv',
        'symbol', 'name', 'pe', 'pb', 'profit_yoy', 'rev_yoy', 'holder_num'
    ]
    new_order = cols + [col for col in df if col not in cols]
    df = df.reindex(columns=new_order)

    print(df.head(50))
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    df.to_csv(f"./assets/temp_dividend_{current_time}.csv", index=False, encoding='GBK')

def getDividend(row: pandas.DataFrame, bar_data):
    if bar_data is None:
        print(f"缺少{row['ts_code']}.{row['name']}的BarData")
        return 0, ''

    # 获取分红数据
    df = pro.dividend(**{
        "ts_code": row['ts_code'],
        "limit": "100",
    }, fields=[
        "ts_code",
        "end_date",  # 分送年度
        # "ann_date",
        "stk_div",  # 每股送转
        "div_proc",  # 实施进度
        "cash_div_tax",  # 每股分红（税前）
        # "record_date",
        # "ex_date",
        # "pay_date",
    ])
    # 接口限制300个/min
    time.sleep(0.2)
    if len(df) == 0: return 0, ''

    # 往期分红率 = 分红 / 当时股价
    # xxx

    # 最低分红率 = 上期分红 / 当日股价
    div_rows = df[df['div_proc'] == '预案'].head(2)
    cash_div_tax = div_rows['cash_div_tax'].sum()

    # 分红率
    # todo: 有高送转的情况下，偏差率会很大
    cash_div_tax_percent = round(cash_div_tax / bar_data.close_price, 4)
    return cash_div_tax_percent, div_rows.iloc[0]['end_date']


if __name__ == "__main__":
    utils.calculate_function_runtime(dividendStart)