from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Sample product data
products = [
    {"name": "Handmade Vase", "description": "Beautiful ceramic vase", "cellular": "12345", "category": "Decor"},
    {"name": "Wicker Basket", "description": "Durable handwoven basket", "cellular": "67890", "category": "Storage"},
    {"name": "Clay Lamp", "description": "Eco-friendly clay lamp", "cellular": "11223", "category": "Lighting"},
    {"name": "Wooden Bowl", "description": "Polished wooden bowl", "cellular": "44556", "category": "Kitchenware"},
]

# Simple HTML templates using render_template_string for testing
login_template = """
<!doctype html>
<title>Login</title>
<h1>Login</h1>
<form method="post">
    Username: <input name="username"><br>
    Role: 
    <select name="role">
        <option value="buyer">Buyer</option>
        <option value="seller">Seller</option>
    </select><br>
    <input type="submit" value="Login">
</form>
"""

register_template = """
<!doctype html>
<title>Register</title>
<h1>Register</h1>
<form method="post">
    Username: <input name="username"><br>
    Role: 
    <select name="role">
        <option value="buyer">Buyer</option>
        <option value="seller">Seller</option>
    </select><br>
    <input type="submit" value="Register">
</form>
"""

dashboard_template = """
<!doctype html>
<title>{{ role.capitalize() }} Dashboard</title>
<h1>Welcome {{ username }} ({{ role }})</h1>
<a href="{{ url_for('logout') }}">Logout</a>
<h2>Products</h2>
<form method="get" action="{{ url_for('search') }}">
    <input type="text" name="query" placeholder="Search products">
    <input type="submit" value="Search">
</form>
<ul>
{% for product in products %}
    <li><b>{{ product.name }}</b>: {{ product.description }} (Cell: {{ product.cellular }})</li>
{% endfor %}
</ul>
"""

search_template = """
<!doctype html>
<title>Search Results</title>
<h1>Search Results for "{{ query }}"</h1>
<a href="{{ url_for('home') }}">Back</a>
<ul>
{% for product in results %}
    <li><b>{{ product.name }}</b>: {{ product.description }} (Cell: {{ product.cellular }})</li>
{% endfor %}
{% if results|length == 0 %}
    <li>No products found.</li>
{% endif %}
</ul>
"""

# Root route redirects based on login status
@app.route("/")
def home():
    if "username" in session:
        if session.get("role") == "buyer":
            return redirect(url_for("buyer_dashboard"))
        elif session.get("role") == "seller":
            return redirect(url_for("seller_dashboard"))
    return redirect(url_for("login"))

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["username"] = request.form["username"]
        session["role"] = request.form["role"]
        return redirect(url_for("home"))
    return render_template_string(login_template)

# Register route
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # In a real app, save user to database
        session["username"] = request.form["username"]
        session["role"] = request.form["role"]
        return redirect(url_for("home"))
    return render_template_string(register_template)

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# Buyer dashboard
@app.route("/buyer")
def buyer_dashboard():
    if session.get("role") != "buyer":
        return redirect(url_for("login"))
    return render_template_string(dashboard_template, username=session["username"], role="buyer", products=products)

# Seller dashboard
@app.route("/seller")
def seller_dashboard():
    if session.get("role") != "seller":
        return redirect(url_for("login"))
    return render_template_string(dashboard_template, username=session["username"], role="seller", products=products)

# Search route
@app.route("/search")
def search():
    query = request.args.get("query", "").lower()
    results = [p for p in products if query in p["name"].lower() or query in p["description"].lower()]
    return render_template_string(search_template, query=query, results=results)

if __name__ == "__main__":
    app.run(debug=True)

