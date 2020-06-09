from sqlite3 import dbapi2 as sqlite3
from contextlib import closing

from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash
from werkzeug.security import generate_password_hash, check_password_hash

import plotly
import plotly.graph_objs as go
import plotly.figure_factory as ff

from datetime import datetime
import time
from create_database import init_db
import json
from data_processing import bar_data, line_data, gantt_data, fileName, df_freq_app, df_freq_category, df_freq_time, df_most, df_most_app
from appUsage_time_processing import get_usage_times
from esm_processing import preprocess, filter_data
import colors

#DATA EXTRACTION
most_freq_app = df_freq_app['name']
num_freq_app = df_freq_app['Task']

most_freq_category = df_freq_category['Task']
num_freq_category = df_freq_category['name']

most_freq_time = df_freq_time['time_frame']

most_category = df_most['Task']
most_category_min = df_most['timeSpent_min']

most_app = df_most_app['name']
most_app_min = df_most_app['timeSpent_min']

app = Flask(__name__)
app.secret_key = "ie481-programming code"
app_fileNames = ['AppUsageEventEntity-5572736000.csv', 'AppUsageEventEntity-5573600000.csv', 'AppUsageEventEntity-5574464000.csv', 'AppUsageEventEntity-5575328000.csv',
                'AppUsageEventEntity-5576192000.csv', 'AppUsageEventEntity-5577056000.csv', 'AppUsageEventEntity-5577920000.csv']
fileName = 'P0701/AppUsageEventEntity-5572736000.csv'

def connect_db():
    """Returns a new connection to the database."""
    return sqlite3.connect('user.db')


def init_db():
    """Creates the database tables."""
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.before_request
def before_request():
    """Make sure we are connected to the database each request and look
    up the current user so that we know he's there.
    """
    g.db = connect_db()
    g.user = None
    if 'user_id' in session:
        g.user = query_db('select * from user where user_id = ?',
                          [session['user_id']], one=True)


@app.teardown_request
def teardown_request(exception):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'db'):
        g.db.close()


def get_user_id(username):
    """Convenience method to look up the id for a username."""
    rv = g.db.execute('select user_id from user where username = ?',
                       [username]).fetchone()
    return rv[0] if rv else None


def query_db(query, args=(), one=False):
    """Queries the database and returns a list of dictionaries."""
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


@app.route('/')
def home():
    if not g.user:
        return redirect(url_for('default_page'))
    return render_template('homePage.html', username=g.user['username'],
        most_freq_app=most_freq_app,
        num_freq_app=num_freq_app,
        most_freq_category=most_freq_category,
        num_freq_category=num_freq_category,
        most_freq_time=most_freq_time,
        most_category=most_category,
        most_category_min=most_category_min,
        most_app=most_app,
        most_app_min=most_app_min
    )

@app.route('/default')
def default_page():
    """Displays the latest messages of all users."""
    return render_template('default.html')

@app.route('/graphs')
def graphs():
    if not g.user:
        return redirect(url_for('default_page'))
    return render_template('graphs.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('home'))
    error = None
    if request.method == 'POST':
        user = query_db('''select * from user where
            username = ?''', [request.form['username']], one=True)
        if user is None:
            error = 'Invalid Username'
        elif not check_password_hash(user['pw_hash'],
                                     request.form['password']):
            error = 'Invalid Password'
        else:
            session['user_id'] = user['user_id']
            return redirect(url_for('home'))
    return render_template('loginPage.html', error=error)

@app.route('/logout')
def logout():
    """Logs the user out."""
    flash('You were logged out')
    session.pop('user_id', None)
    return redirect(url_for('default_page'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        if not request.form['username']:
            error = 'You have to enter a username'
        elif not request.form['email'] or '@' not in request.form['email']:
            error = 'You have to enter a valid email address'
        elif not request.form['password']:
            error = 'You have to enter a password'
        elif request.form['password'] != request.form['password2']:
            error = 'The two passwords do not match'
        elif get_user_id(request.form['username']) is not None:
            error = 'The username is already taken'
        else:
            g.db.execute('''insert into user (
                username, email, pw_hash) values (?, ?, ?)''',
                [request.form['username'], request.form['email'],
                 generate_password_hash(request.form['password'])])
            g.db.commit()
            flash('You were successfully registered and can login now')
            return redirect(url_for('login'))
    return render_template('registerPage.html', error=error)

def create_bar_plot():
    df_bar = bar_data(fileName)
    appColors = colors.app_colors(df_bar)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=["Other", "Entertainment", "Internet", "Multimedia", "SNS"],
        x=[0, 0, 0, 0, 0],
        orientation='h'
    ))
    for index, row in df_bar.iterrows():
        fig.add_trace(go.Bar(
            y=[row['Task']],
            x=[row['timeSpent_min']/60],
            name=row['name'],
            orientation='h',
            hovertext=[row['Description']],
            marker=dict(
                color=appColors[row['name']],
                line_color=appColors[row['name']],
                line_width=4,
                opacity=0.8
            )
        ))
    fig.update_layout(
        title= "<b>Total Usage: How much do you use each app per day?</b> <br /> (Click on graph to see Application Usage Schedule)",

        template='plotly_white',
        barmode="stack",
        showlegend=False,
        hovermode='y unified',
        xaxis_title="Total Usage Time (hour)",
        yaxis_title="Application Categories",

        autosize=False,
        height=450,
        width=1100,

        margin=dict(l=20,r=20,b=20,t=50)
    )
    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)

    graphJSON_b = json.dumps(fig.to_plotly_json())
    return graphJSON_b

