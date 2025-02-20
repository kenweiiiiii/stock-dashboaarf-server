from datetime import datetime, time

# ✅ 记录缓存的收盘数据
cached_closing_data = None


def is_trading_time():
    """判断当前是否为交易时间"""
    now = datetime.now().time()
    return (time(9, 30) <= now <= time(11, 30)) or (time(13, 0) <= now <= time(15, 0))


def update_cached_closing_data(data):
    """更新收盘缓存数据"""
    global cached_closing_data
    cached_closing_data = data


def get_cached_closing_data():
    """获取缓存的收盘数据"""
    return cached_closing_data if cached_closing_data else []
