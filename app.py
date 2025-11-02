import os
import json
import uuid
import threading
from datetime import datetime
from decimal import Decimal

# Load .env if present (optional convenience)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# --- Config from env ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tribal_marketplace.db")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
APP_URL = os.getenv("APP_URL", "http://localhost:8501")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# --- Imports for web / db / stripe / streamlit ---
import streamlit as st
from flask import Flask, request, jsonify
import stripe

from sqlalchemy import (create_engine, Column, Integer, String, DateTime,
                        ForeignKey, Text, JSON, Boolean)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import bcrypt

# Initialize Stripe
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

# --- Database setup (SQLAlchemy) ---
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_admin = Column(Boolean, default=False)
    vendor = relationship("Vendor", uselist=False, back_populates="owner")
    addresses = relationship("Address", back_populates="user")

class Vendor(Base):
    __tablename__ = "vendors"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String, ForeignKey("users.id"))
    name = Column(String)
    description = Column(Text)
    status = Column(String, default="PENDING")  # PENDING / APPROVED / REJECTED
    payout_info = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User", back_populates="vendor")
    products = relationship("Product", back_populates="vendor")

class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    vendor_id = Column(String, ForeignKey("vendors.id"))
    title = Column(JSON)    # {'en': 'Bamboo Basket', 'te': '...', 'hi': '...'}
    description = Column(JSON)
    price_cents = Column(Integer, default=0)
    currency = Column(String, default="USD")
    stock = Column(Integer, default=0)
    images = Column(JSON, default=[])  # list of paths/URLs
    created_at = Column(DateTime, default=datetime.utcnow)
    vendor = relationship("Vendor", back_populates="products")

class Address(Base):
    __tablename__ = "addresses"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    line1 = Column(String)
    city = Column(String)
    state = Column(String)
    postal_code = Column(String)
    country = Column(String)
    is_default = Column(Boolean, default=False)
    user = relationship("User", back_populates="addresses")

class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    product_id = Column(String, ForeignKey("products.id"))
    qty = Column(Integer, default=1)

class WishlistItem(Base):
    __tablename__ = "wishlist_items"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    product_id = Column(String, ForeignKey("products.id"))

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=True)
    items = Column(JSON)
    total_cents = Column(Integer)
    currency = Column(String)
    status = Column(String, default="PENDING")  # PENDING / PAID / FULFILLING / SHIPPED / DELIVERED / CANCELLED
    payment_metadata = Column(JSON, nullable=True)
    fulfillment = Column(JSON, nullable=True)
    address = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class Payout(Base):
    __tablename__ = "payouts"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    vendor_id = Column(String, ForeignKey("vendors.id"))
    amount_cents = Column(Integer)
    currency = Column(String)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ------------------------------
