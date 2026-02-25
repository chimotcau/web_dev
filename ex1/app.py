from flask import Flask, render_template, request, redirect, url_for, abort

app = Flask(__name__)

# In-memory posts list
posts = [
    {"id": 1, "title": "First post", "content": "Welcome to my blog."},
    {"id": 2, "title": "Second post", "content": "Templates + CSS are working!"},
]

@app.route("/")
def home():
    return render_template("index.html", posts=posts)

@app.route("/post/<int:id>")
def post(id):
    for p in posts:
        if p["id"] == id:
            return render_template("post.html", post=p)
    abort(404)

@app.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()

        new_id = posts[-1]["id"] + 1 if posts else 1
        posts.append({"id": new_id, "title": title, "content": content})

        return redirect(url_for("home"))

    return render_template("new.html")

if __name__ == "__main__":
    app.run(debug=True)