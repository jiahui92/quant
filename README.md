https://zhuanlan.zhihu.com/p/647611800
# 项目初始化
* pip install -r requirements.txt
  * pip freeze > requirements.txt(生成依赖)
* tushare里的api.pro_bar.adj='qfq'（默认值修改为前复权）
  * ./site-packages/tushare/pro/data_pro.py

* run.py 启动回测程序
* backtesting.py 断点调试策略文件
* study.py

MA + BOOL + 量 + 自选股


数据
* 每天请求股票列表
* 删除不在列表里的数据
* 定时更新

明显信号：
* 直接介入
* 信号介入
  * 连续3天小涨（这种好介入，风险低）
  * 成交量大涨，并且上涨（介入风险大）
  * 二次探底确认
* 卖出
  * 放量顶冲不过去
  * 破位卖出
  * 10d卖出
* 股票较多的时候，可以调大回撤
* 测试下10%等小区间的

* 买入点
  * 换手率
  * 动量策略？

策略！！！
* 50%波浪
  * 近几天平稳
* 小市值策略
  * 昨天收盘价
  * 今天开盘价
* 动量策略 + 龙虎榜
* 港股通
* PEG
* 研报：券商、价格/涨幅、持有评级、无研报
* 股票回购

mpf文档
https://github.com/matplotlib/mplfinance/blob/master/examples/addplot.ipynb



# TODO
* 识别的点位太少（波峰识别不准确）
  * 预处理数据，标记所有波峰，并且标记low,high price
    * 波峰里面还会包含小波峰
  * 往前寻找支撑点
  * 买入时机
    * 尾盘买入？这个省事，但要统计概率，做好止损
    * 实盘结合量能来决定介入时机？
* -50%

# 策略
* 中际旭创最近两次探底走势？
  * 拿到所有的数据
  * 识别波浪顶底
    * 底：止跌、顶：MA
    * 止损
  * 再测试别的股票
  * 获取A股所有数据
* 追涨策略
* ETF T0
  * 看图/波动是否足够大
  * tick数据
* 期货


# roadmap
* [ ] 策略研究
  * [x] <font color="red">验证：是否有效、收益/风险评估</font>
  * [ ] 开发
    * [ ] <font color="red">策略来源（别人已验证策略/因子库）</font>
    * [ ] uni-bar
    * [ ] 契合模型数据
  * [ ] 多策略：针对验证指标来做完善
  * [ ] 接入模型
  * [ ] chatGPT
* [ ] 量化系统/工具
  * [x] 获取数据
  * [ ] 回测
    * [x] nvpy, backtrader
    * [ ] pandas-ts 技术指标库
  * [ ] 交易
    * [ ] 模拟/实盘交易
    * [ ] 拆单


# 策略研究
* <font color="red">因子：fama、波动、ma、boll</font>
* Boll+MACD
* 三浪
* uni-bar
* 判断顶底概率
  * 结合概率逐步买卖
  * 离场时机：波动变小
* 信号识别（时间点、空间）
  * 识别小散/机构单子
    * 了解拆单工具
* 资金、技术指标、价值指标
  * 资金占比：黄金、债券、股市（国、行业）

有效因子
* Boll


## 验证
* <font color="red">是否有效（多数据源验证）</font>
  * 对比市场(hs300)
    * 超额收益
    * alpha: 与市场对比超额收益（收益指标）
    * beta:  与市场对比波动性（风险指标）
  * 多数据源验证：防止幸存者偏差、过拟合
    * 不同股票、年份
    * tip: 先拿噪音小的市场来验证？比如hs300
  * 造数据验证
    * 
* 收益/风险评估
  * 收益
    * 年化、超额年化
  * 风险
    * 夏普（超额收益所承担的风险：性价比）
    * 最大回撤
    * 盈亏比例/胜率

## 其它
* 开发新策略
  * K线周期：15min、日K
  * 策略失效？自动停止？
  * unit-bar
  * 市场：股票、指数、期货、btc
* 工具

## 问题
* 单因子验证结果差，可能只是有偏科？如果搭配在一起用可能会很好？

# draf
[基于机器学习提升的轮动多因子量化选股模型](https://www.tipdm.org/u/cms/www/201908/08105038ojo4.pdf)

## 因子
每月重新检验有效性
* fama: 市场、规模、价值、盈利、投资
* 估值因子、成长因子
* 杠杆

## 模型
* 训练随机森林模型
  * 入参：各技术指标
    * pandas-ta 技术指标库（量化入参，而不是bool）
  * 预测：后1d~5d的数据(短期可能噪音太大，试一下周线？)，各涨跌幅概率

## chatGPT
chatGPT预测行业热度，分数/系数
* 训练：给出利好利空的分数，并且举几个例子给GPT
* 入参：当天的新闻和贴吧、微信指数（股票、开户、销户）
* 出参：分数

## 其它
* 机器学习寻找因子
* 跟随资金
  * 主力会隐藏资金，但散户不行
  * 主力布局阶段
* 龙虎榜

## vnpy支持北交所修改的文件
* D:\veighna_studio\Lib\site-packages\vnpy_tushare\tushare_datafeed.py
  * EXCHANGE_VT2TS
  * to_ts_asset

