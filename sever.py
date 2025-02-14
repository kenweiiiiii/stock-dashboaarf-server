from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 模拟股票数据
stock_data = [
    {"name": "中芯国际", "code": "600108.SH", "open": 50.0, "close": 60.0, "change": "+20.00%", "high": 60.0, "low": 30.0, "trend": "up"},
    {"name": "宇树科技", "code": "600109.SH", "open": 50.0, "close": 40.0, "change": "-10.00%", "high": 53.0, "low": 45.0, "trend": "down"},
    {"name": "等等科技", "code": "600108.SH", "open": 50.0, "close": 60.0, "change": "+20.00%", "high": 60.0, "low": 30.0, "trend": "up"},
    {"name": "亿点科技", "code": "600109.SH", "open": 50.0, "close": 40.0, "change": "-10.00%", "high": 53.0, "low": 45.0, "trend": "down"},
    {"name": "不二数魅", "code": "600109.SH", "open": 50.0, "close": 40.0, "change": "-10.00%", "high": 53.0, "low": 45.0, "trend": "down"}

]

@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    return jsonify({"stocks": stock_data})  # 返回 JSON 数据

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)


