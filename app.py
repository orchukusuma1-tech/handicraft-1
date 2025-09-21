from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB = "handicraft.db"

# ===== DATABASE SETUP =====
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )''')
    # Products table
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        price REAL,
        category TEXT,
        image TEXT,
        owner_id INTEGER,
        FOREIGN KEY(owner_id) REFERENCES users(id)
    )''')
    # Cart table
    c.execute('''CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        buyer_id INTEGER,
        product_id INTEGER,
        FOREIGN KEY(buyer_id) REFERENCES users(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )''')
    conn.commit()

    # Insert default seller and sample products if not exist
    c.execute("SELECT COUNT(*) FROM users WHERE username='seller1'")
    if c.fetchone()[0] == 0:
        hashed_password = generate_password_hash("sellerpass")
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("seller1", hashed_password, "seller"))
        seller_id = c.lastrowid

        sample_products = [
            ("Handmade Vase", "Beautiful ceramic vase.", 499.0, "Decor", "https://via.placeholder.com/150", seller_id),
            ("Woven Basket", "Eco-friendly basket.", 299.0, "Storage", "https://via.placeholder.com/150", seller_id),
            ("Wooden Coaster Set", "Set of 6 coasters.", 199.0, "Home", "https://via.placeholder.com/150", seller_id),
        ]
        c.executemany("INSERT INTO products (name, description, price, category, image, owner_id) VALUES (?, ?, ?, ?, ?, ?)", sample_products)

    conn.commit()
    conn.close()

init_db()

# ===== AUTHENTICATION =====
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]
        hashed_password = generate_password_hash(password)
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_password, role))
            conn.commit()
            flash("User registered successfully! Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists!", "danger")
        finally:
            conn.close()
    return render_template_string("""
    <h2>Register</h2>
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <ul>
          {% for category, message in messages %}
            <li style="color: {% if category=='danger' %}red{% elif category=='success' %}green{% else %}blue{% endif %};">{{ message }}</li>
          {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    <form method="post">
      Username: <input type="text" name="username" required><br>
      Password: <input type="password" name="password" required><br>
      Role: 
      <select name="role">
        <option value="buyer">Buyer</option>
        <option value="seller">Seller</option>
      </select><br>
      <button type="submit">Register</button>
    </form>
    <p>Already have an account? <a href="{{ url_for('login') }}">Login here</a></p>
    """)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT id, password, role FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]
            session["role"] = user[2]
            flash(f"Logged in as {user[2]}", "success")
            return redirect(url_for(f"{user[2]}_dashboard"))
        else:
            flash("Invalid credentials", "danger")
    return render_template_string("""
    <h2>Login</h2>
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <ul>
          {% for category, message in messages %}
            <li style="color: {% if category=='danger' %}red{% elif category=='success' %}green{% else %}blue{% endif %};">{{ message }}</li>
          {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    <form method="post">
      Username: <input type="text" name="username" required><br>
      Password: <input type="password" name="password" required><br>
      <button type="submit">Login</button>
    </form>
    <p>Don't have an account? <a href="{{ url_for('register') }}">Register here</a></p>
    """)

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("login"))

# ===== SELLER DASHBOARD =====
@app.route("/seller")
def seller_dashboard():
    if "role" not in session or session["role"] != "seller":
        return redirect(url_for("login"))
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE owner_id=?", (session["user_id"],))
    products = c.fetchall()
    conn.close()
    return render_template_string("""
    <h2>Seller Dashboard</h2>
    <a href="{{ url_for('logout') }}">Logout</a>
    <h3>Your Products:</h3>
    <ul>
      {% for p in products %}
      <li>{{ p[1] }} - ₹{{ p[3] }}<br>
          <img src="{{ p[5] or 'https://via.placeholder.com/150' }}" width="100"><br>
      </li>
      {% endfor %}
    </ul>
    """, products=products)

# ===== BUYER DASHBOARD =====
@app.route("/buyer", methods=["GET", "POST"])
def buyer_dashboard():
    if "role" not in session or session["role"] != "buyer":
        return redirect(url_for("login"))
    search_query = request.form.get("search") if request.method == "POST" else ""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    if search_query:
        c.execute("SELECT p.*, u.username FROM products p JOIN users u ON p.owner_id=u.id WHERE p.name LIKE ? OR p.category LIKE ?", 
                  (f"%{search_query}%", f"%{search_query}%"))
    else:
        c.execute("SELECT p.*, u.username FROM products p JOIN users u ON p.owner_id=u.id")
    products = c.fetchall()
    conn.close()
    return render_template_string("""
    <h2>Buyer Dashboard</h2>
    <a href="{{ url_for('view_cart') }}">View Cart</a> | <a href="{{ url_for('logout') }}">Logout</a>
    <form method="post">
      Search: <input type="text" name="search" placeholder="Search products">
      <button type="submit">Search</button>
    </form>
    <h3>Available Products:</h3>
    <ul>
      {% for p in products %}
      <li>
        <b>{{ p[1] }}</b> - ₹{{ p[3] }} | Seller: {{ p[7] }} <br>
        <img src="{{ p[5] or 'https://via.placeholder.com/150' }}" width="100"><br>
        <form style="display:inline" method="post" action="{{ url_for('add_to_cart', product_id=p[0]) }}">
          <button type="submit">Add to Cart</button>
        </form>
      </li>
      {% endfor %}
    </ul>
    """, products=products)

@app.route("/buyer/add_to_cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    if "role" not in session or session["role"] != "buyer":
        return redirect(url_for("login"))
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO cart (buyer_id, product_id) VALUES (?, ?)", (session["user_id"], product_id))
    conn.commit()
    conn.close()
    flash("Added to cart!", "success")
    return redirect(url_for("buyer_dashboard"))

@app.route("/buyer/cart")
def view_cart():
    if "role" not in session or session["role"] != "buyer":
        return redirect(url_for("login"))
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""SELECT cart.id, p.name, p.price, p.image FROM cart 
                 JOIN products p ON cart.product_id=p.id 
                 WHERE cart.buyer_id=?""", (session["user_id"],))
    items = c.fetchall()
    conn.close()
    return render_template_string("""
    <h2>Your Cart</h2>
    <a href="{{ url_for('buyer_dashboard') }}">Back to Products</a> | <a href="{{ url_for('logout') }}">Logout</a>
    <ul>
      {% for item in items %}
      <li>
        <b>{{ item[1] }}</b> - ₹{{ item[2] }}<br>
        <img src="{{ item[3] or 'https://via.placeholder.com/150' }}" width="100"><br>
        <a href="{{ url_for('remove_from_cart', cart_id=item[0]) }}">Remove</a>
      </li>
      {% endfor %}
    </ul>
    <form method="post" action="{{ url_for('checkout') }}">
      <button type="submit">Checkout</button>
    </form>
    """, items=items)

@app.route("/buyer/cart/remove/<int:cart_id>")
def remove_from_cart(cart_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM cart WHERE id=?", (cart_id,))
    conn.commit()
    conn.close()
    flash("Removed from cart", "info")
    return redirect(url_for("view_cart"))

@app.route("/buyer/cart/checkout", methods=["POST"])
def checkout():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM cart WHERE buyer_id=?", (session["user_id"],))
    conn.commit()
    conn.close()
    flash("Checkout successful!", "success")
    return redirect(url_for("buyer_dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
