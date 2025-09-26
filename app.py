from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import json, os, threading
from dotenv import load_dotenv

# ---------------- Load Environment Variables ----------------
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")

app = Flask(__name__)
app.secret_key = SECRET_KEY

DATA_FILE = "data.json"
lock = threading.Lock()  # Thread-safe JSON access

# ---------------- Data Handling ----------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": [], "products": [], "orders": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with lock:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

def generate_id(items):
    return max([item["id"] for item in items], default=0) + 1

# ---------------- Authentication ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    data = load_data()
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = next((u for u in data["users"] if u["email"] == email and u.get("password") == password), None)
        if user:
            session["user_email"] = email
            session["role"] = user.get("role", "customer")
            flash(f"Welcome {user.get('name')}!", "success")
            return redirect(url_for("home"))
        flash("Invalid credentials", "error")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("home"))

@app.route("/register", methods=["GET", "POST"])
def register():
    data = load_data()
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")
        if any(u["email"] == email for u in data["users"]):
            flash("Email already registered.", "error")
            return redirect(url_for("register"))
        user = {
            "name": name,
            "email": email,
            "password": password,
            "role": role,
            "cart": [],
            "favorites": []
        }
        data["users"].append(user)
        save_data(data)
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

# ---------------- Home / Product Listing ----------------
@app.route("/")
def home():
    data = load_data()
    user_email = session.get("user_email")
    role = session.get("role")
    products_view = []
    for p in data["products"]:
        product_copy = p.copy()
        if role != "owner" or p["owner"]["email"] != user_email:
            product_copy.pop("owner", None)
        products_view.append(product_copy)
    return render_template("index.html", products=products_view)

# ---------------- Add Product (Owner) ----------------
@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    data = load_data()
    user_email = session.get("user_email")
    role = session.get("role")
    if role != "owner":
        flash("Access denied. Only owners can add products.", "error")
        return redirect(url_for("home"))
    
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        price = float(request.form.get("price"))
        rating = float(request.form.get("rating"))
        sensitive_info = request.form.get("sensitive_info")

        product = {
            "id": generate_id(data["products"]),
            "name": name,
            "description": description,
            "price": price,
            "rating": rating,
            "owner": {"email": user_email, "sensitive_info": sensitive_info}
        }
        data["products"].append(product)
        save_data(data)
        flash("Product added successfully!", "success")
        return redirect(url_for("home"))
    
    return render_template("add_product.html")

# ---------------- Cart & Favorites ----------------
@app.route("/cart")
def cart():
    data = load_data()
    user_email = session.get("user_email")
    user = next((u for u in data["users"] if u["email"] == user_email), None)
    cart_items = [p for p in data["products"] if p["id"] in user.get("cart", [])]
    return render_template("cart.html", cart=cart_items)

@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    data = load_data()
    user_email = session.get("user_email")
    user = next((u for u in data["users"] if u["email"] == user_email), None)
    if "cart" not in user:
        user["cart"] = []
    if product_id not in user["cart"]:
        user["cart"].append(product_id)
        save_data(data)
        flash("Added to cart!", "success")
    return redirect(url_for("home"))

@app.route("/place_order")
def place_order():
    data = load_data()
    user_email = session.get("user_email")
    user = next((u for u in data["users"] if u["email"] == user_email), None)
    for pid in user.get("cart", []):
        order = {"id": generate_id(data["orders"]), "product_id": pid, "customer": {"name": user.get("name"), "email": user_email}}
        data["orders"].append(order)
    user["cart"] = []
    save_data(data)
    flash("Order placed successfully!", "success")
    return redirect(url_for("home"))

@app.route("/favorites")
def favorites():
    data = load_data()
    user_email = session.get("user_email")
    user = next((u for u in data["users"] if u["email"] == user_email), None)
    favorite_items = [p for p in data["products"] if p["id"] in user.get("favorites", [])]
    return render_template("favorites.html", favorites=favorite_items)

@app.route("/add_to_favorites/<int:product_id>")
def add_to_favorites(product_id):
    data = load_data()
    user_email = session.get("user_email")
    user = next((u for u in data["users"] if u["email"] == user_email), None)
    if "favorites" not in user:
        user["favorites"] = []
    if product_id not in user["favorites"]:
        user["favorites"].append(product_id)
        save_data(data)
        flash("Added to favorites!", "success")
    return redirect(url_for("home"))

# ---------------- Owner & Admin Views ----------------
@app.route("/owner_products")
def owner_products():
    data = load_data()
    user_email = session.get("user_email")
    if session.get("role") != "owner":
        flash("Access denied", "error")
        return redirect(url_for("home"))
    products = [p for p in data["products"] if p["owner"]["email"] == user_email]
    return render_template("owner_products.html", products=products)

@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        flash("Access denied. Admin only.", "error")
        return redirect(url_for("home"))
    data = load_data()
    return render_template("admin.html", users=data["users"], products=data["products"], orders=data["orders"])

# ---------------- Simple AI Chatbot ----------------
@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    if request.method == "POST":
        user_message = request.form.get("message", "")
        # Simple rule-based bot response
        if "hello" in user_message.lower():
            bot_reply = "Hello! How can I help you today?"
        elif "product" in user_message.lower():
            bot_reply = "You can browse products on the home page or ask me for recommendations."
        elif "cart" in user_message.lower():
            bot_reply = "Check your cart in the cart section to see items you added."
        else:
            bot_reply = "I'm just a simple chatbot 🤖. Please try asking about products, cart, or orders."
        return render_template("chatbot.html", user_message=user_message, bot_reply=bot_reply)
    return render_template("chatbot.html")

if __name__ == "__main__":
    app.run(debug=True)
