from flask import Flask, render_template
import mysql.connector
app = Flask(__name__)

db =  mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "bae,bemywaifu",
    database = "teamforge",
    use_pure=True
)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/test_db")
def test_db():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM test_users")
    users = cursor.fetchall()
    cursor.close()
    return str(users)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)