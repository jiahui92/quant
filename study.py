from studies.wave import wave, find_wave
from vnpy.trader.constant import Exchange, Interval
from utils.index import getStockDataFrame, plotStock


for index, row in getStockDataFrame().iterrows():
    find_wave(row)
