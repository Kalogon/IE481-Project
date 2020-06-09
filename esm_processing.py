# -*- coding: utf-8 -*-
import pandas as pd
import sys
from os import listdir
from os.path import isfile, join
import pprint, time
from datetime import datetime
import numpy as np
from appUsage_time_processing import get_usage_times
fileName = "esm_data.csv"
app_fileNames = ['AppUsageEventEntity-5572736000.csv', 'AppUsageEventEntity-5573600000.csv', 'AppUsageEventEntity-5574464000.csv', 'AppUsageEventEntity-5575328000.csv',
                'AppUsageEventEntity-5576192000.csv', 'AppUsageEventEntity-5577056000.csv', 'AppUsageEventEntity-5577920000.csv']

category = ["sns", "multimedia", "internet", "games", "others"]





def preprocess(file, times_result):
    def is_phone_using(time):
        for (start, end, interval) in times_result:
            if (start - 60) < time and time < (end + 60):
                return True
        return False

    data = pd.read_csv(join(file))
    df = data[data.UID == 701]
    df.reset_index(drop=True, inplace=True)
    # df.set_index('responseTime_unixtimestamp', drop=True, inplace=True)
    #Convert timestamp to datetime. Create new column for old timestamp
    df["responseTime_unixtimestamp"] = df["responseTime_unixtimestamp"] + 3600*9
    df['responseTime'] = pd.to_datetime(df['responseTime_unixtimestamp'], unit='s')
    # df['responseTime'] = df['responseTime'] + np.timedelta64(9,'h')
    df_bool = []
    for i, row in df.iterrows():
        df_bool.append(is_phone_using(row["responseTime_unixtimestamp"]))
    df_phone = df[df_bool]
    df_bool_reverse = [not i for i in df_bool]

    df_not_phone = df[df_bool_reverse]
    return (df_phone, df_not_phone)


def filter_data(date, p_data, np_data):
    timestamp = time.mktime(datetime.strptime(date, "%Y-%m-%d").timetuple())
    temp = p_data[(timestamp+32400) < p_data["responseTime_unixtimestamp"]]
    filtered_p_data = temp[(timestamp + 118800) > temp["responseTime_unixtimestamp"]]
    temp2 = np_data[(timestamp + 32400) < np_data["responseTime_unixtimestamp"]]
    filtered_np_data = temp2[(timestamp + 118800) > temp2["responseTime_unixtimestamp"]]
    print(filtered_p_data)
    return (filtered_p_data, filtered_np_data)


# for app_fileName in app_fileNames:
#     file = "P0701/"+app_fileName
#     get_usage_times(file, times_result)
# get_usage_times('P0701/AppUsageEventEntity-5572736000.csv', times_result)
# pprint.pprint(times_result)
# print(len(times_result))
# (phone_data, not_phone_data) = preprocess(fileName)
# (phone_using, phone_unusing) = filter_data("2019-05-08", phone_data, not_phone_data)
# phone_using.drop(columns=['UID', 'responseTime_KDT', 'responseTime_unixtimestamp', 'Duration', 'Emotion_change', 'responseTime'], inplace=True)

