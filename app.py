from flask import Flask, render_template, request, redirect, url_for, session, flash
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

    # ===== SAMPLE DATA =====
    # Add sample sellers if not exists
    c.execute("SELECT * FROM users WHERE username='seller1'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  ("seller1", generate_password_hash("password1"), "seller"))
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  ("seller2", generate_password_hash("password2"), "seller"))
    conn.commit()

    # Add sample products if table empty
    c.execute("SELECT * FROM products")
    if not c.fetchall():
        # Get seller ids
        c.execute("SELECT id FROM users WHERE username='seller1'")
        seller1_id = c.fetchone()[0]
        c.execute("SELECT id FROM users WHERE username='seller2'")
        seller2_id = c.fetchone()[0]

        sample_products = [
            ("Handmade Clay Vase", "Beautiful handcrafted clay vase, ideal for home decor.", 499.0, "Decor", "vase.jpg", seller1_id),
            ("Woven Basket", "Sturdy and eco-friendly woven basket, perfect for storage.", 299.0, "Storage", "basket.jpg", seller1_id),
            ("Wooden Key Holder", "Rustic wooden key holder, handmade with care.", 199.0, "Accessories", "keyholder.jpg", seller2_id),
            ("Colorful Wall Hanging", "Vibrant wall hanging made of fabric and beads.", 599.0, "Decor", "wallhang.jpg", seller2_id),
        ]

        for product in sample_products:
            c.execute("INSERT INTO products (name, description, price, category, image, owner_id) VALUES (?, ?, ?, ?, ?, ?)", product)

    conn.commit()
    conn.close()

init_db()

# ===== HOMEPAGE =====
@app.route("/")
def home():
    if "role" in session:
        if session["role"] == "seller":
            return redirect(url_for("seller_dashboard"))
        else:
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
    return render_template("register.html")

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
    return render_template("login.html")

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
    return render_template("seller_dashboard.html", products=products)

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
    return render_template("add_product.html")

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
    return render_template("edit_product.html", product=product)

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
    return render_template("buyer_dashboard.html", products=products)

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
    return render_template("cart.html", items=items)

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

