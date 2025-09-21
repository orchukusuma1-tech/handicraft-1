from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "supersecretkey"  # For session management

# -------------------------------
# Embedded product data
# -------------------------------
products = [
    {
        "id": 1,
        "name": "Handmade Bamboo Basket",
        "description": "A strong eco-friendly basket made with love by rural artisans.",
        "price": 299,
        "image": "basket.png",
        "category": "Basket",
        "owner": "Anitha Handicrafts",
        "manager": "Ravi Kumar"
    },
    {
        "id": 2,
        "name": "Terracotta Vase",
        "description": "Beautifully crafted terracotta vase, perfect for home decor.",
        "price": 599,
        "image": "vase.png",
        "category": "Vase",
        "owner": "Sita Pottery Works",
        "manager": "Lakshmi Devi"
    }
]

# -------------------------------
# Base template string
# -------------------------------
base_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Handicrafts Store</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(to right, #ffe0f0, #fff0e0);
            color: #333;
            margin: 0;
            padding: 0 2rem;
        }
        header, footer { text-align: center; padding: 1rem 0; }
        nav a {
            margin: 0 1rem;
            text-decoration: none;
            color: #ff4081;
            font-weight: bold;
        }
        nav a:hover { text-decoration: underline; }
        h1 { color: #ff4081; }
        .product-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 2rem;
            justify-content: center;
            margin-top: 1rem;
        }
        .product-card {
            background: #fff0f5;
            border-radius: 15px;
            padding: 1rem;
            width: 250px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .product-card img { max-width: 100%; border-radius: 10px; }
        .cart-item {
            background: #fff0f5;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        }
        form { margin-bottom: 1rem; text-align: center; }
        input, select { padding: 0.5rem; margin: 0.2rem; }
        button { padding: 0.5rem 1rem; background: #ff4081; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { opacity: 0.8; }
    </style>
</head>
<body>
    <header>
        <h1>🛍️ Handicrafts Store</h1>
        <nav>
            <a href="{{ url_for('home') }}">Home</a>
            <a href="{{ url_for('show_products') }}">Products</a>
            <a href="{{ url_for('show_cart') }}">Cart</a>
            <a href="{{ url_for('about') }}">About</a>
        </nav>
        <hr>
    </header>
    
    <main>
        {% block content %}{% endblock %}
    </main>

    <footer>
        <hr>
        <p>🌸 Supporting Rural Artisans | All rights reserved 2025</p>
    </footer>
</body>
</html>
"""

# -------------------------------
# Home template
# -------------------------------
home_template = """
{% extends base %}
{% block content %}
<h2>Discover Authentic Handmade Products</h2>
<p>Browse our collection of eco-friendly and traditional handicrafts.</p>
{% endblock %}
"""

# -------------------------------
# Products template
# -------------------------------
products_template = """
{% extends base %}
{% block content %}
<h2>Available Products</h2>

<form method="get">
    <input type="text" name="search" placeholder="🔍 Search Products" value="{{ search_query }}">
    <select name="category">
        {% for cat in categories %}
            <option value="{{ cat }}" {% if cat == selected_category %}selected{% endif %}>{{ cat }}</option>
        {% endfor %}
    </select>
    <button type="submit">Filter</button>
</form>

<div class="product-grid">
    {% if products %}
        {% for p in products %}
        <div class="product-card">
            <img src="{{ url_for('static', filename='images/' ~ p.image) }}" alt="{{ p.name }}">
            <h3>{{ p.name }}</h3>
            <p>{{ p.description }}</p>
            <p>💰 Price: ₹{{ p.price }}</p>
            <p>Owner: {{ p.owner }} | Manager: {{ p.manager }}</p>
            <a href="{{ url_for('add_to_cart', product_id=p.id) }}">Add to Cart 🛒</a>
        </div>
        {% endfor %}
    {% else %}
        <p>No products found.</p>
    {% endif %}
</div>
{% endblock %}
"""

# -------------------------------
# Cart template
# -------------------------------
cart_template = """
{% extends base %}
{% block content %}
<h2>🛒 Your Cart</h2>
{% if cart %}
    {% for item in cart %}
        <div class="cart-item">
            <img src="{{ url_for('static', filename='images/' ~ item.image) }}" width="150">
            <h3>{{ item.name }}</h3>
            <p>{{ item.description }}</p>
            <p>💰 Price: ₹{{ item.price }}</p>
            <p>Owner: {{ item.owner }} | Manager: {{ item.manager }}</p>
            <hr>
        </div>
    {% endfor %}
    <h3>Total: ₹{{ total }}</h3>
    <a href="{{ url_for('checkout') }}"><button>Proceed to Checkout ✅</button></a>
{% else %}
    <p>Your cart is empty.</p>
{% endif %}
{% endblock %}
"""

# -------------------------------
# Routes
# -------------------------------
@app.route("/")
def home():
    return render_template_string(home_template, base=base_template)

@app.route("/products")
def show_products():
    search_query = request.args.get("search", "").strip().lower()
    selected_category = request.args.get("category", "All")

    filtered = [
        p for p in products
        if (selected_category == "All" or p["category"] == selected_category)
        and (search_query in p["name"].lower() or search_query in p["description"].lower())
    ]

    categories = ["All"] + sorted(list(set([p["category"] for p in products])))
    return render_template_string(products_template, base=base_template, products=filtered,
                                  categories=categories, selected_category=selected_category, search_query=search_query)

@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    if "cart" not in session:
        session["cart"] = []
    product = next((p for p in products if p["id"] == product_id), None)
    if product:
        session["cart"].append(product)
        session.modified = True
    return redirect(url_for("show_cart"))

@app.route("/cart")
def show_cart():
    cart = session.get("cart", [])
    total = sum(item["price"] for item in cart)
    return render_template_string(cart_template, base=base_template, cart=cart, total=total)

@app.route("/checkout")
def checkout():
    session.pop("cart", None)
    return "<h1>✅ Checkout Complete! Thank you for supporting local artisans. 🙏</h1>"

@app.route("/about")
def about():
    return render_template_string(home_template, base=base_template)  # Can create separate about section

# -------------------------------
# Run
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)