# Simple localization dictionary
# ------------------------------
LOCALES = {
    "en": {
        "title": "Tribal Marketplace",
        "login": "Login",
        "signup": "Sign up",
        "logout": "Logout",
        "email": "Email",
        "password": "Password",
        "name": "Name",
        "profile": "Profile",
        "products": "Products",
        "cart": "Cart",
        "wishlist": "Wishlist",
        "add_to_cart": "Add to cart",
        "add_to_wishlist": "Add to wishlist",
        "checkout": "Checkout",
        "address": "Address",
        "add_address": "Add Address",
        "place_order": "Place Order",
        "chat_with_ai": "Chat with assistant",
        "apply_vendor": "Apply to become a vendor",
        "vendor_dashboard": "Vendor Dashboard",
        "admin_panel": "Admin Panel",
    },
    "te": {
        "title": "త్రైబల్ మార్కెట్‌ప్లేస్",
        "login": "లాగిన్",
        "signup": "సైన్ అప్",
        "logout": "లాగౌట్",
        "email": "ఇమెయిల్",
        "password": "పాస్‌వర్డ్",
        "name": "పేరు",
        "profile": "ప్రొఫైల్",
        "products": "ఉత్పత్తులు",
        "cart": "కార్ట్",
        "wishlist": "విష్‌లిస్ట్",
        "add_to_cart": "కార్ట్‌కు జత చేయి",
        "add_to_wishlist": "విష్‌లిస్ట్‌లో జత చేయి",
        "checkout": "చెక్‌ఆవుట్",
        "address": "చిరునామా",
        "add_address": "చిరునామా జత చేయి",
        "place_order": "ఆర్డర్ పెట్టండి",
        "chat_with_ai": "సహాయకుడితో చాట్ చేయి",
        "apply_vendor": "విక్రేతగా దరఖాస్తు చేయండి",
        "vendor_dashboard": "విక్రేత డాష్‌బోర్డు",
        "admin_panel": "అడ్మిన్ ప్యానెల్",
    },
    "hi": {
        "title": "ट्राइबल मार्केटप्लेस",
        "login": "लॉग इन",
        "signup": "साइन अप",
        "logout": "लॉग आउट",
        "email": "ईमेल",
        "password": "पासवर्ड",
        "name": "नाम",
        "profile": "प्रोफ़ाइल",
        "products": "उत्पाद",
        "cart": "कार्ट",
        "wishlist": "विशलिस्ट",
        "add_to_cart": "कार्ट में जोड़ें",
        "add_to_wishlist": "विशलिस्ट में जोड़ें",
        "checkout": "चेकआउट",
        "address": "पता",
        "add_address": "पता जोड़ें",
        "place_order": "ऑर्डर दें",
        "chat_with_ai": "सहायक से चैट करें",
        "apply_vendor": "विक्रेता बनने के लिए आवेदन करें",
        "vendor_dashboard": "विक्रेता डैशबोर्ड",
        "admin_panel": "एडमिन पैनल",
    },
}

# ------------------------------
# Utility helpers
# ------------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False

def to_float(cents: int) -> float:
    return cents / 100.0

# Exchange rates placeholder (USD base). Replace with live API in production
EXCHANGE_RATES = {"USD": 1.0, "INR": 82.0, "EUR": 0.92}

# ------------------------------
# Stripe helpers
# ------------------------------
def create_stripe_checkout_session(items, order_id, currency="USD"):
    """
    items: list of dicts with keys: name, unit_amount (in cents), quantity
    """
    if not STRIPE_SECRET_KEY:
        raise RuntimeError("Missing STRIPE_SECRET_KEY env var.")
    line_items = []
    for it in items:
        line_items.append({
            "price_data": {
                "currency": currency.lower(),
                "product_data": {"name": it["name"]},
                "unit_amount": int(it["unit_amount"])
            },
            "quantity": int(it.get("quantity", 1))
        })
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        metadata={"order_id": order_id},
        success_url=f"{APP_URL}?checkout=success",
        cancel_url=f"{APP_URL}?checkout=cancel"
    )
    return session

# ------------------------------
# Embedded Flask webhook server
# ------------------------------
app = Flask("webhook_server")

