# services/market_place/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.database import get_db_connection
from auth.decorators import login_required

market_bp = Blueprint(
    "market_place",
    __name__,
    url_prefix="/market_place",
    template_folder="templates"
)

# ==================================================
# PUBLIC PAGES (UNCHANGED)
# ==================================================

@market_bp.route("/")
def home():
    conn = get_db_connection()
    products = conn.execute(
        "SELECT * FROM products WHERE is_active = 1 ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return render_template("mp_home.html", products=products)


@market_bp.route("/services")
def services():
    return render_template("mp_services.html")


@market_bp.route("/portfolio")
def portfolio():
    return render_template("mp_portfolio.html")


@market_bp.route("/process")
def process():
    return render_template("mp_process.html")


@market_bp.route("/contact")
def contact():
    return render_template("mp_contact.html")


# ==================================================
# PRODUCT DETAILS (PUBLIC)
# ==================================================

@market_bp.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_detail(product_id):
    conn = get_db_connection()

    product = conn.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    if not product:
        conn.close()
        abort(404)

    # 🔹 HANDLE FORM SUBMISSION
    if request.method == 'POST':
        message = request.form.get('message')

        # Option A: email admin (future)
        # Option B: save inquiry (recommended)

        conn.execute("""
            INSERT INTO product_inquiries (product_id, message)
            VALUES (?, ?)
        """, (product_id, message))

        conn.commit()
        conn.close()

        flash("Your inquiry has been sent. We will contact you shortly.", "success")
        return redirect(url_for('market_place.product_detail', product_id=product_id))

    conn.close()
    return render_template(
        'mp_product_detail.html',
        product=product
    )


# ==================================================
# PRODUCT INQUIRY (PUBLIC / CLIENT)
# ==================================================

@market_bp.route("/product/<int:product_id>/inquire", methods=["POST"])
def inquire_product(product_id):
    name = request.form.get("name")
    email = request.form.get("email")
    message = request.form.get("message")
    user_id = session.get("user_id")

    if not message:
        flash("Message is required.", "error")
        return redirect(url_for("market_place.product_detail", product_id=product_id))

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO product_inquiries (product_id, user_id, name, email, message)
        VALUES (?, ?, ?, ?, ?)
    """, (product_id, user_id, name, email, message))
    conn.commit()
    conn.close()

    flash("Your inquiry has been sent. We will contact you shortly.", "success")
    return redirect(url_for("market_place.product_detail", product_id=product_id))


# ==================================================
# ADMIN: ADD PRODUCT
# ==================================================

@market_bp.route("/admin/add", methods=["GET", "POST"])
@login_required
def add_product():
    if session.get("role") != "admin":
        flash("Unauthorized access.", "error")
        return redirect(url_for("market_place.home"))

    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        price = request.form.get("price")
        image = request.form.get("image")  # filename or URL
        created_by = session.get("user_id")

        if not name or not price or not description:
            flash("Name, price and description are required.", "error")
            return redirect(request.url)

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO products (name, description, price, image, created_by)
            VALUES (?, ?, ?, ?, ?)
        """, (name, description, price, image, created_by))
        conn.commit()
        conn.close()

        flash("Product added successfully.", "success")
        return redirect(url_for("market_place.home"))

    return render_template("admin_add_product.html")


# ==================================================
# ADMIN: MANAGE PRODUCTS
# ==================================================

@market_bp.route("/admin/products")
@login_required
def admin_products():
    if session.get("role") != "admin":
        flash("Unauthorized access.", "error")
        return redirect(url_for("market_place.home"))

    conn = get_db_connection()
    products = conn.execute(
        "SELECT * FROM products ORDER BY created_at DESC"
    ).fetchall()
    conn.close()

    return render_template("admin_products.html", products=products)


@market_bp.route("/admin/product/<int:product_id>/toggle")
@login_required
def toggle_product(product_id):
    if session.get("role") != "admin":
        flash("Unauthorized access.", "error")
        return redirect(url_for("market_place.home"))

    conn = get_db_connection()
    conn.execute("""
        UPDATE products
        SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END
        WHERE id = ?
    """, (product_id,))
    conn.commit()
    conn.close()

    flash("Product visibility updated.", "success")
    return redirect(url_for("market_place.admin_products"))
