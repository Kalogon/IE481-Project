import random
import numpy as np

#SET COLORS FOR EACH APPLICATION
def lighter(color, percent):
    color = np.array(color)
    white = np.array([255, 255, 255])
    vector = white-color
    rgb_color = color + vector * (percent/100)
    return 'rgb({}, {}, {})'.format(rgb_color[0], rgb_color[1], rgb_color[2])
def app_colors(df):
    colors = dict()
    for index, row in df.iterrows():
        category = row['Task']
        app_name = row['name']
        if(category == 'SNS'):
            color = [0, 0, 255]
            percent = random.randint(0, 50)
            colors['{}'.format(app_name)] = lighter(color, percent)
        elif(category == 'Multimedia'):
            color = [255, 0, 0]
            percent = random.randint(0, 50)
            colors['{}'.format(app_name)] = lighter(color, percent)
        elif(category == 'Internet'):
            color = [0, 160, 185]
            percent = random.randint(0, 50)
            colors['{}'.format(app_name)] = lighter(color, percent)
        elif(category == 'Games'):
            color = [255, 155, 0]
            percent = random.randint(0, 50)
            colors['{}'.format(app_name)] = lighter(color, percent)
        else:
            color = [20, 20, 20]
            percent = random.randint(0, 50)
            colors['{}'.format(app_name)] = lighter(color, percent)
    return colors