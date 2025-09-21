from flask import Flask, request, redirect, url_for, flash, render_template_string
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Sample product data with links
products = [
    {
        "name": "Handmade Vase",
        "description": "Beautifully crafted ceramic vase.",
        "cost": "₹25",
        "manufacturer": "Crafts by Kusuma",
        "image": "https://mumbaisplash.blogspot.com/search/label/vase",
        "link": "https://mumbaisplash.blogspot.com/search/label/vase"
   
    },
    {
        "name": "Woven Basket",
        "description": "Durable and colorful basket for storage.",
        "cost": "₹15",
        "manufacturer": "Village Artisans",
        "image":  "https://www.etsy.com/listing/640732864/antique-farmhouse-basket-split-oak",
        "link":  "https://www.etsy.com/listing/640732864/antique-farmhouse-basket-split-oak"
    }
]

# Base template merged into each page
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
            .product-info a { display:inline-block; margin-top:5px; color:#ff6f61; text-decoration:none; font-weight:bold; }
            .product-info a:hover { text-decoration:underline; }
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
        <a href="{{ url_for('login') }}">Login</a>
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
    return render_template_string(base_html, **context)

# Home page
@app.route('/')
def home():
    search_query = request.args.get('search', '')
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
                <p><span>Cost:</span> {{ product.cost }}</p>
                <p><span>Manufacturer:</span> {{ product.manufacturer }}</p>
                <a href="{{ product.link }}" target="_blank">View Product</a>
            </div>
        </div>
        {% endfor %}
    </div>
    """
    return render_page(home_content, products=filtered_products, search_query=search_query)

# Login page
@app.route('/login', methods=['GET', 'POST'])
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

# Seller page
@app.route('/seller', methods=['GET', 'POST'])
def seller():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        cost = request.form.get('cost')
        manufacturer = request.form.get('manufacturer')
        image = request.form.get('image') or "https://via.placeholder.com/220"
        link = request.form.get('link') or "#"

        if name and cost:
            products.append({
                "name": name,
                "description": description,
                "cost": f"₹{cost.replace('₹','').strip()}",
                "manufacturer": manufacturer,
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
        <input type="text" name="manufacturer" placeholder="Manufacturer">
        <input type="text" name="cost" placeholder="Price in ₹" required>
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
                <p><span>Cost:</span> {{ product.cost }}</p>
                <p><span>Manufacturer:</span> {{ product.manufacturer }}</p>
                <a href="{{ product.link }}" target="_blank">View Product</a>
            </div>
        </div>
        {% endfor %}
    </div>
    """
    return render_page(seller_content, products=products)

if __name__ == '__main__':
    app.run(debug=True)