def create_gantt_plot():
    df_gantt = gantt_data(fileName)
    # SET COLORS FOR EACH APPLICATION
    appColors = colors.app_colors(df_gantt)

    # DATE EXTRACTION
    date = df_gantt['Start'].iloc[0].date()

    # CREATE GANTT CHART
    fig3 = ff.create_gantt(
        df_gantt,
        bar_width=0.45,
        colors=appColors,
        index_col='name',
        show_hover_fill=True,
        group_tasks=True,
        showgrid_x=True,
        showgrid_y=True,
        title= "<b>Application Usage Schedule: At what times do you use each app? How often do you use each app? </b> <br /> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; (Click on graph to see Total Usage)"
    )

    def add_label(graph, time, text, textcolor, bgcolor):
        graph.add_annotation(
            x='{} {}:00:00'.format(date, time),
            y='5.5',
            text="{}".format(text),
            showarrow=False,
            font=dict(
                family="Arial, monospace",
                size=12,
                color="{}".format(textcolor)
            ),
            align='center',
            bordercolor="#111111",
            borderwidth=2,
            borderpad=4,
            bgcolor="{}".format(bgcolor),
            opacity=0.8
        )

    add_label(fig3, "02", "Night (After Midnight)", "#ffffff", "rgb(1, 87, 155)")
    add_label(fig3, "08", "Morning", "#111111", "rgb(129, 212, 250)")
    add_label(fig3, "14", "Afternoon", "#111111", "rgb(3, 169, 244)")
    add_label(fig3, "18", "Evening", "#111111", "rgb(2, 136, 209)")
    add_label(fig3, "22", "Night (Before Midnight)", "#ffffff", "rgb(1, 87, 155)")
    fig3.update_layout(
        shapes=[
            dict(
                fillcolor="rgba(1, 87, 155, 0.2)",
                line={"width": 0},
                type="rect",
                x0='{} 00:00:00'.format(date),
                x1='{} 06:00:00'.format(date),
                xref="x",
                y0=0,
                y1=0.95,
                yref="paper"
            ),
            dict(
                fillcolor="rgba(129, 212, 250, 0.2)",
                line={"width": 0},
                type="rect",
                x0='{} 06:00:00'.format(date),
                x1='{} 12:00:00'.format(date),
                xref="x",
                y0=0,
                y1=0.95,
                yref="paper"
            ),
            dict(
                fillcolor="rgba(3, 169, 244, 0.2)",
                line={"width": 0},
                type="rect",
                x0='{} 12:00:00'.format(date),
                x1='{} 17:00:00'.format(date),
                xref="x",
                y0=0,
                y1=0.95,
                yref="paper"
            ),
            dict(
                fillcolor="rgba(2, 136, 209, 0.2)",
                line={"width": 0},
                type="rect",
                x0='{} 17:00:00'.format(date),
                x1='{} 20:00:00'.format(date),
                xref="x",
                y0=0,
                y1=0.95,
                yref="paper"
            ),
            dict(
                fillcolor="rgba(1, 87, 155, 0.2)",
                line={"width": 0},
                type="rect",
                x0='{} 20:00:00'.format(date),
                x1='{} 23:59:00'.format(date),
                xref="x",
                y0=0,
                y1=0.95,
                yref="paper",
            )
        ],
        template='plotly_white',
        xaxis_title="Time of Day",
        yaxis_title="Application Categories",

        autosize=False,
        height=470,
        width=1100,

        margin=dict(l=20,r=20,b=20,t=75)
    )

    graphJSON_g = json.dumps(fig3.to_plotly_json(), default=str)
    return graphJSON_g


def create_esm_plot(feature):
    df_phone_use = []
    df_phone_unuse = []
    categories = ['Valence', 'Attention', 'Stress', 'Disturbance_level']
    (phone_using, phone_unusing) = filter_data(feature, phone_data, not_phone_data)
    for category in categories:
        df_phone_use.append(phone_using[category].mean())
        df_phone_unuse.append(phone_unusing[category].mean())

    fig = go.Figure(data=[
        go.Bar(name='When using phone', x=categories, y=df_phone_use),
        go.Bar(name='When not using phone', x=categories, y=df_phone_unuse)])

    fig.update_layout(
        title= "Self-Diagnosis: How is my phone affecting me psycologically?",
        barmode='group',
        autosize=False,
        height=500,
        width=900,
        yaxis= {'range': [-3,3]},
        margin=dict(l=20, r=20, b=20, t=50, pad=4),
        template='plotly_white',
        font=dict(
            family="Roboto",
            size=20
        ),
    )
    graphJSON_esm = json.dumps(fig.to_plotly_json(), default=str)
    return graphJSON_esm


@app.route('/chart', methods=['GET', 'POST'])
def chart():
    feature = request.args['date']
    graphJSON_bar = create_bar_plot()
    graphJSON_gantt = create_gantt_plot()
    graphJSON_esm = create_esm_plot(feature)
    graphJSON = dict()
    graphJSON["bar"] = graphJSON_bar
    graphJSON["gantt"] = graphJSON_gantt
    graphJSON["esm"] = graphJSON_esm
    return graphJSON


@app.route('/gantt', methods=['GET', 'POST'])
def gantt():
    feature = request.args['date']
    graphJSON_gantt = create_gantt_plot()
    return graphJSON_gantt


@app.route('/bar', methods=['GET', 'POST'])
def bar():
    feature = request.args['date']
    graphJSON_bar = create_bar_plot()
    return graphJSON_bar


if __name__ == '__main__':
    esm_fileName = "esm_data.csv"
    times_result = []
    init_db()
    for app_fileName in app_fileNames:
        file = "P0701/" + app_fileName
        get_usage_times(file, times_result)
    (phone_data, not_phone_data) = preprocess(esm_fileName, times_result)
    print(not_phone_data)
    app.run(port=5050, debug=True)
