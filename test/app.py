from flask import Flask, request, render_template, redirect, url_for, abort

app = Flask(__name__)
@app.route("/")
def home():
    return "Hello world"

@app.route("/about")
def about():
    return "About page"

@app.route("/user/<username>")
def show_user(username):
    return f"User: {username}"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        return f"Logged in as {username}"
    return '''
        <form method="post">
            Username: <input name="username"><br>
            Password: <input name="password" type="password"><br>
            <input type="submit">
        </form>
        '''
@app.route("/welcome/<user>")
def welcome(user):
        return render_template("index.html", title="Home page", user=user)

@app.route("/admin")
def admin():
    return redirect(url_for("home"))
    
if __name__ == "__main__":
    app.run(debug=True) 