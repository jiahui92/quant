import math
import re
import statistics

import pandas
from datetime import datetime, timedelta

import pandas as pd
import utils.index as utils
import talib
from openpyxl import load_workbook

def kdj_daily_start():
    zx_df = utils.getStockDataFrame()
    zx_df = zx_df[['ts_code', 'name', 'industry', 'total_share', 'profit_yoy']]

    df = pandas.DataFrame(columns=zx_df.columns)
    df_stock = utils.getStockDataFrame(True)

    for index, row in zx_df.iterrows():
        # if index < 6000: continue

        if pd.isna(row['ts_code']): continue
        symbol = row['ts_code'].split('.')[0]
        exchange = utils.get_exchange(row['ts_code'])
        df_stock_filter = df_stock[df_stock["ts_code"] == row["ts_code"]]

        if exchange == None: continue

        nowPrice, ma5Percent, ma10Percent, ma20Percent, ma60Percent, bollHighPercent, bollLowPercent = maBoll(
            row['name'], row['ts_code'])
        row['nowPrice'] = nowPrice

        print(f"{index}/{len(zx_df)}")
        if pandas.isna(nowPrice) or nowPrice * row['total_share'] < 100:
            continue
        if row['profit_yoy'] < -10: continue


        stock_row = None
        if len(df_stock_filter) > 0:
            stock_row = df_stock_filter.iloc[0]


        if stock_row is not None:
            # 计算股息率
            dividend_pct, end_date = utils.get_dividend_pct(row["ts_code"], nowPrice)
            row['div %'] = dividend_pct * 100

            profit_yoy = stock_row['profit_yoy'] / 100
            row['div.dyn %'] = round((1 + profit_yoy) * dividend_pct * 100, 2)  # 动态股息率

            # 计算peg
            peg = utils.safe_division(stock_row['pe'], stock_row['profit_yoy'])
            row['peg'] = round(peg, 1)
            row['profit %'] = stock_row['profit_yoy']
        else:
            row['div %'] = ''
            row['div.dyn %'] = ''
            row['peg'] = ''
            row['profit %'] = ''

        # if row['peg'] is float and (row['peg'] < -2 or row['peg'] > 1.1): continue

        bar_datas = utils.get_bar_data(row['ts_code'], 100)
        data_dicts = [{
            'high': bar_data.high_price,
            'low': bar_data.low_price,
            'close': bar_data.close_price,
        } for bar_data in bar_datas]
        data = pd.DataFrame(data_dicts)

        kdj = utils.calculate_kdj(data)
        rsi = talib.RSI(data['close'], timeperiod=6)

        if kdj['J'].iloc[-1] > 20 or rsi.iloc[-1] > 30:
            continue
        # 跳过kdj还未反转的股票
        if kdj['K'].iloc[-1] < kdj['K'].iloc[-2] or kdj['J'].iloc[-1] < kdj['J'].iloc[-2] or rsi.iloc[-1] < rsi.iloc[-2]:
            continue


        row['K'] = round(kdj['K'].iloc[-1], 1)
        row['D'] = round(kdj['D'].iloc[-1], 1)
        row['J'] = round(kdj['J'].iloc[-1], 1)
        row['RSI'] = round(rsi.iloc[-1], 1)

        macd, macd_signal, macd_hist = talib.MACD(data['close'])




        row['ma5 %'] = ma5Percent
        row['ma10 %'] = ma10Percent
        row['ma20 %'] = ma20Percent
        row['ma60 %'] = ma60Percent
        row['boll'] = pd.NaT
        row['High %'] = bollHighPercent
        row['Low %'] = bollLowPercent


        arr = row['ts_code'].split('.')
        if len(arr) == 2:
            row['link'] = f"https://quote.eastmoney.com/{arr[1]}{arr[0]}.html"

        df = pandas.concat([df, row.to_frame().T], axis=0, ignore_index=True)

    # 把desc挪到最后一列
    columns_to_move = ['desc', 'link']
    new_columns = [col for col in df.columns if col not in columns_to_move] + columns_to_move
    df = df.reindex(columns=new_columns)

    df = df.sort_values(by="J")

    style_df = df.style.apply(add_df_style, axis=1, subset=[
        'ts_code', 'name', 'div.dyn %', 'peg', 'K', 'D', 'J', 'RSI', 'ma5 %', 'ma10 %', 'ma20 %', 'ma60 %', 'High %', 'Low %'
    ])



    # current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    excel_file = f"./assets/temp_kdj_daily.xlsx"
    style_df.to_excel(excel_file, engine='openpyxl', index=False)

    # 加载工作簿和工作表
    wb = load_workbook(excel_file)
    ws = wb.active
    # 冻结第一行
    ws.freeze_panes = 'A2'
    # 启用筛选功能
    ws.auto_filter.ref = ws.dimensions
    # 自动调整列宽
    for col in ws.columns:
        min_length = 10
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > min_length:
                    min_length = len(cell.value)
            except:
                pass
        adjusted_width = min_length + 2
        ws.column_dimensions[column].width = adjusted_width
    # 保存工作簿
    wb.save(excel_file)

