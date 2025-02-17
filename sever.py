import gevent
import gevent.monkey
gevent.monkey.patch_all()  # ✅ 让 gevent 兼容 Flask-SocketIO

import tushare as ts
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import pandas as pd
import numpy as np
from datetime import datetime, time

# ✅ 设置 Tushare API Token（请替换成你的 Token）
TS_TOKEN = '970731c03e50a00c461cb7c11922fe8a43142b9ea77346c19a18526b'  # ← 你需要替换成自己的 Tushare Token
ts.set_token(TS_TOKEN)
pro = ts.pro_api()

app = Flask(__name__)
CORS(app)

# ✅ 使用 gevent 作为 Flask-SocketIO 后端
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")


def is_trading_time():
    """
    判断当前是否为交易时间：
    - 上午交易：09:30 - 11:30
    - 下午交易：13:00 - 15:00
    """
    now = datetime.now().time()
    return (time(9, 30) <= now <= time(11, 30)) or (time(13, 0) <= now <= time(15, 0))

def is_trading_day():
    today = datetime.today().strftime("%Y%m%d")
    trade_dates = pro.trade_cal(exchange='SSE', is_open='1', fields='cal_date')

    if today not in trade_dates["cal_date"].values:
        return True
    else:
        return False



def get_all_stock_codes():
    """
    获取当前所有正常上市的股票代码
    """
    try:
        stock_list = pro.stock_basic(exchange='', list_status='L', fields='ts_code')['ts_code'].tolist()
        print(f"📋 获取到 {len(stock_list)} 只股票代码")
        print(stock_list)
        return stock_list
    except Exception as e:
        print(f"❌ 获取股票列表失败: {e}")
        return []


def fetch_real_stock_data(stock_code):
    """
    获取单只股票的实时数据
    """
    try:
        # df = ts.realtime_quote(stock_code,fields='ts_code,name')
        df=ts.realtime_list()
        print(df)
        if df.empty:
            return None

        # required_columns = ["name", "ts_code","data","time","open","pre_close","price","high", "low","bid","ask","volume","amount"]
        # if not all(col in df.columns for col in required_columns):
        #     return None

        return {
            "名称": df["NAME"][0],
            "代码": df[ "TS_CODE"][0],
            "日期": (df["DATE"][0]) ,
            "时间": (df["TIME"][0]) ,
            "开盘价": float(df["OPEN"][0]) if df["OPEN"][0] else 0,
            "昨收价": float(df["PRE_CLOSE"][0]) if df["PRE_CLOSE"][0] else 0,
            "现价": float(df["PRICE"][0]) if df["PRICE"][0] else 0,
            "今日最高价": float(df["HIGH"][0]) if df["HIGH"][0] else 0,
            "今日最低价": float(df[ "LOW"][0]) if df[ "LOW"][0] else 0,
            "买一报价": float(df["BID"][0]) if df["BID"][0] else 0,
            "卖一”报价": float(df["ASK"][0]) if df["ASK"][0] else 0,
            "成交量": float(df["VOLUME"][0]) if df["VOLUME"][0] else 0,
            "成交金额": float(df["AMOUNT"][0]) if df["AMOUNT"][0] else 0

        }
    except Exception as e:
        print(f"❌ 获取 {stock_code} 实时数据失败: {e}")
        return None


@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    """
    REST API: 获取股票数据
    - 交易时间: 获取所有股票的实时数据
    - 非交易时间: 获取所有股票最近的收盘数据
    """
    stock_list = ts.realtime_list()[:20]
    # stocks = [fetch_real_stock_data(code) for code in stock_list if fetch_real_stock_data(code)]

    return jsonify({"stocks": stock_list})


def push_stock_data():
    """
    WebSockets 实时推送最新股票数据
    """
    while True:
        stock_list = ts.realtime_list()
        # stocks = fetch_real_stock_data(stock_list)
        print(stock_list)
        if stock_list is not None and not stock_list.empty:
            socketio.emit('update_stock_data', {"stocks": stock_list})

        gevent.sleep(30)  # ✅ 避免阻塞


@socketio.on('connect')
def handle_connect():
    print("✅ 客户端 WebSocket 连接成功！")


if __name__ == '__main__':
    gevent.spawn(push_stock_data)
    socketio.run(app, host='0.0.0.0', port=5002, debug=False, use_reloader=False)
