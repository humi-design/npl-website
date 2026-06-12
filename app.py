import os 
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pymysql
from urllib.parse import quote_plus
from flask import session
import uuid

pymysql.install_as_MySQLdb()

app = Flask(__name__)

# ======================
# MYSQL CONFIG
# ======================

DB_USER = "humijxhw_nirmal_web"
DB_PASS = quote_plus("Ralpana@1808")
DB_NAME = "humijxhw_nirmal_web"
DB_HOST = "localhost"

app.config["SQLALCHEMY_DATABASE_URI"] = \
f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ======================
# MODELS
# ======================

class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50))
    name = db.Column(db.String(200))
    category = db.Column(db.String(100))
    material = db.Column(db.String(100))
    size = db.Column(db.String(100))
    standard = db.Column(db.String(100))
    image = db.Column(db.String(500))


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100))   # ✅ ADD THIS
    product_id = db.Column(db.Integer)
    qty = db.Column(db.Integer)


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))


class Quote(db.Model):
    __tablename__ = "quotes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    company = db.Column(db.String(200))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    country = db.Column(db.String(100))
    message = db.Column(db.Text)


class Contact(db.Model):
    __tablename__ = "contacts"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    company = db.Column(db.String(200))
    country = db.Column(db.String(100))
    message = db.Column(db.Text)


class Compare(db.Model):
    __tablename__ = "compare"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer)


class Country(db.Model):
    __tablename__ = "countries"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))


class ExportStat(db.Model):
    __tablename__ = "export_stats"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    value = db.Column(db.String(50))

class QuoteItem(db.Model):
    __tablename__ = "quote_items"

    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer)
    product_id = db.Column(db.Integer)
    qty = db.Column(db.Integer)

@app.before_request
def create_session():
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
        
@app.context_processor
def global_data():
    return dict(
        categories=Category.query.all(),
        
    )


# ======================
# HOME
# ======================

@app.route("/")
@app.route("/")

@app.route("/")
def home():
    cart = Cart.query.all()

    categories = Category.query.all()

    industries = [
        "Oil & Gas", "Construction", "Automobile", "Railway",
        "Energy", "Infrastructure", "Marine", "Aerospace"
    ]

    # Load all images from static/products
    product_folder = os.path.join(app.static_folder, "img", "products")

    images = [
        img for img in os.listdir(product_folder)
        if img.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif"))
    ]

    images.sort()

    return render_template(
        "index.html",
        cart=cart,
        industries=industries,
        categories=categories,
        images=images
    )


# ======================
# ABOUT (✅ FIX ADDED)
# ======================

@app.route("/about")
def about():
    cart = Cart.query.all()
    return render_template("about.html", cart=cart)


# ======================
# PRODUCTS
# ======================

@app.route("/products")
def products_page():
    category = request.args.get("category")
    search = request.args.get("search")

    query = Product.query

    if category:
        query = query.filter(Product.category == category)

    if search:
        query = query.filter(Product.name.contains(search))

    products = query.all()
    categories = Category.query.all()
    cart = Cart.query.all()

    return render_template(
        "products.html",
        products=products,
        categories=categories,
        cart=cart,
        selected_category=category,
        search_text=search
    )


# ======================
# CART
# ======================

@app.route("/add/<int:id>")
def add_to_cart(id):
    user_id = session.get("user_id")

    existing = Cart.query.filter_by(
        product_id=id,
        session_id=user_id
    ).first()

    if existing:
        existing.qty += 1
    else:
        item = Cart(product_id=id, qty=1, session_id=user_id)
        db.session.add(item)

    db.session.commit()
    return redirect(request.referrer or url_for("products_page"))


@app.route("/cart")
def cart():
    user_id = session.get("user_id")

    cart_items = Cart.query.filter_by(session_id=user_id).all()

    enriched_cart = []

    for item in cart_items:
        product = Product.query.get(item.product_id)
        if product:
            enriched_cart.append({
                "id": item.id,
                "name": product.name,
                "image": product.image,
                "qty": item.qty,
                "spec": product.standard
            })

    return render_template("cart.html", cart=enriched_cart)


from flask import jsonify

@app.route("/remove/<int:id>")
def remove_from_cart(id):
    user_id = session.get("user_id")

    item = Cart.query.filter_by(id=id, session_id=user_id).first()

    if item:
        db.session.delete(item)
        db.session.commit()

    return ("", 204)

    return ("", 204)   # ✅ no redirect
    
    
