# -*- coding: utf-8 -*-
import pandas as pd
import sys
from os import listdir
from os.path import isfile, join
import datetime, pprint
from collections import defaultdict

#Define categories of applications
# app_unique = df['name'].unique().tolist()
SNS = ['카톡 프리뷰', '카카오톡', 'Messenger', '에브리타임', '메시지']
Multimedia = ['Samsung Music', '음성 녹음', 'SNOW', 'YouTube', '카메라', '한컴오피스 viewer']
Internet = ['Gmail', 'Chrome', '직방', '다방', 'Google Play 서비스', 'Dropsync']
Games = []
fileName = 'P0701/AppUsageEventEntity-5572736000.csv'
app_fileNames = ['AppUsageEventEntity-5572736000.csv', 'AppUsageEventEntity-5573600000.csv', 'AppUsageEventEntity-5574464000.csv', 'AppUsageEventEntity-5575328000.csv',
                'AppUsageEventEntity-5576192000.csv', 'AppUsageEventEntity-5577056000.csv', 'AppUsageEventEntity-5577920000.csv']


def categorize(row):
    if row['name'] in SNS:
        return 'SNS'
    elif row['name'] in Multimedia:
        return 'Multimedia'
    elif row['name'] in Internet:
        return 'Internet'
    elif row['name'] in Games:
        return 'Games'
    else:
        return 'Other'


def describe(row):
    m, s = divmod(row["timeSpent"], 60)
    h, m = divmod(m, 60)
    if h>0:
        return '{}hr, {}min, {}sec'.format(h,m,s)
    elif m>0:
        return '{}min, {}sec'.format(m,s)
    else:
        return '{}sec'.format(s)


def get_usage_times(file, result):

    data = pd.read_csv(join(file))
    data.set_index('timestamp', drop=True, inplace=True)
    data.drop(columns=['packageName', 'isSystemApp', 'isUpdatedSystemApp'], inplace=True)
    data.dropna(how="any")
    #Convert timestamp to datetime. Create new column for old timestamp
    data['start_time'] = pd.to_datetime(data.index, unit='ms')
    data['start_timestamp'] = data.index

    #Remove all rows except those with types MOVE_TO_FOREGROUND, MOVE_TO_BACKGROUND
    df = data[(data.type=='MOVE_TO_FOREGROUND') | (data.type=='MOVE_TO_BACKGROUND')]

    #Create new columns for when app goes into MOVE_TO_BACKGROUND state.
    df['end_timestamp'] = df['start_timestamp'].shift(-1)
    df['end_time'] = pd.to_datetime(df['end_timestamp'], unit='ms')

    #Get rid of type column.
    df = df.loc[df['type'] == 'MOVE_TO_FOREGROUND']
    df.drop(columns=['type'], inplace=True)

    #Add application category column
    df['category'] = df.apply(lambda row: categorize(row), axis=1)

    #Rename and Rearrange (for use in Gantt Chart)
    df = df.rename(columns={"category": "Task", "start_time": "Start", "end_time": "Finish"})
    # df.set_index('Task', drop=True, inplace=True)

    #Add timeSpent column
    delta = df["Finish"] - df["Start"]
    df["timeSpent"] = delta.dt.seconds
    df.dropna(inplace=True)
    df["timeSpent"] = df["timeSpent"].apply(lambda x: int(x))

    #Drop rows where timeSpent is less than 1 second.
    df = df[df.timeSpent > 60]
    df_sns = df.loc[df["Task"]=='SNS']
    df_multimedia = df.loc[df["Task"] == 'Multimedia']
    df_internet = df.loc[df["Task"] == 'Internet']
    df_games = df.loc[df["Task"] == 'Games']
    df_others = df.loc[df["Task"] == 'Others']

    for i, row in df.iterrows():
        result.append((int(row["start_timestamp"]/1000), int(row["end_timestamp"]/1000), row["timeSpent"]))


# times_result = []
#
# for app_fileName in app_fileNames:
#     file = "P0701/"+app_fileName
#     print(file)
#     get_usage_times(file, times_result)
#
# pprint.pprint(times_result)
# get_usage_times(fileName, [])
# times_dic = get_usage_times(fileName)
# pprint.pprint(times_dic["multimedia"])