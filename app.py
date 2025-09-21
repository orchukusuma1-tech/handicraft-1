from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "static/images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
    conn.close()

init_db()

# ===== HOME ROUTE =====
@app.route("/")
def home():
    if "role" in session:
        if session["role"] == "seller":
            return redirect(url_for("seller_dashboard"))
        elif session["role"] == "buyer":
            return redirect(url_for("buyer_dashboard"))
    return redirect(url_for("login"))

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
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                      (username, hashed_password, role))
            conn.commit()
            flash("User registered successfully! Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists!", "danger")
        finally:
            conn.close()
    return render_template_string("""
    <h2>Register</h2>
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
    <form method="post">
      Username: <input type="text" name="username" required><br>
      Password: <input type="password" name="password" required><br>
      <button type="submit">Login</button>
    </form>
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
    <a href="{{ url_for('add_product') }}">Add New Product</a> | 
    <a href="{{ url_for('logout') }}">Logout</a>
    <h3>Your Products:</h3>
    <ul>
      {% for p in products %}
      <li>{{ p[1] }} - ₹{{ p[3] }} | <a href="{{ url_for('edit_product', product_id=p[0]) }}">Edit</a></li>
      {% endfor %}
    </ul>
    """, products=products)

@app.route("/seller/add", methods=["GET", "POST"])
def add_product():
    if "role" not in session or session["role"] != "seller":
        return redirect(url_for("login"))
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        price = float(request.form["price"])
        category = request.form["category"]
        image_file = request.files["image"]
        image_filename = None
        if image_file:
            image_filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO products (name, description, price, category, image, owner_id) VALUES (?, ?, ?, ?, ?, ?)",
                  (name, description, price, category, image_filename, session["user_id"]))
        conn.commit()
        conn.close()
        flash("Product added!", "success")
        return redirect(url_for("seller_dashboard"))
    return render_template_string("""
    <h2>Add Product</h2>
    <form method="post" enctype="multipart/form-data">
      Name: <input type="text" name="name" required><br>
      Description: <textarea name="description" required></textarea><br>
      Price: <input type="number" name="price" step="0.01" required><br>
      Category: <input type="text" name="category" required><br>
      Image: <input type="file" name="image"><br>
      <button type="submit">Add Product</button>
    </form>
    """)

@app.route("/seller/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    if "role" not in session or session["role"] != "seller":
        return redirect(url_for("login"))
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id=? AND owner_id=?", (product_id, session["user_id"]))
    product = c.fetchone()
    if not product:
        conn.close()
        flash("Product not found", "danger")
        return redirect(url_for("seller_dashboard"))
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        price = float(request.form["price"])
        category = request.form["category"]
        image_file = request.files["image"]
        image_filename = product[5]
        if image_file:
            image_filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        c.execute("UPDATE products SET name=?, description=?, price=?, category=?, image=? WHERE id=?",
                  (name, description, price, category, image_filename, product_id))
        conn.commit()
        conn.close()
        flash("Product updated!", "success")
        return redirect(url_for("seller_dashboard"))
    conn.close()
    return render_template_string("""
    <h2>Edit Product</h2>
    <form method="post" enctype="multipart/form-data">
      Name: <input type="text" name="name" value="{{ product[1] }}" required><br>
      Description: <textarea name="description">{{ product[2] }}</textarea><br>
      Price: <input type="number" name="price" step="0.01" value="{{ product[3] }}" required><br>
      Category: <input type="text" name="category" value="{{ product[4] }}" required><br>
      Image: <input type="file" name="image"><br>
      <button type="submit">Update Product</button>
    </form>
    """, product=product)

# ===== BUYER DASHBOARD WITH SEARCH AND CART =====
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
        {{ p[1] }} - ₹{{ p[3] }} | Seller: {{ p[7] }} 
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
    c.execute("""SELECT cart.id, p.name, p.price FROM cart 
                 JOIN products p ON cart.product_id=p.id 
                 WHERE cart.buyer_id=?""", (session["user_id"],))
    items = c.fetchall()
    conn.close()
    return render_template_string("""
    <h2>Your Cart</h2>
    <a href="{{ url_for('buyer_dashboard') }}">Back to Products</a> | <a href="{{ url_for('logout') }}">Logout</a>
    <ul>
      {% for item in items %}
      <li>{{ item[1] }} - ₹{{ item[2] }} 
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
    flash("Checkout complete!", "success")
    return redirect(url_for("buyer_dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
