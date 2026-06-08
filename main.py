import sqlite3

from website import create_app
from website.database import connect_db

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)

@app.teardown_appcontext
def close_db(error):
    connect_db.close()
    print ('Database Closed')