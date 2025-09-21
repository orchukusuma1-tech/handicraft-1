# app.py
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "supersecretkey"

# -------------------------------
# Product Data
# -------------------------------
products = [
    {
        "id": 1,
        "name": "Handmade Bamboo Basket",
        "description": "A strong eco-friendly basket made with love by rural artisans.",
        "price": 299,
        "image": "https://i.ibb.co/9pFb2yQ/basket.png",
        "category": "Basket",
        "owner": "Anitha Handicrafts",
        "manager": "Ravi Kumar"
    },
    {
        "id": 2,
        "name": "Terracotta Vase",
        "description": "Beautifully crafted terracotta vase, perfect for home decor.",
        "price": 599,
        "image": "https://i.ibb.co/DG3dGxF/vase.png",
        "category": "Vase",
        "owner": "Sita Pottery Works",
        "manager": "Lakshmi Devi"
    }
]

# -------------------------------
# Templates (All-in-One with artistic and colorful UI)
# -------------------------------
base_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>🌸 Handicrafts Store</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- Bootstrap 5 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #fceabb, #f8b500);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .navbar {
            background: #ff6f91 !important;
        }
        .navbar-brand {
            font-weight: bold;
            font-size: 1.8rem;
            color: #fff !important;
        }
        .nav-link {
            color: #fff !important;
            font-weight: 500;
        }
        .nav-link:hover {
            color: #ffe5e0 !important;
        }
        .card {
            border-radius: 20px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.2);
            transition: transform 0.2s;
        }
        .card:hover {
            transform: translateY(-5px);
        }
        .card img {
            border-radius: 20px 20px 0 0;
            height: 250px;
            object-fit: cover;
        }
        footer {
            background: #ff6f91;
            color: white;
            padding: 20px 0;
            text-align: center;
            font-weight: bold;
        }
        .btn-custom {
            background: linear-gradient(to right, #ff8177, #ff867a, #ff8c7f, #f99185, #cf556c);
            color: white;
            border: none;
        }
        .btn-custom:hover {
            transform: scale(1.05);
            transition: 0.3s;
        }
        input[type="text"], select {
            padding: 8px 12px;
            border-radius: 10px;
            border: none;
            outline: none;
            margin-right: 10px;
        }
        .section-title {
            text-align: center;
            font-weight: bold;
            font-size: 2rem;
            margin-bottom: 20px;
            color: #6a0572;
            text-shadow: 1px 1px 3px #fff;
        }
    </style>
</head>
<body>

<nav class="navbar navbar-expand-lg navbar-dark">
  <div class="container">
    <a class="navbar-brand" href="{{ url_for('home') }}">🌸 Handicrafts Store</a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
        <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav ms-auto">
        <li class="nav-item"><a class="nav-link" href="{{ url_for('home') }}">Home</a></li>
        <li class="nav-item"><a class="nav-link" href="{{ url_for('product_list') }}">Products</a></li>
        <li class="nav-item"><a class="nav-link" href="{{ url_for('cart') }}">Cart</a></li>
        <li class="nav-item"><a class="nav-link" href="{{ url_for('about') }}">About</a></li>
      </ul>
    </div>
  </div>
</nav>

<div class="container my-5">
    {% block content %}{% endblock %}
</div>

<footer>
    &copy; 2025 Handicrafts Store - Supporting Rural Artisans 🌸
</footer>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# -------------------------------
# Home
# -------------------------------
home_template = """
{% extends "base" %}
{% block content %}
<h2 class="section-title">Discover Authentic Handmade Products</h2>
<p class="text-center fs-5">Browse our collection of eco-friendly and traditional handicrafts made with love by rural artisans. 🌸</p>
{% endblock %}
"""

# -------------------------------
# Products
# -------------------------------
products_template = """
{% extends "base" %}
{% block content %}
<h2 class="section-title">Available Products</h2>
<form method="get" class="mb-4 text-center">
    <input type="text" name="search" placeholder="🔍 Search Products" value="{{ search_query }}">
    <select name="category">
        {% for cat in categories %}
            <option value="{{ cat }}" {% if cat == selected_category %}selected{% endif %}>{{ cat }}</option>
        {% endfor %}
    </select>
    <button class="btn btn-custom btn-sm">Filter</button>
</form>

<div class="row">
    {% for product in products %}
    <div class="col-md-6 mb-4">
        <div class="card">
            <img src="{{ product.image }}" class="card-img-top">
            <div class="card-body">
                <h5 class="card-title">{{ product.name }}</h5>
                <p class="card-text">{{ product.description }}</p>
                <p>💰 Price: ₹{{ product.price }}</p>
                <p>Owner: {{ product.owner }} | Manager: {{ product.manager }}</p>
                <a href="{{ url_for('add_to_cart', product_id=product.id) }}" class="btn btn-custom">Add to Cart 🛒</a>
            </div>
        </div>
    </div>
    {% endfor %}
</div>

{% if not products %}
<p class="text-center text-danger fs-5">No products found matching your search. ❌</p>
{% endif %}
{% endblock %}
"""

# -------------------------------
# Cart
# -------------------------------
cart_template = """
{% extends "base" %}
{% block content %}
<h2 class="section-title">🛒 Your Cart</h2>
{% if cart_items %}
<table class="table table-striped table-hover align-middle">
    <thead class="table-dark">
        <tr>
            <th>Product</th>
            <th>Description</th>
            <th>Price (₹)</th>
        </tr>
    </thead>
    <tbody>
    {% for item in cart_items %}
        <tr>
            <td>{{ item.name }}</td>
            <td>{{ item.description }}</td>
            <td>{{ item.price }}</td>
        </tr>
    {% endfor %}
    </tbody>
</table>
<h4 class="text-end">Total: ₹{{ total }}</h4>
<a href="{{ url_for('checkout') }}" class="btn btn-custom float-end">Proceed to Checkout ✅</a>
{% else %}
<p class="text-center fs-5">Your cart is empty. 🛒</p>
{% endif %}
{% endblock %}
"""

# -------------------------------
# Checkout
# -------------------------------
checkout_template = """
{% extends "base" %}
{% block content %}
<h2 class="section-title">Checkout Complete! 🎉</h2>
<p class="text-center fs-5">Thank you for supporting local artisans. 🌸</p>
<a href="{{ url_for('home') }}" class="btn btn-custom d-block mx-auto">Back to Home</a>
{% endblock %}
"""

# -------------------------------
# About
# -------------------------------
about_template = """
{% extends "base" %}
{% block content %}
<h2 class="section-title">About Us</h2>
<p class="fs-5 text-center">
🌸 Our mission is to support rural artisans by bringing their handmade crafts online.  
Every purchase directly helps local communities grow and sustain their traditions.  
</p>
{% endblock %}
"""

# -------------------------------
# Routes
# -------------------------------
@app.route('/')
def home():
    return render_template_string(home_template, base=base_template)

@app.route('/products')
def product_list():
    query = request.args.get("search", "").lower()
    category = request.args.get("category", "All")
    filtered = [
        p for p in products
        if (category == "All" or p["category"] == category) and
           (query in p["name"].lower() or query in p["description"].lower())
    ]
    categories = ["All"] + sorted(list({p["category"] for p in products}))
    return render_template_string(products_template, base=base_template,
                                  products=filtered, categories=categories,
                                  selected_category=category, search_query=query)

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if "cart" not in session:
        session["cart"] = []
    product = next((p for p in products if p["id"] == product_id), None)
    if product:
        session["cart"].append(product)
        session.modified = True
    return redirect(url_for('product_list'))

@app.route('/cart')
def cart():
    cart_items = session.get("cart", [])
    total = sum(item["price"] for item in cart_items)
    return render_template_string(cart_template, base=base_template,
                                  cart_items=cart_items, total=total)

@app.route('/checkout')
def checkout():
    session.pop("cart", None)
    return render_template_string(checkout_template, base=base_template)

@app.route('/about')
def about():
    return render_template_string(about_template, base=base_template)

# -------------------------------
# Run the app
# -------------------------------
if __name__ == '__main__':
    app.run(debug=True)

