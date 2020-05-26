from sqlite3 import dbapi2 as sqlite3

from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash
from werkzeug.security import generate_password_hash, check_password_hash

import plotly
import plotly.graph_objs as go
import plotly.figure_factory as ff

from create_database import init_db
import json
from data_processing import bar_data, line_data, gantt_data, fileName
import colors

app = Flask(__name__)
app.secret_key = "ie481-programming code"


def connect_db():
    """Returns a new connection to the database."""
    return sqlite3.connect('userdb')


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
        return redirect(url_for('login'))
    return render_template('homePage.html', username=g.user['username'])


@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('home'))
    error = None
    if request.method == 'POST':
        user = query_db('''select * from user where
            username = ?''', [request.form['username']], one=True)
        if user is None:
            error = 'Invalid username'
        elif not check_password_hash(user['pw_hash'],
                                     request.form['password']):
            error = 'Invalid password'
        else:
            flash('You were logged in')
            session['user_id'] = user['user_id']
            return redirect(url_for('home'))
    return render_template('loginPage.html', error=error)


@app.route('/logout', methods=['POST'])
def logout():
    """Logs the user out."""
    flash('You were logged out')
    session.pop('user_id', None)
    return redirect(url_for('login'))


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
            return redirect(url_for('register'))
    return render_template('registerPage.html', error = error)


def create_bar_plot():
    df_bar = bar_data(fileName)
    appColors = colors.app_colors(df_bar)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=["Other", "Games", "Internet", "Multimedia", "SNS"],
        x=[0, 0, 0, 0, 0],
        orientation='h'
    ))
    for index, row in df_bar.iterrows():
        fig.add_trace(go.Bar(
            y=[row['Task']],
            x=[row['timeSpent_min']],
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
        template='plotly_white',
        autosize=True,
        width=1000,
        height=400,
        barmode="stack",
        showlegend=False,
        hovermode='y unified',
        xaxis_title="Usage Time (min)",
        yaxis_title="Application Categories"
    )
    graphJSON_b = json.dumps(fig.to_plotly_json())
    return graphJSON_b


def create_line_plot():
    df_line_60T = line_data(fileName)

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_line_60T['Start'],
        y=df_line_60T['timeSpent_min'],
        mode='lines',
        line=dict(
            color='#111111',
            width=4
        ))
    )
    for index, row in df_line_60T.iterrows():
        fig2.add_trace(go.Bar(
            x=[row['Start']],
            y=[row['timeSpent_min']],
            hovertext=[row['Description']],
            marker=dict(
                color='green',
                line_color='rgb(150,150,150)',
                line_width=1.5,
                opacity=0.2
            ))
        )
    fig2.update_layout(
        template='plotly_white',
        showlegend=False,
        title='Usage Time',
        hovermode='x unified',
        width=600,
        height=400,
        xaxis_title='Time of Day',
        yaxis_title='Usage Time (min)'
    )
    graphJSON_l = json.dumps(fig2.to_plotly_json(), default=str)
    return graphJSON_l


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
    )

    def add_label(graph, time, text, textcolor, bgcolor):
        graph.add_annotation(
            x='{} {}:00:00'.format(date, time),
            y='4.5',
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
        xaxis=dict(
            autorange=True,
            range=["{} 00:00:00".format(date), "{} 23:59:00".format(date)],
            rangeslider=dict(
                autorange=True,
                range=["{} 00:00:00".format(date), "{} 23:59:00".format(date)]
            ),
            type="date"
        ),
        xaxis_title="Time of Day",
        yaxis_title="Application Categories"
    )
    graphJSON_g = json.dumps(fig3.to_plotly_json(), default=str)
    return graphJSON_g


@app.route('/chart', methods=['GET', 'POST'])
def chart():
    feature = request.args['date']
    graphJSON_bar = create_bar_plot()
    graphJSON_line = create_line_plot()
    graphJSON_gantt = create_gantt_plot()
    graphJSON = dict()
    graphJSON["bar"] = graphJSON_bar
    graphJSON["line"] = graphJSON_line
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
    init_db()
    app.run(port=5050, debug=True)