from flask import jsonify

@app.route("/update_qty/<int:id>/<action>")
def update_qty(id, action):
    user_id = session.get("user_id")

    item = Cart.query.filter_by(id=id, session_id=user_id).first()

    if not item:
        return ("", 404)

    if action == "increase":
        item.qty += 1
    elif action == "decrease":
        item.qty -= 1
        if item.qty <= 0:
            db.session.delete(item)
            db.session.commit()
            return ("deleted", 200)

    db.session.commit()
    return {"qty": item.qty}
    
    
@app.route("/set_qty/<int:id>", methods=["POST"])
def set_qty(id):
    try:
        item = Cart.query.get(id)

        if not item:
            return ("not found", 404)

        qty = int(request.form.get("qty"))

        if qty <= 0:
            db.session.delete(item)
            db.session.commit()
            return ("deleted", 200)

        item.qty = qty
        db.session.commit()

        return {"qty": item.qty}

    except Exception as e:
        print("ERROR:", e)
        return ("error", 500)



# ======================
# COMPARE
# ======================

@app.route("/compare_add/<int:id>")
def compare_add(id):
    if Compare.query.count() >= 4:
        return redirect(url_for("compare"))

    item = Compare(product_id=id)
    db.session.add(item)
    db.session.commit()

    return redirect(url_for("compare"))


@app.route("/compare")
def compare():
    compare_items = Compare.query.all()

    products = []

    for item in compare_items:
        p = Product.query.get(item.product_id)

        if p:
            # ✅ Inject dynamic specs dictionary
            p.specs = {
                "Material": p.material or "—",
                "Size": p.size or "—",
                "Standard": p.standard or "—",
                "Category": p.category or "—"
            }

            # 👉 Optional future-ready fields (safe fallback)
            p.specs["Strength Grade"] = getattr(p, "strength", "—") or "—"
            p.specs["Surface Coating"] = getattr(p, "coating", "—") or "—"

            products.append(p)

    # ✅ Build dynamic spec keys (VERY IMPORTANT)
    spec_keys = set()
    for p in products:
        spec_keys.update(p.specs.keys())

    spec_keys = sorted(spec_keys)

    cart = Cart.query.all()

    return render_template(
        "compare.html",
        compare=products,
        cart=cart,
        spec_keys=spec_keys
    )


@app.route("/remove_compare/<int:id>")
def remove_compare(id):
    item = Compare.query.filter_by(product_id=id).first()

    if item:
        db.session.delete(item)
        db.session.commit()

    return redirect(url_for("compare"))


@app.route("/clear_compare")
def clear_compare():
    Compare.query.delete()
    db.session.commit()
    return redirect(url_for("compare"))
    
    
from flask import request, redirect, url_for, session
from email.mime.text import MIMEText
import smtplib

@app.route("/submit_quote", methods=["POST"])
def submit_quote():
    try:
        # =========================
        # GET FORM DATA
        # =========================
        name = request.form.get("name")
        email = request.form.get("email")
        company = request.form.get("company")
        phone = request.form.get("phone")
        country = request.form.get("country")
        message = request.form.get("message")

        # =========================
        # CREATE QUOTE
        # =========================
        q = Quote(
            name=name,
            email=email,
            company=company,
            phone=phone,
            country=country,
            message=message
        )

        db.session.add(q)
        db.session.commit()   # ⚠️ required to get q.id

        # =========================
        # GET CART ITEMS (SAFE)
        # =========================
        user_id = session.get("user_id")

        cart_items = []
        if user_id:
            cart_items = Cart.query.filter_by(session_id=user_id).all()

        # =========================
        # SAVE CART ITEMS TO QUOTE
        # =========================
        email_items_text = ""

        for item in cart_items:
            qi = QuoteItem(
                quote_id=q.id,
                product_id=item.product_id,
                qty=item.qty
            )
            db.session.add(qi)

            # Build email content
            product = Product.query.get(item.product_id)
            if product:
                email_items_text += f"{product.name} (Qty: {item.qty})\n"

        # =========================
        # CLEAR CART
        # =========================
        if user_id:
            Cart.query.filter_by(session_id=user_id).delete()

        db.session.commit()

        # =========================
        # SEND EMAIL
        # =========================
        full_message = f"""
New RFQ Received

Name: {name}
Email: {email}
Company: {company}
Phone: {phone}
Country: {country}

Items:
{email_items_text}

Message:
{message}
"""

        msg = MIMEText(full_message)
        msg["Subject"] = f"New RFQ from {name}"
        msg["From"] = email
        msg["To"] = "yourcompany@email.com"  # 🔁 change this

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login("yourcompany@email.com", "your_app_password")
            server.send_message(msg)
            server.quit()
        except Exception as mail_error:
            print("EMAIL ERROR:", mail_error)

        # =========================
        # SUCCESS
        # =========================
        return redirect(url_for("cart", success=1))

    except Exception as e:
        print("ERROR:", e)
        return f"Internal Server Error: {e}"