def add_df_style(row: pandas.Series):
    darkgreen = 'background-color: mediumseagreen;'
    darkred = 'background-color: salmon;'
    lightgreen = 'background-color: lightgreen;'
    lightred = 'background-color: lightpink;'
    lightyellow = 'background-color: lightyellow;'

    result = []
    for key, value in row.items():
        # 字符串不需要染色，只处理数值
        if isinstance(value, str) or pandas.isna(value) or key in ["K", "D"]:
            result.append('')
        elif key == "J":
            if value < 20:
                if math.isclose(row['K'], row['D'], abs_tol=10) or row['K'] > row['D']:
                    result.append(darkgreen)
                else:
                    result.append(lightgreen)
            elif value > 80:
                if math.isclose(row['K'], row['D'], abs_tol=10) or row['K'] < row['D']:
                    result.append(darkred)
                else:
                    result.append(lightred)
            else: result.append('')
        elif key == "RSI":
            # 大于80超买，小于20超卖
            if value < 25: result.append(lightgreen)
            elif value > 75: result.append(lightred)
            else: result.append('')
        elif re.search('High', key):
            if value < 2: result.append(lightred)
            else: result.append('')
        elif re.search('Low', key) and value > -2:
            result.append(lightgreen)
        elif re.search('div', key):
            if value >= 5:
                result.append(lightgreen)
            else: result.append('')
        elif re.search('peg', key):
            if 0 <= value <= 0.8:
                result.append(lightgreen)
            else: result.append('')
        else:
            # ma
            if -2 < value < 0:
                result.append(lightgreen)
            elif 0 < value < 2:
                result.append(lightred)
            elif value == 0:
                result.append(lightyellow)
            else:
                result.append('')

    # name处重点标注颜色
    if result.count(lightgreen) >= 5: result[1] = lightgreen
    if result.count(lightred) >= 4: result[1] = lightred

    # 上涨 或 下跌趋势
    if isinstance(row['ma5 %'], (int, float)):
        if 0 >= row['ma5 %'] >= row['ma10 %'] >= row['ma20 %']:
            result[0] = lightgreen
        elif 0 <= row['ma5 %'] <= row['ma10 %'] <= row['ma20 %']:
            result[0] = lightred
        elif statistics.stdev([row['ma5 %'], row['ma10 %'], row['ma20 %']]) <= 0.5:
            result[0] = lightyellow

    return result


def maBoll(name, ts_code):
    emptyResult = pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT
    exchange = utils.get_exchange(ts_code)
    if exchange == None: return emptyResult

    history_data = utils.get_bar_data(ts_code, 100)
    nowDate = datetime.now()
    df = utils.getDataFrame(history_data)

    lastIndex = len(history_data) - 1
    if lastIndex == -1:
        print(name + ": 数据错误")
        return emptyResult
    nowPrice = df['close_price'].iloc[lastIndex]
    ma5 = utils.get_ma_price(df['close_price'], 5)
    ma10 = utils.get_ma_price(df['close_price'], 10)
    ma20 = utils.get_ma_price(df['close_price'], 20)
    ma60 = utils.get_ma_price(df['close_price'], 60)
    ma5weekly = utils.get_ma_price(df['close_price'], 5 * 5)
    ma10weekly = utils.get_ma_price(df['close_price'], 10 * 5)
    ma20weekly = utils.get_ma_price(df['close_price'], 20 * 5)
    std = df['close_price'][lastIndex - 20:lastIndex].std()
    bollHigh = ma20 + 2 * std
    bollLow = ma20 - 2 * std

    # 近期高价（弧形）?
    # 量？
    # 月线维度

    ma5Percent = utils.get_percent(nowPrice, ma5)
    ma10Percent = utils.get_percent(nowPrice, ma10)
    ma20Percent = utils.get_percent(nowPrice, ma20)
    ma60Percent = utils.get_percent(nowPrice, ma60)
    bollHighPercent = utils.get_percent(nowPrice, bollHigh)
    bollLowPercent = utils.get_percent(nowPrice, bollLow)

    # print(row["name"], ma5Percent, ma10Percent, ma20Percent, bollHighPercent, bollLowPercent)
    # table.add_row([
    #     row["name"], nowPrice,
    #     ma5Percent, ma10Percent, ma20Percent, ma30Percent, ma60Percent,
    #     bollHighPercent, bollLowPercent
    # ])
    return nowPrice, ma5Percent, ma10Percent, ma20Percent, ma60Percent, bollHighPercent, bollLowPercent

    # 输出结果
    #   标记某个股票的长时间段的结果

    # 已买：顶点提示，支撑点提示！！！

    #
    # # if (symbol == '300093'): print(preWithdrawal, preMin, lastMin)
    # isNotST = row['name'].find("ST") == -1
    # if isNotST and isStable and isWave and isGoodWithdrawal and withdrawaled > 45 and 60 < waveLen:
    #     title = f"预期回撤:{int(willWithdrawal)} 最大已回撤:{int(withdrawaled)} 利润:{int(profit)}  {row['symbol']} {row['name']} {row['industry']}"
    #     floatMarketValue = (row['float_share']*df.iloc[-1]['close_price'])
    #     axtitle = f"流通市值:{int(floatMarketValue)}亿 PE:{row['pe']} 利润同比:{int(row['profit_yoy'])}% 股东人数:{int(row['holder_num']/10000)}万"
    #
    #     print(title)
    #
    #     isGoodPeg = 0 < row['pe'] / row['profit_yoy'] <= 1
    #     pegPath = ''
    #     if isGoodPeg:
    #         pegPath = 'PEG-'
    #     savePath = "./studies/png2/" + pegPath + row['industry'] + row['symbol'] + ".png"
    #
    #     plt = utils.getStockPlot(df, dotArr, title, axtitle, savePath)
    #     plt.close()

    # plt.show()

if __name__ == "__main__":
    utils.calculate_function_runtime(kdj_daily_start)