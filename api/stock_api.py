import tushare as ts
from flask import Blueprint, jsonify
from api.utils import is_trading_time, get_cached_closing_data, update_cached_closing_data

stock_bp = Blueprint('stock_api', __name__)

# ✅ 设置 Tushare API Token
TS_TOKEN = '970731c03e50a00c461cb7c11922fe8a43142b9ea77346c19a18526b'
ts.set_token(TS_TOKEN)
pro = ts.pro_api()


def fetch_stock_data():
    """获取所有股票数据（交易时间/收盘时间通用）"""
    try:
        df = ts.realtime_list()
        if df is None or df.empty:
            print("⚠️ 获取数据为空")
            return []

        return df.to_dict(orient="records")

    except Exception as e:
        print(f"❌ 获取股票数据失败: {e}")
        return []


@stock_bp.route('/api/stocks', methods=['GET'])
def get_stocks():
    """提供 REST API 访问股票数据"""
    stock_data = fetch_stock_data() if is_trading_time() else get_cached_closing_data()

    if not stock_data:
        stock_data = fetch_stock_data()
        update_cached_closing_data(stock_data)  # 缓存数据，避免重复获取

    print(f"📊 API 返回数据: {len(stock_data)} 条")
    return jsonify({"stocks": stock_data[:100]})  # 默认返回前 100 条
