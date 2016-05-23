#!/usr/bin/env python
# coding:utf-8
while True:
    #获取系统当前时间,年月日，时分秒
    import datetime
    import time
    #定义用户计划运行的时间
    #用户定义年,格式input_year = "2016,2017"
    input_year = "2016,2017"
    #用户定义单个月，格式input_month = "4"
    #用户定义多个月，格式input_month = "4,5"
    input_month = "4"
    #定义单个日期,input_day = "4"
    #用户定义多个日期,input_day = "4,5"
    input_day = "4"
    #定义单个小时,input_hour ="17"
    #定义多个小时,input_hour = "17,18,19"
    input_hour = "17,18,19"
    #定义1分钟,input_minute ="17"
    #定义多分钟,input_minute = "17,18,19"
    input_minute = "45"
    #定义单周日,input_weekday ="0"
    #定义多周日,input_weekday = "0,1,2,3,4,5,6"#周一至周日，对应数字(0-6)
    #注意！若果定义了周的模式，则年月日定义设置则无效
    input_weekday = "0"
    input_second = "1"
    #获取系统当前的时间戳
    now_year = datetime.datetime.now().year
    now_month = datetime.datetime.now().month
    now_day = datetime.datetime.now().day
    now_hour = datetime.datetime.now().hour
    now_minute = datetime.datetime.now().minute
    now_second = datetime.datetime.now().second
    now_weekday = datetime.datetime.now().weekday()
    #但条件满足用户输入条件，则运行以下语句
    #使用10 in list[10,20,30],这样的逻辑判断来执行，也就是系统当前获取的时间数据在用户设定的范围内，则进行执行
    #如果每天都执行或者每小时固定时间执行，则在天和小时执行模块设置跳过检查，
    #定义用户输入的变量值
    #定义存储时间的列表
    list_year = []
    list_month = []
    list_day = []
    list_hour = []
    list_minute = []
    list_second = []
    list_weekday = []
    #对用户输入的时间值进行处理
    for i in input_year.split(","):
        list_year.append(int(i))
    for i in input_month.split(","):
        list_month.append(int(i))
    for i in input_day.split(","):
        list_day.append(int(i))
    for i in input_hour.split(","):
        list_hour.append(int(i))
    for i in input_minute.split(","):
        list_minute.append(int(i))
    for i in input_second.split(","):
        list_second.append(int(i))
    for i in input_weekday.split(","):
        list_weekday.append(int(i))
    #如果用户设置了按周执行，则代码直接按每周的天数来进行判断，而不会去判断年月日
    if len(list_weekday) > 0:
        if now_weekday in list_weekday:
            print "Run weekday Task:%s",now_weekday
            if now_hour in list_hour:
                print "Run hour Task:%s",now_hour
                if now_minute in list_minute:
                    print "Run minute Task:%s",now_minute
                    if now_second in list_second:
                        print "Run second Task:%s",now_second
                        print "Run main Task:Start:weekday"
                        time.sleep(1)
                    else:
                        time.sleep(1)
                        continue
                else:
                    continue
            else:
                continue 
        else:
            continue
    else:
        if now_year in list_year:
            print "Run year Task:%s",now_year
            if now_month in list_month:
                print "Run month Task:%s",now_month
                if now_day in list_day:
                   print "Run day Task:%s",now_day
                   if now_hour in list_hour:
                       print "Run hour Task:%s",now_hour
                       if now_minute in list_minute:
                           print "Run minute Task:%s",now_minute
                           if now_second in list_second:
                               print "Run second Task:%s",now_second
                               print "Run main Task:Start"
                               time.sleep(1)
                           else:
                               time.sleep(1)
                               continue
                       else:
                           continue
                   else:
                       continue
                else:
                    continue
            else:
                continue
        else:
            continue
