from flask import Flask, request, redirect, url_for, session, render_template_string

app = Flask(__name__)
app.secret_key = "handicrafts-secret"

# -------------------------------
# Product Data
# -------------------------------
products = [
    {
        "id": 1,
        "name": "Handmade Bamboo Basket",
        "description": "A strong eco-friendly basket made with love by rural artisans.",
        "price": 299,
        "image": "https://5.imimg.com/data5/SELLER/Default/2024/10/462402160/XY/BE/IB/153079681/handicraft-basket-500x500.png",
        "category": "Basket",
        "owner": "Anitha Handicrafts",
        "manager": "Ravi Kumar"
    },
    {
        "id": 2,
        "name": "Terracotta Vase",
        "description": "Beautifully crafted terracotta vase, perfect for home decor.",
        "price": 599,
        "image": "https://5.imimg.com/data5/SELLER/Default/2023/4/300077453/GH/YS/YL/28816920/terracotta-flower-vase-1000x1000.jpg",
        "category": "Vase",
        "owner": "Sita Pottery Works",
        "manager": "Lakshmi Devi"
    }
]

# -------------------------------
# Base Template
# -------------------------------
base_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Handicrafts Store</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; background: #fdf6f0; }
        header { background: #ff7f50; color: white; padding: 20px; text-align: center; }
        nav { background: #fff3f0; padding: 10px; text-align: center; }
        nav a { margin: 0 10px; padding: 10px 20px; background: #ff7f50; color: white; text-decoration: none; border-radius: 5px; }
        nav a:hover { background: #ff5722; }
        .container { max-width: 1000px; margin: auto; padding: 20px; }
        .product { border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; border-radius: 10px; background: white; display: flex; gap: 15px; }
        .product img { width: 150px; border-radius: 10px; }
        .cart-item { border-bottom: 1px solid #ddd; padding: 10px 0; }
        .cart-total { font-weight: bold; margin-top: 20px; }
    </style>
</head>
<body>
    <header>
        <h1>🛍️ Handicrafts Store</h1>
    </header>
    <nav>
        <a href="{{ url_for('home') }}">Home</a>
        <a href="{{ url_for('show_products') }}">Products</a>
        <a href="{{ url_for('show_cart') }}">Cart</a>
        <a href="{{ url_for('about') }}">About</a>
    </nav>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

# -------------------------------
# Routes
# -------------------------------
@app.route("/")
def home():
    return render_template_string(
        base_html.replace("{% block content %}{% endblock %}", """
            <h2>Discover Authentic Handmade Products</h2>
            <p>Browse our collection of eco-friendly and traditional handicrafts.</p>
        """)
    )

@app.route("/products")
def show_products():
    query = request.args.get("q", "").lower()
    if query:
        filtered = [p for p in products if query in p["name"].lower() or query in p["description"].lower()]
    else:
        filtered = products

    product_html = """
    <h2>Available Products</h2>
    <form method="get">
        <input type="text" name="q" placeholder="🔍 Search Products" value="{{ query }}">
        <button type="submit">Search</button>
    </form>
    """
    if filtered:
        for p in filtered:
            product_html += f"""
            <div class="product">
                <img src="{p['image']}" alt="{p['name']}">
                <div>
                    <h3>{p['name']}</h3>
                    <p>{p['description']}</p>
                    <p>💰 Price: ₹{p['price']}</p>
                    <p>Owner: {p['owner']} | Manager: {p['manager']}</p>
                    <a href="{url_for('add_to_cart', product_id=p['id'])}">Add to Cart 🛒</a>
                </div>
            </div>
            """
    else:
        product_html += "<p>No products found matching your search.</p>"

    return render_template_string(base_html.replace("{% block content %}{% endblock %}", product_html), query=query)

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
    cart_html = "<h2>🛒 Your Cart</h2>"
    if cart:
        for item in cart:
            cart_html += f"""
            <div class="cart-item">
                <strong>{item['name']}</strong> - ₹{item['price']}<br>
                {item['description']}<br>
                Owner: {item['owner']} | Manager: {item['manager']}
            </div>
            """
        cart_html += f"<div class='cart-total'>Total: ₹{total}</div>"
        cart_html += f"<a href='{url_for('checkout')}'>Proceed to Checkout ✅</a>"
    else:
        cart_html += "<p>Your cart is empty.</p>"
    return render_template_string(base_html.replace("{% block content %}{% endblock %}", cart_html))

@app.route("/checkout")
def checkout():
    session["cart"] = []
    session.modified = True
    checkout_html = """
    <h2>🛒 Your Cart</h2>
    <p>✅ Checkout complete! Thank you for supporting local artisans 🙏</p>
    """
    return render_template_string(base_html.replace("{% block content %}{% endblock %}", checkout_html))

@app.route("/about")
def about():
    return render_template_string(
        base_html.replace("{% block content %}{% endblock %}", """
            <h2>About Us</h2>
            <p>🌸 Our mission is to support rural artisans by bringing their handmade crafts online.<br>
            Every purchase directly helps local communities grow and sustain their traditions.</p>
        """)
    )

# -------------------------------
# Run App
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

