import gevent
import gevent.monkey
gevent.monkey.patch_all()

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from api.stock_api import stock_bp, fetch_stock_data
from api.market_api import market_bp
from api.utils import is_trading_time

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")

# ✅ 注册蓝图（API 分模块管理）
app.register_blueprint(stock_bp)
app.register_blueprint(market_bp)


def push_stock_data():
    """WebSockets 实时推送最新股票数据"""
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