@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    if not STRIPE_WEBHOOK_SECRET:
        return jsonify({"error":"STRIPE_WEBHOOK_SECRET not configured"}), 400
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError:
        return jsonify({"error":"Invalid payload"}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({"error":"Invalid signature"}), 400

    db = next(get_db())
    try:
        etype = event["type"]
        data = event["data"]["object"]
        if etype == "checkout.session.completed":
            metadata = data.get("metadata") or {}
            order_id = metadata.get("order_id")
            if order_id:
                order = db.query(Order).filter_by(id=order_id).first()
                if order and order.status != "PAID":
                    order.status = "PAID"
                    order.payment_metadata = dict(data)
                    order.fulfillment = {"status":"QUEUED", "notes":"Ready for vendor fulfillment"}
                    db.add(order)
                    db.commit()
                    # decrement inventory
                    for it in order.items:
                        pid = it.get("product_id")
                        qty = int(it.get("qty",1))
                        if pid:
                            prod = db.query(Product).filter_by(id=pid).first()
                            if prod:
                                prod.stock = max(0, prod.stock - qty)
                                db.add(prod)
                    db.commit()
                    # create payout entry for vendor (example: 90% to vendor)
                    payout_amount = int(order.total_cents * 0.9)
                    payout = Payout(vendor_id=order.vendor_id, amount_cents=payout_amount, currency=order.currency, status="PENDING")
                    db.add(payout)
                    db.commit()
        elif etype == "payment_intent.payment_failed":
            # handle failed payment if needed
            pass
    finally:
        db.close()

    return jsonify({"received": True}), 200

def run_webhook_server():
    # Start Flask in threaded mode on port 5000
    app.run(port=5000, debug=False, use_reloader=False)

# ------------------------------
# Streamlit UI
# ------------------------------
# Start webhook thread when module is run
def start_webhook_thread_once():
    if os.getenv("DISABLE_WEBHOOK_THREAD") == "1":
        return
    if not getattr(start_webhook_thread_once, "started", False):
        thread = threading.Thread(target=run_webhook_server, daemon=True)
        thread.start()
        start_webhook_thread_once.started = True

start_webhook_thread_once()

st.set_page_config(page_title="Tribal Marketplace", layout="wide")

# Session-level defaults
if "locale" not in st.session_state:
    st.session_state["locale"] = "en"
if "page" not in st.session_state:
    st.session_state["page"] = "home"
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "user_is_admin" not in st.session_state:
    st.session_state["user_is_admin"] = False
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

locale = st.session_state["locale"]
strings = LOCALES.get(locale, LOCALES["en"])

# Top bar: language and title
cols = st.columns([1,6,1])
with cols[0]:
    lang = st.selectbox("", options=["en","te","hi"], index=["en","te","hi"].index(locale), format_func=lambda x: {"en":"English","te":"తెలుగు","hi":"हिन्दी"}[x])
    st.session_state["locale"] = lang
    locale = lang
    strings = LOCALES.get(locale, LOCALES["en"])

with cols[1]:
    st.title(strings["title"])

with cols[2]:
    if st.session_state.get("user_id"):
        if st.button(strings["logout"]):
            st.session_state.clear()
            st.experimental_rerun()

# Sidebar: Auth & account actions
with st.sidebar:
    if not st.session_state.get("user_id"):
        st.header("Account")
        tab = st.radio("", ["Login", "Sign up"])
        if tab == "Login":
            email = st.text_input(strings["email"], key="login_email")
            password = st.text_input(strings["password"], type="password", key="login_password")
            if st.button(strings["login"]):
                db = next(get_db())
                user = db.query(User).filter_by(email=email).first()
                if user and verify_password(password, user.password_hash):
                    st.session_state["user_id"] = user.id
                    st.session_state["user_email"] = user.email
                    st.session_state["user_name"] = user.name
                    st.session_state["user_is_admin"] = user.is_admin
                    st.success("Logged in")
                    st.experimental_rerun()
                else:
                    st.error("Invalid credentials")
        else:
            st.subheader(strings["signup"])
            s_name = st.text_input(strings["name"], key="signup_name")
            s_email = st.text_input(strings["email"], key="signup_email")
            s_password = st.text_input(strings["password"], type="password", key="signup_password")
            if st.button(strings["signup"]):
                db = next(get_db())
                if db.query(User).filter_by(email=s_email).first():
                    st.error("Email already registered")
                else:
                    h = hash_password(s_password)
                    user = User(name=s_name, email=s_email, password_hash=h)
                    db.add(user); db.commit()
                    st.success("Account created. Please login.")
    else:
        st.subheader(strings["profile"])
        db = next(get_db())
        user = db.query(User).filter_by(id=st.session_state["user_id"]).first()
        st.write("Logged in as:", user.email)
        new_name = st.text_input(strings["name"], value=user.name)
        if st.button("Update profile"):
            user.name = new_name
            db.add(user); db.commit(); st.success("Profile updated")

    st.write("---")
    st.subheader(strings["cart"])
    if st.session_state.get("user_id"):
        db = next(get_db())
        cart_items = db.query(CartItem).filter_by(user_id=st.session_state["user_id"]).all()
        for it in cart_items:
            prod = db.query(Product).filter_by(id=it.product_id).first()
            if prod:
                st.write(f"{prod.title.get(locale, prod.title.get('en'))} x {it.qty} -> {to_float(prod.price_cents):.2f} {prod.currency}")
        if st.button("Go to checkout"):
            st.session_state["page"] = "checkout"
    else:
        st.write("Login to see cart")

    st.write("---")
    st.subheader(strings["wishlist"])
    if st.session_state.get("user_id"):
        db = next(get_db())
        wishlist = db.query(WishlistItem).filter_by(user_id=st.session_state["user_id"]).all()
        for w in wishlist:
            prod = db.query(Product).filter_by(id=w.product_id).first()
            if prod:
                st.write(prod.title.get(locale, prod.title.get("en")))
    else:
        st.write("Login to see wishlist")

    # Vendor apply
    st.write("---")
    if st.session_state.get("user_id"):
        if st.button(strings["apply_vendor"]):
            st.session_state["page"] = "apply_vendor"
    else:
        st.info("Login to apply as vendor")

    # Admin panel link visible for admin users
    if st.session_state.get("user_is_admin"):
        if st.button(strings["admin_panel"]):
            st.session_state["page"] = "admin"

# --- Main pages ---
page = st.session_state["page"]

if page == "home":
    st.header(strings["products"])
    db = next(get_db())
    products = db.query(Product).all()
    if not products:
        st.info("No products yet")
    cols2 = st.columns(3)
    for idx, p in enumerate(products):
        c = cols2[idx % 3]
        with c:
            st.subheader(p.title.get(locale, p.title.get("en")))
            st.write(p.description.get(locale, p.description.get("en")))
            st.write(f"Price: {to_float(p.price_cents):.2f} {p.currency} | Stock: {p.stock}")
            qty = st.number_input("Qty", min_value=1, max_value=100, value=1, key=f"qty_{p.id}")
            if st.button(strings["add_to_cart"], key=f"cart_{p.id}"):
                if not st.session_state.get("user_id"):
                    st.warning("Please login to add to cart")
                else:
                    db = next(get_db())
                    ci = CartItem(user_id=st.session_state["user_id"], product_id=p.id, qty=qty)
                    db.add(ci); db.commit(); st.success("Added to cart")
            if st.button(strings["add_to_wishlist"], key=f"wish_{p.id}"):
                if not st.session_state.get("user_id"):
                    st.warning("Please login to add to wishlist")
                else:
                    db = next(get_db())
                    wi = WishlistItem(user_id=st.session_state["user_id"], product_id=p.id)
                    db.add(wi); db.commit(); st.success("Added to wishlist")

elif page == "apply_vendor":
    st.header(strings["apply_vendor"])
    if not st.session_state.get("user_id"):
        st.warning("Please login to apply")
    else:
        with st.form("vendor_apply"):
            store_name = st.text_input("Store name")
            store_desc = st.text_area("Short description")
            payout_info = st.text_input("Payout info (bank/UPI/Stripe account id) - optional")
            kyc = st.file_uploader("KYC doc (image/pdf) - optional")
            submitted = st.form_submit_button("Submit application")
            if submitted:
                db = next(get_db())
                me = db.query(User).filter_by(id=st.session_state["user_id"]).first()
                v = Vendor(owner_id=me.id, name=store_name, description=store_desc, payout_info={"raw": payout_info})
                db.add(v); db.commit()
                st.success("Vendor application submitted. Admin will review.")
                st.session_state["page"] = "home"

elif page == "admin":
    st.header("Admin: Vendor Approvals & Orders")
    if not st.session_state.get("user_is_admin"):
        st.warning("Admin access required")
    else:
        db = next(get_db())
        pending = db.query(Vendor).filter_by(status="PENDING").all()
        st.subheader("Pending vendor applications")
        for v in pending:
            owner = db.query(User).filter_by(id=v.owner_id).first()
            st.write(f"Store: {v.name} | Owner: {owner.email} | Desc: {v.description}")
            c1, c2 = st.columns(2)
            if c1.button("Approve", key=f"approve_{v.id}"):
                v.status = "APPROVED"
                db.add(v); db.commit(); st.success("Vendor approved")
            if c2.button("Reject", key=f"reject_{v.id}"):
                v.status = "REJECTED"
                db.add(v); db.commit(); st.info("Vendor rejected")

        st.subheader("Recent orders")
        recent_orders = db.query(Order).order_by(Order.created_at.desc()).limit(20).all()
        for o in recent_orders:
            st.write(f"Order {o.id} | User {o.user_id} | Status: {o.status} | Total: {to_float(o.total_cents)} {o.currency}")

elif page == "vendor_dashboard":
    st.header(strings["vendor_dashboard"])
    if not st.session_state.get("user_id"):
        st.warning("Please login")
    else:
        db = next(get_db())
        me = db.query(User).filter_by(id=st.session_state["user_id"]).first()
        vendor = me.vendor
        if not vendor or vendor.status != "APPROVED":
            st.info("No approved vendor found. Apply and wait for admin approval.")
        else:
            st.subheader("My products")
            for p in vendor.products:
                st.write(f"{p.title.get(locale,'-')} | {to_float(p.price_cents):.2f} {p.currency} | Stock {p.stock}")
                c1, c2 = st.columns(2)
                if c1.button("Edit", key=f"edit_{p.id}"):
                    st.session_state["editing_product"] = p.id
                if c2.button("Delete", key=f"del_{p.id}"):
                    db.delete(p); db.commit(); st.success("Deleted")

            st.subheader("Create product")
            with st.form("create_prod"):
                t_en = st.text_input("Title (EN)")
                t_te = st.text_input("Title (TE)")
                d_en = st.text_area("Desc (EN)")
                price = st.number_input("Price (USD)", value=10.0)
                stock = st.number_input("Stock", value=10)
                submitted = st.form_submit_button("Create")
                if submitted:
                    prod = Product(vendor_id=vendor.id, title={"en":t_en,"te":t_te}, description={"en":d_en}, price_cents=int(price*100), currency="USD", stock=stock)
                    db.add(prod); db.commit(); st.success("Product created")

            st.subheader("Orders for my products")
            my_orders = db.query(Order).filter_by(vendor_id=vendor.id).order_by(Order.created_at.desc()).all()
            for o in my_orders:
                st.write(f"Order {o.id} | Status: {o.status} | Total: {to_float(o.total_cents)} {o.currency}")
                if o.fulfillment and o.fulfillment.get("status") == "QUEUED":
                    if st.button("Mark as shipped", key=f"ship_{o.id}"):
                        o.fulfillment = {"status":"SHIPPED", "tracking": "TBD", "notes": "Shipped by vendor"}
                        o.status = "SHIPPED"
                        db.add(o); db.commit(); st.success("Marked shipped")

elif page == "checkout":
    st.header(strings["checkout"])
    if not st.session_state.get("user_id"):
        st.warning("Please login to checkout")
    else:
        db = next(get_db())
        user = db.query(User).filter_by(id=st.session_state["user_id"]).first()
        cart_items = db.query(CartItem).filter_by(user_id=user.id).all()
        if not cart_items:
            st.info("Cart is empty")
        else:
            st.subheader("Addresses")
            user_addresses = user.addresses
            addr_map = {a.id: f"{a.line1}, {a.city}, {a.state}, {a.postal_code}, {a.country}" for a in user_addresses}
            selected_addr = None
            if addr_map:
                sel = st.selectbox("Select address", options=list(addr_map.keys()), format_func=lambda k: addr_map[k])
                selected_addr = db.query(Address).filter_by(id=sel).first()
            if st.button("Add address"):
                with st.form("add_addr"):
                    line1 = st.text_input("Line1")
                    city = st.text_input("City")
                    state = st.text_input("State")
                    postal = st.text_input("Postal")
                    country = st.text_input("Country")
                    sub = st.form_submit_button("Save")
                    if sub:
                        a = Address(user_id=user.id, line1=line1, city=city, state=state, postal_code=postal, country=country)
                        db.add(a); db.commit(); st.success("Address saved"); st.experimental_rerun()

            # Prepare Stripe line items and order record
            currency = st.selectbox("Pay in currency", options=list(EXCHANGE_RATES.keys()), index=0)
            line_items = []
            total_cents = 0
            vendor_id = None
            for it in cart_items:
                prod = db.query(Product).filter_by(id=it.product_id).first()
                if not prod: continue
                vendor_id = prod.vendor_id
                # convert price to selected currency using EXCHANGE_RATES as simple multiplier
                base_usd = prod.price_cents / 100.0
                rate = EXCHANGE_RATES.get(currency, 1.0)
                unit_amount_cents = int(round(base_usd * rate * 100))
                line_items.append({"name": prod.title.get(locale, prod.title.get("en")), "unit_amount": unit_amount_cents, "quantity": it.qty, "product_id": prod.id})
                total_cents += unit_amount_cents * it.qty

            st.write("Items:")
            for li in line_items:
                st.write(f"{li['name']} x {li['quantity']} -> {li['unit_amount']/100.0:.2f} {currency}")
            st.write("Total:", total_cents/100.0, currency)

            if st.button(strings["place_order"]):
                # create Order record
                order = Order(user_id=user.id, vendor_id=vendor_id, items=[{"product_id":x["product_id"], "qty":x["quantity"], "amount":x["unit_amount"]} for x in line_items], total_cents=total_cents, currency=currency, status="PENDING", address={"raw": addr_map.get(selected_addr.id) if selected_addr else None})
                db.add(order); db.commit()
                try:
                    sess = create_stripe_checkout_session([{"name":x["name"], "unit_amount":x["unit_amount"], "quantity":x["quantity"]} for x in line_items], order_id=order.id, currency=currency)
                    st.info("Redirecting to Stripe Checkout")
                    st.markdown(f"[Proceed to payment]({sess.url})")
                except Exception as e:
                    st.error(f"Stripe error: {e}")

# Chat assistant (basic)
st.write("---")
st.header(strings["chat_with_ai"])
chat_input = st.text_input("Ask about a product, shipping, or the platform", key="chat_input")
if st.button("Send to assistant"):
    if not chat_input:
        st.info("Type a message")
    else:
        st.session_state["chat_history"].append({"role":"user", "content": chat_input})
        if not OPENAI_API_KEY:
            st.session_state["chat_history"].append({"role":"assistant", "content":"(OpenAI key not set) I can explain the app and product details. Enable OPENAI_API_KEY to get AI responses."})
        else:
            try:
                import openai
                openai.api_key = OPENAI_API_KEY
                msgs = [{"role":m["role"], "content":m["content"]} for m in st.session_state["chat_history"]]
                sys = {"role":"system", "content":"You are a helpful marketplace assistant. Answer briefly in the user's locale."}
                res = openai.ChatCompletion.create(model="gpt-4o-mini", messages=[sys]+msgs, temperature=0.7)
                content = res.choices[0].message.content
                st.session_state["chat_history"].append({"role":"assistant", "content": content})
            except Exception as e:
                st.error(f"OpenAI error: {e}")

for m in st.session_state["chat_history"][-10:]:
    if m["role"] == "user":
        st.markdown(f"**You:** {m['content']}")
    else:
        st.markdown(f"**Assistant:** {m['content']}")

st.write("\n---\n")
st.caption("Starter Tribal Marketplace — customize for production: storage, Stripe Connect, HTTPS, and background workers.")
