import os
from flask import Flask, request, redirect, url_for, flash, render_template_string, session, jsonify
import openai

# ---------------- OpenAI API ----------------
openai.api_key = os.getenv("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")  # set this in environment variables

def ask_gpt(message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": message}],
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# ---------------- Flask App ----------------
app = Flask(__name__)
app.secret_key = os.urandom(24)

# ---------------- Sample product data ----------------
products = [
    {
        "id": 1,
        "name": "Handmade Bamboo Basket",
        "description": "A strong eco-friendly basket made with love by rural artisans.",
        "price": "₹299",
        "image": "https://5.imimg.com/data5/SELLER/Default/2024/10/462402160/XY/BE/IB/153079681/handicraft-basket-500x500.png",
        "owner": "Anitha Handicrafts",
        "manager": "Ravi Kumar",
        "link": "#"
    },
    {
        "id": 2,
        "name": "Terracotta Vase",
        "description": "Beautifully crafted terracotta vase, perfect for home decor.",
        "price": "₹599",
        "image": "https://5.imimg.com/data5/SELLER/Default/2023/4/300077453/GH/YS/YL/28816920/terracotta-flower-vase-1000x1000.jpg",
        "owner": "Sita Pottery Works",
        "manager": "Lakshmi Devi",
        "link": "#"
    }
]

# ---------------- Base Template ----------------
def render_page(content_html, **context):
    base_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Handicraft Market</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Roboto', sans-serif; margin:0; padding:0; background: linear-gradient(120deg, #ffecd2, #fcb69f); }
            header { background-color: #ff6f61; padding: 25px; text-align:center; color:white; font-size:2.5rem; font-weight:bold; text-shadow:2px 2px #333; }
            nav { display:flex; justify-content:center; margin:15px; flex-wrap:wrap; }
            nav a { margin:0 15px; text-decoration:none; color:#333; font-weight:bold; font-size:1.2rem; transition:0.3s; }
            nav a:hover { color:#ff3b2e; }
            .container { max-width:1200px; margin:20px auto; padding:0 20px; }
            .product-grid { display:flex; flex-wrap:wrap; justify-content:space-around; }
            .product-card { 
                background: linear-gradient(145deg, #ffffff, #ffe6e1); 
                border-radius:20px; 
                box-shadow:0 8px 15px rgba(0,0,0,0.2); 
                overflow:hidden; margin:20px; flex:1 1 300px; display:flex; flex-direction:column; transition: transform 0.4s, box-shadow 0.4s;
            }
            .product-card:hover { transform:translateY(-10px); box-shadow:0 15px 25px rgba(0,0,0,0.3); }
            .product-image { height:220px; object-fit:cover; width:100%; }
            .product-info { padding:15px; }
            .product-info h3 { margin:0; color:#ff6f61; }
            .product-info p { margin:5px 0; font-size:1rem; }
            .product-info span { font-weight:bold; }
            .product-info a, .product-info button { display:inline-block; margin-top:5px; color:#fff; background:#ff6f61; border:none; padding:8px 14px; border-radius:8px; text-decoration:none; cursor:pointer; }
            .product-info a:hover, .product-info button:hover { background:#ff3b2e; }
            input[type="text"], input[type="number"], input[type="password"] { padding:10px; margin:5px 0; width:100%; border-radius:8px; border:1px solid #ccc; font-size:1rem; }
            button { background-color:#ff6f61; color:white; border:none; padding:12px 25px; border-radius:12px; cursor:pointer; margin-top:10px; font-size:1rem; transition:0.3s; }
            button:hover { background-color:#ff3b2e; }
            .flash { padding:12px; border-radius:10px; margin:15px 0; font-weight:bold; font-size:1rem; }
            .success { background-color:#d4edda; color:#155724; }
            .danger { background-color:#f8d7da; color:#721c24; }
            form { max-width:500px; margin:auto; }
            @media(max-width:768px) { .product-grid { flex-direction:column; align-items:center; } }
        </style>
    </head>
    <body>
    <header>Handicraft Market</header>
    <nav>
        <a href="{{ url_for('home') }}">Home</a>
        <a href="{{ url_for('seller') }}">Seller</a>
        <a href="{{ url_for('cart') }}">View Cart ({{ cart_count }})</a>
        <a href="{{ url_for('login') }}">Login</a>
        <a href="{{ url_for('chatbot') }}">Chatbot</a>
    </nav>
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        """ + content_html + """
    </div>
    </body>
    </html>
    """
    return render_template_string(base_html, cart_count=sum(item.get('quantity',1) for item in session.get("cart", [])), **context)

# ---------------- Home Page ----------------
@app.route('/')
def home():
    search_query = request.args.get('search','')
    filtered_products = [p for p in products if search_query.lower() in p['name'].lower()]
    home_content = """
    <form method="get" action="{{ url_for('home') }}">
        <input type="text" name="search" placeholder="Search products..." value="{{ search_query }}">
        <button type="submit">Search</button>
    </form>
    <div class="product-grid">
        {% for product in products %}
        <div class="product-card">
            <img src="{{ product.image }}" alt="{{ product.name }}" class="product-image">
            <div class="product-info">
                <h3>{{ product.name }}</h3>
                <p><span>Description:</span> {{ product.description }}</p>
                <p><span>Price:</span> {{ product.price }}</p>
                <p><span>Owner:</span> {{ product.owner }}</p>
                <p><span>Manager:</span> {{ product.manager }}</p>
                <form method="post" action="{{ url_for('add_to_cart', product_id=product.id) }}">
                    <button type="submit">Add to Cart</button>
                </form>
            </div>
        </div>
        {% endfor %}
    </div>
    """
    return render_page(home_content, products=filtered_products, search_query=search_query)

# ---------------- Add to Cart ----------------
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    cart = session.get("cart", [])
    product = next((p for p in products if p["id"] == product_id), None)
    if product:
        existing = next((item for item in cart if item["id"] == product_id), None)
        if existing:
            existing['quantity'] += 1
        else:
            product_copy = product.copy()
            product_copy['quantity'] = 1
            cart.append(product_copy)
        session["cart"] = cart
        flash(f"{product['name']} added to cart!", "success")
    return redirect(url_for("home"))

# ---------------- View Cart ----------------
@app.route('/cart')
def cart():
    cart_items = session.get("cart", [])
    total = sum(int(item['price'].replace("₹",""))*item.get('quantity',1) for item in cart_items)
    recommended = [p for p in products if p not in cart_items]
    cart_content = """
    <h2 style="text-align:center; color:#ff6f61;">Your Cart</h2>
    {% if cart_items %}
    <div class="product-grid">
        {% for product in cart_items %}
        <div class="product-card">
            <img src="{{ product.image }}" alt="{{ product.name }}" class="product-image">
            <div class="product-info">
                <h3>{{ product.name }}</h3>
                <p><span>Price:</span> {{ product.price }}</p>
                <p><span>Quantity:</span> {{ product.quantity }}</p>
                <p><span>Owner:</span> {{ product.owner }}</p>
            </div>
        </div>
        {% endfor %}
    </div>
    <h3>Total: ₹{{ total }}</h3>
    <form method="post" action="{{ url_for('checkout') }}">
        <button type="submit">Proceed to Checkout</button>
    </form>
    <h3 style="text-align:center; color:#ff6f61; margin-top:40px;">You May Also Like</h3>
    <div class="product-grid">
        {% for product in recommended %}
        <div class="product-card">
            <img src="{{ product.image }}" alt="{{ product.name }}" class="product-image">
            <div class="product-info">
                <h3>{{ product.name }}</h3>
                <p><span>Price:</span> {{ product.price }}</p>
                <p><span>Owner:</span> {{ product.owner }}</p>
            </div>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <p style="text-align:center;">Your cart is empty.</p>
    {% endif %}
    """
    return render_page(cart_content, cart_items=cart_items, total=total, recommended=recommended)

# ---------------- Checkout ----------------
@app.route('/checkout', methods=['POST'])
def checkout():
    session["cart"] = []
    flash("Checkout successful! Thank you for shopping 🙏", "success")
    return redirect(url_for("home"))

# ---------------- Login ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    login_content = """
    <h2 style="text-align:center; color:#ff6f61;">Login</h2>
    <form method="post">
        <input type="text" name="username" placeholder="Username" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Login</button>
    </form>
    """
    return render_page(login_content)

# ---------------- Seller ----------------
@app.route('/seller', methods=['GET','POST'])
def seller():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        owner = request.form.get('owner')
        manager = request.form.get('manager')
        image = request.form.get('image') or "https://via.placeholder.com/220"
        link = request.form.get('link') or "#"

        if name and price:
            products.append({
                "id": len(products)+1,
                "name": name,
                "description": description,
                "price": f"₹{price.replace('₹','').strip()}",
                "owner": owner or "Unknown",
                "manager": manager or "Unknown",
                "image": image,
                "link": link
            })
            flash("Product added successfully!", "success")
        else:
            flash("Name and price are required!", "danger")
        return redirect(url_for('seller'))
    seller_content = """
    <h2 style="text-align:center; color:#ff6f61;">Add New Product</h2>
    <form method="post">
        <input type="text" name="name" placeholder="Product Name" required>
        <input type="text" name="description" placeholder="Description">
        <input type="text" name="owner" placeholder="Owner">
        <input type="text" name="manager" placeholder="Manager">
        <input type="text" name="price" placeholder="Price in ₹" required>
        <input type="text" name="image" placeholder="Image URL (optional)">
        <input type="text" name="link" placeholder="Product Link (optional)">
        <button type="submit">Add Product</button>
    </form>
    <h2 style="text-align:center; color:#ff6f61; margin-top:40px;">Existing Products</h2>
    <div class="product-grid">
        {% for product in products %}
        <div class="product-card">
            <img src="{{ product.image }}" alt="{{ product.name }}" class="product-image">
            <div class="product-info">
                <h3>{{ product.name }}</h3>
                <p><span>Description:</span> {{ product.description }}</p>
                <p><span>Price:</span> {{ product.price }}</p>
                <p><span>Owner:</span> {{ product.owner }}</p>
                <p><span>Manager:</span> {{ product.manager }}</p>
            </div>
        </div>
        {% endfor %}
    </div>
    """
    return render_page(seller_content, products=products)

# ---------------- AI Chatbot ----------------
@app.route('/chatbot', methods=['GET','POST'])
def chatbot():
    response = ""
    if request.method == 'POST':
        user_msg = request.form.get('message','')
        if user_msg.strip():
            # Call GPT-4 API
            response = ask_gpt(user_msg)
    chatbot_html = """
    <h2 style="text-align:center; color:#ff6f61;">AI Chatbot 🤖</h2>
    <form method="post">
        <input type="text" name="message" placeholder="Type your message..." required>
        <button type="submit">Send</button>
    </form>
    {% if response %}
    <p style="margin-top:20px; background:#ffe6e1; padding:10px; border-radius:10px;">{{ response }}</p>
    {% endif %}
    """
    return render_page(chatbot_html, response=response)

# ---------------- Search Suggestions API ----------------
@app.route('/search_suggestions')
def search_suggestions():
    query = request.args.get('q','').lower()
    suggestions = [p['name'] for p in products if query in p['name'].lower()][:5]
    return jsonify(suggestions)

# ---------------- Run App ----------------
if __name__ == '__main__':
    app.run(debug=True)
