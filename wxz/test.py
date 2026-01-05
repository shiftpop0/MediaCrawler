import datetime

a='1717658128000'
# 转化成年月日时分秒
timestamp_seconds = int(a) / 1000
# 从时间戳创建datetime对象
date_time_obj = datetime.datetime.fromtimestamp(timestamp_seconds)
# 格式化为“年-月-日 时:分:秒”
formatted_string = date_time_obj.strftime('%Y-%m-%d %H:%M:%S')

print(formatted_string)