# ======================
# EXPORT
# ======================

@app.route("/export")
def export():
    countries = Country.query.all()
    cart = Cart.query.all()

    # ✅ Hardcoded stats (safe, no DB dependency)
    stats = [
        {"title": "Countries Exported", "value": "80+"},
        {"title": "Years Experience", "value": "25+"},
        {"title": "Global Clients", "value": "2000+"},
        {"title": "Products", "value": "50K+"}
    ]

    return render_template(
        "export.html",
        countries=countries,
        stats=stats,
        cart=cart
    )


# ======================
# CONTACT
# ======================

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        try:
            c = Contact(
                name=request.form["name"],
                email=request.form["email"],
                company=request.form["company"],
                country=request.form["country"],
                message=request.form["message"]
            )
            db.session.add(c)
            db.session.commit()

            flash("Message sent successfully!")
            return redirect(url_for("contact"))

        except Exception as e:
            print(e)
            flash("Error sending message")

    return render_template(
        "contact.html",
        cart=Cart.query.all(),
        categories=Category.query.all(),
        company_address="A-12, Priya Industrial Estate, Behind Mira Bhayandar Sports, Mumbai,401105, India",
        company_phone="+91 8424849942",
        company_email="sales@nirmalprecision.com",
        business_hours="Mon–Sat: 9:00 AM – 6:00 PM IST",
        map_title="Mumbai Manufacturing Unit"
    )
    



# ======================
# ADMIN
# ======================

# ======================
# ADMIN CONFIG
# ======================

from flask import session

app.secret_key = "supersecretkey"


# ======================
# ADMIN LOGIN
# ======================

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if (
            request.form["username"] == ADMIN_USER and
            request.form["password"] == ADMIN_PASS
        ):
            session["admin"] = True
            return redirect(url_for("admin"))

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


# ======================
# ADMIN DASHBOARD
# ======================

@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    return render_template(
        "admin.html",
        products=Product.query.all(),
        categories=Category.query.all(),
        countries=Country.query.all(),
        stats=[]
    )


# ======================
# PRODUCT CRUD
# ======================

@app.route("/admin/add_product", methods=["POST"])
def add_product():
    p = Product(
        code=request.form["code"],
        name=request.form["name"],
        category=request.form["category"],
        material=request.form.get("material"),
        size=request.form.get("size"),
        standard=request.form.get("standard"),
        image=request.form.get("image")
    )
    db.session.add(p)
    db.session.commit()
    return redirect(url_for("admin"))


@app.route("/admin/delete_product/<int:id>")
def delete_product(id):
    p = Product.query.get(id)
    if p:
        db.session.delete(p)
        db.session.commit()
    return redirect(url_for("admin"))


# ======================
# CATEGORY
# ======================

@app.route("/admin/add_category", methods=["POST"])
def add_category():
    db.session.add(Category(name=request.form["name"]))
    db.session.commit()
    return redirect(url_for("admin"))


# ======================
# COUNTRY
# ======================

@app.route("/admin/add_country", methods=["POST"])
def add_country():
    db.session.add(Country(name=request.form["name"]))
    db.session.commit()
    return redirect(url_for("admin"))


# ======================
# EXPORT STATS
# ======================

@app.route("/admin/add_stat", methods=["POST"])
def add_stat():
    db.session.add(
        ExportStat(
            title=request.form["title"],
            value=request.form["value"]
        )
    )
    db.session.commit()
    return redirect(url_for("admin"))
    
@app.route("/admin/update_product/<int:id>", methods=["POST"])
def update_product(id):
    p = Product.query.get(id)

    if p:
        p.code = request.form["code"]
        p.name = request.form["name"]
        p.category = request.form["category"]
        p.material = request.form.get("material")
        p.size = request.form.get("size")
        p.standard = request.form.get("standard")

        db.session.commit()

    return redirect(url_for("admin"))


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")
# ======================

if __name__ == "__main__":
    app.run(debug=True)