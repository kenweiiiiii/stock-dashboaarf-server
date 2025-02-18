import gevent
import gevent.monkey

gevent.monkey.patch_all()  # ✅ 让 gevent 兼容 Flask-SocketIO

import tushare as ts
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import pandas as pd
from datetime import datetime, time

# ✅ 设置 Tushare API Token
TS_TOKEN = '970731c03e50a00c461cb7c11922fe8a43142b9ea77346c19a18526b'
ts.set_token(TS_TOKEN)
pro = ts.pro_api()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")

# ✅ 记录缓存的收盘数据
cached_closing_data = None


def is_trading_time():
    """判断当前是否为交易时间"""
    now = datetime.now().time()
    return (time(9, 30) <= now <= time(11, 30)) or (time(13, 0) <= now <= time(15, 0))


def fetch_stock_data():
    """✅ 统一获取所有股票数据（无论交易时间还是收盘时间）"""
    try:
        df = ts.realtime_list()
        print(df.columns)
        if df is None or df.empty:
            print("⚠️ 获取数据为空")
            return []

        print("📊 获取到数据:", df.shape)
        return df.to_dict(orient="records")

    except Exception as e:
        print(f"❌ 获取数据失败: {e}")
        return []


def fetch_closing_data():
    """✅ 获取收盘数据（缓存机制）"""
    global cached_closing_data
    if cached_closing_data is None or len(cached_closing_data) == 0:
        print("📊 收盘后，首次获取数据...")
        cached_closing_data = fetch_stock_data()

    if cached_closing_data is None:
        return []  # 避免返回 None 导致前端报错

    return cached_closing_data


@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    """✅ REST API: 获取股票数据"""
    stock_data = fetch_stock_data() if is_trading_time() else fetch_closing_data()
    print(f"📊 API 返回数据: {len(stock_data)} 条")
    return jsonify({"stocks": stock_data[:100]})  # 默认返回前 100 条数据


def push_stock_data():
    """✅ WebSockets 实时推送最新股票数据"""
    while True:
        if is_trading_time():
            stock_data = fetch_stock_data()
            if stock_data and len(stock_data) > 0:
                socketio.emit("update_stock_data", {"stocks": stock_data})
                print("📊 WebSocket 推送数据:", len(stock_data), "条")
            gevent.sleep(5)  # 每 5s 发送一次最新数据
        else:
            print("⏸ 收盘后，WebSocket 不再推送数据")
            gevent.sleep(600)  # 休眠 10 分钟，避免高频查询


if __name__ == '__main__':
    gevent.spawn(push_stock_data)
    socketio.run(app, host='0.0.0.0', port=5002, debug=False, use_reloader=False)
