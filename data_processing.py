# -*- coding: utf-8 -*-
import pandas as pd
import sys
from os import listdir
from os.path import isfile, join
import datetime

#Define categories of applications
# app_unique = df['name'].unique().tolist()
SNS = ['카톡 프리뷰', '카카오톡', 'Messenger', '에브리타임', '메시지']
Multimedia = ['Samsung Music', '음성 녹음', 'SNOW', 'YouTube', '카메라', '한컴오피스 viewer']
Internet = ['Gmail', 'Chrome', '직방', '다방', 'Google Play 서비스', 'Dropsync']
Games = []

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

def time_frame(row):
    d = row['Start'].time()
    six = datetime.datetime.strptime('06:00', '%H:%M').time()
    twelve = datetime.datetime.strptime('12:00', '%H:%M').time()
    seventeen = datetime.datetime.strptime('17:00', '%H:%M').time()
    twenty = datetime.datetime.strptime('20:00', '%H:%M').time()
    if ((six <= d) & (d < twelve)):
        return 'Morning'
    if ((twelve <= d) & (d < seventeen)):
        return 'Afternoon'
    if ((seventeen <= d) & (d < twenty)):
        return 'Evening'
    if (twenty <= d):
        return 'Night (Before Midnight)'
    if (d < six):
        return 'Night (After Midnight)'

def describe(row):
    m, s = divmod(row["timeSpent"], 60)
    h, m = divmod(m, 60)
    if h>0:
        return '{}hr, {}min, {}sec'.format(h,m,s)
    elif m>0:
        return '{}min, {}sec'.format(m,s)
    else:
        return '{}sec'.format(s)

def preprocess(file):
    data = pd.read_csv(join(file))

    data.set_index('timestamp', drop=True, inplace=True)
    data.drop(columns=['packageName', 'isSystemApp', 'isUpdatedSystemApp'], inplace=True)

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
    df["timeSpent"] = df["timeSpent"].apply(lambda x: int(x))

    #Add Description column (for use in Gantt Chart)
    df["Description"] = df.apply(lambda row: ("<b> Usage Time for "+row["name"]+": "+describe(row)+" </b>"), axis=1)

    #Add time_frame column
    df['time_frame'] = df.apply(lambda row: time_frame(row), axis=1)

    #Drop rows where timeSpent is less than 1 second.
    df = df[df.timeSpent > 1]

    return df

def gantt_data(file):
    df = preprocess(file)
    #Gantt Chart DataFrame Extraction
    df_gantt = df.loc[:, ['Task', 'Start', 'Finish', 'name', 'Description', 'time_frame']]
    return df_gantt

def bar_data(file):
    df = preprocess(file)
    #Summation of times spent on each category of application
    df_bar = df.loc[:, ['Task', 'name', 'timeSpent']]
    df_bar['timeSpent'] = df_bar['timeSpent'].astype(int)
    df_bar = df_bar.groupby(['Task', 'name']).sum().reset_index()
    df_bar["Description"] = df_bar.apply(lambda row: ("<b> Usage Time for "+row["name"]+": "+describe(row)+" </b>"), axis=1)
    df_bar["timeSpent_min"] = df_bar.apply(lambda row: row["timeSpent"]/60, axis=1)
    return df_bar

def line_data(file):
    df = preprocess(file)
    #Line Plot DataFrame Extraction
    df_line = df.loc[:, ['Start', 'Finish', 'timeSpent']]
    df_line.set_index('Start', drop=True, inplace=True)
    df_line_60T = df_line.resample('60T').sum().reset_index()
    df_line_60T["Description"] = df_line_60T.apply(lambda row: ("<b> Phone Usage at "+str(row['Start'].time())+": "+describe(row)+" </b>"), axis=1)
    df_line_60T["timeSpent_min"] = df_line_60T.apply(lambda row: row["timeSpent"]/60, axis=1)
    return df_line_60T

fileName = 'AppUsageEventEntity-5572736000.csv'

#df_gantt = gantt_data('AppUsageEventEntity-5572736000.csv')
#print(df_gantt)

#df_bar = bar_data('AppUsageEventEntity-5572736000.csv')
#print(df_bar)

#df_line = line_data('AppUsageEventEntity-5572736000.csv')
#print(df_line)