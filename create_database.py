from sqlite3 import dbapi2 as sqlite3
from hashlib import md5
from contextlib import closing
from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash

app = Flask(__name__)

def connect_db():
    """Returns a new connection to the database."""
    return sqlite3.connect('userdb')


def init_db():
    """Creates the database tables."""
    with closing(connect_db()) as db:
        with app.open_resource('schema/userdb.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


if __name__ == '__main__':
    init_db()
