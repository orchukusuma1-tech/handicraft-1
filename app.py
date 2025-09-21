from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# Sample Products (Cotton Mat removed)
products = [
    {"id": 1, "name": "Clay Vase", "description": "Handmade clay vase", "price": 500, "category": "Vase", "image": "vase.png", "owner": "Kusuma", "manager": "Orchu"},
    {"id": 2, "name": "Wicker Basket", "description": "Handwoven basket", "price": 300, "category": "Basket", "image": "basket.png", "owner": "Kusuma", "manager": "Orchu"},
    # Add more products as needed
]

cart = []

# Base CSS for all pages
base_css = """
<style>
body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
header, footer { background: #f0f0f0; padding: 10px; text-align: center; }
nav a { margin: 0 10px; text-decoration: none; }
.product-grid { display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; }
.product-card { border: 1px solid #ddd; padding: 10px; width: 250px; text-align: center; }
.product-card img { max-width: 100%; height: auto; }
</style>
"""

# Home page
@app.route("/")
def home():
    home_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <title>Handicrafts Store - Home</title>
    """ + base_css + """
    </head>
    <body>
    <header>
        <h1>🛍️ Handicrafts Store</h1>
        <nav>
            <a href="/">Home</a>
            <a href="/products">Products</a>
            <a href="/cart">Cart</a>
            <a href="/about">About</a>
        </nav>
        <hr>
    </header>
    <main>
        <h2>Welcome to our Handicrafts Store!</h2>
        <p>Discover handmade products by rural artisans.</p>
        <a href="/products">Browse Products 🛒</a>
    </main>
    <footer>
        <hr>
        <p>🌸 Supporting Rural Artisans | All rights reserved 2025</p>
    </footer>
    </body>
    </html>
    """
    return render_template_string(home_html)

# Products page
@app.route("/products")
def show_products():
    search_query = request.args.get("search", "").lower()
    selected_category = request.args.get("category", "All")
    filtered = [
        p for p in products
        if (selected_category=="All" or p["category"]==selected_category)
        and (search_query in p["name"].lower() or search_query in p["description"].lower())
    ]
    categories = ["All"] + sorted(list({p["category"] for p in products}))
    
    products_html = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Handicrafts Store - Products</title>
""" + base_css + """
</head>
<body>
<header>
<h1>🛍️ Handicrafts Store</h1>
<nav>
<a href="/">Home</a>
<a href="/products">Products</a>
<a href="/cart">Cart</a>
<a href="/about">About</a>
</nav>
<hr>
</header>
<main>
<h2>Available Products</h2>
<form method="get">
<input type="text" name="search" placeholder="🔍 Search Products" value="{{ search_query }}">
<select name="category">
{% for cat in categories %}
<option value="{{ cat }}" {% if cat==selected_category %}selected{% endif %}>{{ cat }}</option>
{% endfor %}
</select>
<button type="submit">Filter</button>
</form>
<div class="product-grid">
{% for p in products %}
<div class="product-card">
<img src="{{ url_for('static', filename='images/' + p['image']) }}" alt="{{ p['name'] }}">
<h3>{{ p['name'] }}</h3>
<p>{{ p['description'] }}</p>
<p>💰 Price: ₹{{ p['price'] }}</p>
<p>Owner: {{ p['owner'] }} | Manager: {{ p['manager'] }}</p>
<a href="/add_to_cart/{{ p['id'] }}">Add to Cart 🛒</a>
</div>
{% endfor %}
{% if not products %}
<p>No products found.</p>
{% endif %}
</div>
</main>
<footer>
<hr>
<p>🌸 Supporting Rural Artisans | All rights reserved 2025</p>
</footer>
</body>
</html>
"""
    return render_template_string(products_html, products=filtered, categories=categories,
                                  selected_category=selected_category, search_query=search_query)

# Add to cart
@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    product = next((p for p in products if p["id"]==product_id), None)
    if product and product not in cart:
        cart.append(product)
    return redirect(url_for("show_cart"))

# Cart page
@app.route("/cart")
def show_cart():
    total = sum(p['price'] for p in cart)
    cart_html = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Cart</title>
""" + base_css + """
</head>
<body>
<header>
<h1>🛒 Your Cart</h1>
<nav>
<a href="/">Home</a>
<a href="/products">Products</a>
<a href="/cart">Cart</a>
<a href="/about">About</a>
</nav>
<hr>
</header>
<main>
{% if cart %}
<ul>
{% for p in cart %}
<li>{{ p['name'] }} - ₹{{ p['price'] }}</li>
{% endfor %}
</ul>
<p>Total: ₹{{ total }}</p>
<a href="/checkout">Checkout</a>
{% else %}
<p>Your cart is empty.</p>
{% endif %}
</main>
<footer>
<hr>
<p>🌸 Supporting Rural Artisans | All rights reserved 2025</p>
</footer>
</body>
</html>
"""
    return render_template_string(cart_html, cart=cart, total=total)

# About page
@app.route("/about")
def about():
    about_html = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>About Us</title>
""" + base_css + """
</head>
<body>
<header>
<h1>About Handicrafts Store</h1>
<nav>
<a href="/">Home</a>
<a href="/products">Products</a>
<a href="/cart">Cart</a>
<a href="/about">About</a>
</nav>
<hr>
</header>
<main>
<p>We support rural artisans by providing a platform to sell their handmade products directly to customers.</p>
</main>
<footer>
<hr>
<p>🌸 Supporting Rural Artisans | All rights reserved 2025</p>
</footer>
</body>
</html>
"""
    return render_template_string(about_html)

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
