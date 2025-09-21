from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# Sample product data
products = [
    {"id": 1, "name": "Handmade Vase", "category": "Vases", "price": 500, "description": "Beautiful ceramic vase", "owner": "Alice", "manager": "Bob", "image": "vase.png"},
    {"id": 2, "name": "Woven Basket", "category": "Baskets", "price": 300, "description": "Eco-friendly basket", "owner": "Charlie", "manager": "Diana", "image": "basket.png"},
    {"id": 3, "name": "Clay Pot", "category": "Pots", "price": 400, "description": "Traditional clay pot", "owner": "Eve", "manager": "Frank", "image": "pot.png"}
]

cart = []

# CSS (used in all pages)
base_css = """
<style>
body { font-family: 'Arial', sans-serif; background: linear-gradient(to right, #ffe0f0, #fff0e0); color: #333; margin:0; padding:0 2rem;}
header, footer { text-align:center; padding:1rem 0; }
nav a { margin:0 1rem; text-decoration:none; color:#ff4081; font-weight:bold; }
nav a:hover { text-decoration:underline; }
h1 { color:#ff4081; }
.product-grid { display:flex; flex-wrap:wrap; gap:2rem; justify-content:center; margin-top:1rem; }
.product-card { background:#fff0f5; border-radius:15px; padding:1rem; width:250px; text-align:center; box-shadow:0 5px 15px rgba(0,0,0,0.1);}
.product-card img { max-width:100%; border-radius:10px; }
.cart-item { background:#fff0f5; border-radius:10px; padding:1rem; margin-bottom:1rem; box-shadow:0 3px 10px rgba(0,0,0,0.1); }
form { margin-bottom:1rem; text-align:center; }
input, select { padding:0.5rem; margin:0.2rem; }
button { padding:0.5rem 1rem; background:#ff4081; color:white; border:none; border-radius:5px; cursor:pointer; }
button:hover { opacity:0.8; }
</style>
"""

# Home page
@app.route("/")
def home():
    home_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Handicrafts Store</title>
{base_css}
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
<h2>Discover Authentic Handmade Products</h2>
<p>Browse our collection of eco-friendly and traditional handicrafts.</p>
</main>
<footer>
<hr>
<p>🌸 Supporting Rural Artisans | All rights reserved 2025</p>
</footer>
</body>
</html>
"""
    return render_template_string(home_html)

# Products page with search and category filter
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
    
    products_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Handicrafts Store - Products</title>
{base_css}
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
<input type="text" name="search" placeholder="🔍 Search Products" value="{{{{ search_query }}}}">
<select name="category">
{% for cat in categories %}
<option value="{{{{ cat }}}}" {% if cat==selected_category %}selected{% endif %}>{{{{ cat }}}}</option>
{% endfor %}
</select>
<button type="submit">Filter</button>
</form>
<div class="product-grid">
{% for p in products %}
<div class="product-card">
<img src="{{{{ url_for('static', filename='images/' + p['image']) }}}}" alt="{{{{ p['name'] }}}}">
<h3>{{{{ p['name'] }}}}</h3>
<p>{{{{ p['description'] }}}}</p>
<p>💰 Price: ₹{{{{ p['price'] }}}}</p>
<p>Owner: {{{{ p['owner'] }}}} | Manager: {{{{ p['manager'] }}}}</p>
<a href="/add_to_cart/{{{{ p['id'] }}}}">Add to Cart 🛒</a>
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
    return render_template_string(products_html, products=filtered, categories=categories, selected_category=selected_category, search_query=search_query)

# Add to cart
@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    for p in products:
        if p["id"] == product_id:
            cart.append(p)
            break
    return redirect(url_for("show_cart"))

# Cart page
@app.route("/cart")
def show_cart():
    cart_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Handicrafts Store - Cart</title>
{base_css}
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
<h2>Your Cart</h2>
{% if cart %}
{% for item in cart %}
<div class="cart-item">
<h3>{{{{ item['name'] }}}}</h3>
<p>Price: ₹{{{{ item['price'] }}}}</p>
<p>{{{{ item['description'] }}}}</p>
</div>
{% endfor %}
<p><strong>Total: ₹{{{{ total }}}}</strong></p>
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
    total = sum(item["price"] for item in cart)
    return render_template_string(cart_html, cart=cart, total=total)

# About page
@app.route("/about")
def about():
    about_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Handicrafts Store - About</title>
{base_css}
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
<h2>About Us</h2>
<p>We support rural artisans and bring their handmade crafts directly to your home.</p>
</main>
<footer>
<hr>
<p>🌸 Supporting Rural Artisans | All rights reserved 2025</p>
</footer>
</body>
</html>
"""
    return render_template_string(about_html)

if __name__ == "__main__":
    app.run(debug=True)

