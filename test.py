import time
import datetime

now = datetime.datetime.now() # 当前时间

now2 = int(time.mktime(now.timetuple())) # 当前时间的时间戳

threeDayAgo = (datetime.datetime.now() - datetime.timedelta(days = 7)) # 7天前的时间

timeStamp = int(time.mktime(threeDayAgo.timetuple())) # 7天前的时间戳

#注:timedelta()的参数有:days,hours,seconds,microseconds

print now
print now2
print threeDayAgo
print timeStamp

print now2 - timeStamp