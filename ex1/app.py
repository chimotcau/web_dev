from flask import Flask, render_template, redirect,request, url_for

app= Flask(__name__)

posts=[
    {"id":1, "title":"First Post", "content":"Welcome to my blog."},
    {"id":2, "title":"Second Post", "content":"Have a great day!"},
]

@app.route("/")
def index():
    return render_template("index.html", posts=posts)


if __name__ == "__main__":
    app.run(debug=True)