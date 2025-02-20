from dataclasses import fields
from datetime import datetime, time

from dateutil.utils import today
from flask import Blueprint, jsonify, request
import tushare as ts
import pandas as pd
import json

market_bp = Blueprint('market', __name__)

# ✅ 设置 Tushare API
TS_TOKEN = '970731c03e50a00c461cb7c11922fe8a43142b9ea77346c19a18526b'
ts.set_token(TS_TOKEN)
pro = ts.pro_api()

DEFAULT_INDEX_MAPPING = {
    "000001.SH": "上证指数",
    "000300.SH": "沪深 300",
    "399006.SZ": "创业板指",
    "000688.SH": "科创 50"
}

def is_trading_time():
    """✅ 判断当前是否为交易时间"""
    now = datetime.now().time()
    return (time(9, 30) <= now <= time(11, 30)) or (time(13, 0) <= now <= time(15, 0))


@market_bp.route('/api/market/indices', methods=['GET'])
def get_market_indices():
    """✅ 获取市场指数数据（交易时间实时获取，非交易时间获取收盘数据）"""

    try:
        index_mapping = request.args.get("indices")
        index_mapping = eval(index_mapping) if index_mapping else DEFAULT_INDEX_MAPPING  # ✅ 允许动态传入
        today = datetime.today().strftime("%Y%m%d")
        indices = []
        for code, name in index_mapping.items():
            try:
                if is_trading_time():
                    # ✅ **交易时间：获取最新实时数据**
                    df = ts.realtime_quote(ts_code=code)

                    if df.empty:
                        print(f"⚠️ 没有找到 {code} 的数据")
                        continue

                    price = float(df['PRICE'].iloc[0])
                    pre_close = float(df['PRE_CLOSE'].iloc[0])
                else:
                    # ✅ **非交易时间：获取最近收盘数据**

                    df = ts.realtime_quote(ts_code=code)


                    if df.empty:
                        print(f"⚠️ 没有找到 {code} 的收盘数据")
                        continue

                    price = float(df['PRICE'].iloc[0])
                    pre_close = float(df['PRE_CLOSE'].iloc[0])

                change = round(price - pre_close, 2)
                change_pct = round((change / pre_close) * 100, 2)

                # ✅ **获取趋势数据**
                # trend_df = pro.index_daily(ts_code=code, start_date="20240101", end_date=today)
                # trend_data = trend_df["close"].tolist()[-20:] if not trend_df.empty else []

                indices.append({
                    "指数名称": name,
                    "当前点位": price,
                    "指数涨跌": change,
                    "指数涨幅": f"{change_pct}%",
                    "趋势": "up" if change > 0 else "down",
                    # "趋势数据": trend_data
                })

            except Exception as e:
                print(f"❌ 获取 {name} ({code}) 数据失败: {e}")

        return jsonify({"indices": indices})

    except Exception as e:
        print(f"❌ 获取指数数据失败: {e}")
        return jsonify({"error": "获取指数数据失败"}), 500


@market_bp.route('/api/market/overview', methods=['GET'])
def get_market_overview():
    """✅ 获取市场概览数据"""
    today_day = datetime.today().strftime('%Y%m%d')

    try:
        # ✅ 获取股票涨跌分布数据
        stock_data = ts.realtime_list()
        mf_dc = pro.moneyflow_mkt_dc(start_date=today_day)  # 市场主力资金流向
        mf_ma = pro.daily_info(trade_date=today_day, exchange='SZ,SH')  #
        mf_hsgt = pro.moneyflow_hsgt(start_date=today_day)  # 沪深港通资金流向
        mf_mar = pro.margin(start_date=today_day)  # 融资融券数据

        # ✅ 计算涨跌分布
        up_count = (stock_data["CHANGE"] > 0).sum()
        down_count = (stock_data["CHANGE"] < 0).sum()
        no_change_count = (stock_data["CHANGE"] == 0).sum()

        # ✅ 获取主力净流入（单位：亿元）
        main_fund_inflow = round(mf_dc["net_amount"].astype(float).fillna(0).sum() / 1e8, 2)

        # ✅ 获取融资买入（单位：亿元）
        financing_buy = round(mf_mar["rzmre"].astype(float).fillna(0).sum() / 1e8, 2)

        # ✅ 计算沪深两市成交金额（单位：亿元）
        trade_amount = round(stock_data['AMOUNT'].astype(float).fillna(0).sum().sum() / 1e8, 2)

        # ✅ 交易状态检查
        today_status = pro.trade_cal(start_date=today_day, end_date=today_day)
        if today_status["is_open"].iloc[0] == 0:  # 0 代表非交易日
            open_market = "非交易日"
            next_tradetime = ""
        else:
            if is_trading_time():
                open_market = "已开市"
                next_tradetime = ""
            else:
                open_market = "未开市"
                now_time = datetime.now().time()
                if now_time < time(9, 15):
                    next_tradetime = "9:15分开盘"
                elif time(11, 30) < now_time < time(14, 57):
                    next_tradetime = "14:57分开盘"
                else:
                    next_tradetime = "明早9:15分开盘"

        # ✅ 组装返回数据
        overview_data = {
            "涨跌分布": {"上涨": int(up_count), "持平": int(no_change_count), "下跌": int(down_count)},
            "主力净流入": f"{main_fund_inflow} 亿",
            "融资买入": f"{financing_buy} 亿",
            "沪深两市成交金额": f"{trade_amount} 亿",
            "开市状态": open_market,
            "开市时间": next_tradetime
            #"成交额环比":
        }

        return jsonify(overview_data)

    except Exception as e:
        print(f"❌ 获取市场概览数据失败: {e}")
        return jsonify({"error": f"获取市场概览数据失败: {str(e)}"}), 500

