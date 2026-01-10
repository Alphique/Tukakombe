import os
import time
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, current_app
from werkzeug.utils import secure_filename
from utils.database import get_db_connection
from auth.decorators import login_required

# Blueprint Configuration
market_bp = Blueprint(
    "market_place", 
    __name__, 
    url_prefix="/market_place",
    template_folder="templates" 
)

UPLOAD_FOLDER = os.path.join('static', 'uploads', 'products')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'jfif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_product_images(image_string):
    if not image_string:
        return []
    return [img.strip() for img in image_string.split(',') if img.strip()]

# ==================================================
# PUBLIC PAGES
# ==================================================

@market_bp.route("/")
def home():
    conn = get_db_connection()
    try:
        # Only show products that are marked as active
        products = conn.execute(
            "SELECT * FROM products WHERE is_active = 1 ORDER BY created_at DESC"
        ).fetchall()
    finally:
        conn.close()
    return render_template("mp_home.html", products=products, get_images=get_product_images)


# --- Placeholder endpoints to avoid BuildError from templates linking to these pages ---
@market_bp.route('/cart')
def cart():
    # Simple placeholder - redirect to home for now
    return redirect(url_for('market_place.home'))


@market_bp.route('/products')
def products():
    return redirect(url_for('market_place.home'))


@market_bp.route('/categories')
def categories():
    return redirect(url_for('market_place.home'))


@market_bp.route('/services')
def services():
    return redirect(url_for('market_place.home'))


@market_bp.route('/digital_goods')
def digital_goods():
    return redirect(url_for('market_place.home'))


@market_bp.route('/orders')
def orders():
    # require login in real implementation; placeholder redirects to home
    return redirect(url_for('market_place.home'))

@market_bp.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_detail(product_id):
    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()

    if not product:
        conn.close()
        abort(404)

    if request.method == 'POST':
        # 1. ADMIN STATUS TOGGLE (Available / Sold)
        if session.get('role') in ['admin', 'super_admin'] and 'update_status' in request.form:
            new_status = request.form.get('status')
            conn.execute("UPDATE products SET status = ? WHERE id = ?", (new_status, product_id))
            conn.commit()
            flash(f"Status updated to {new_status}.", "success")
            conn.close()
            return redirect(url_for('market_place.product_detail', product_id=product_id))

        # 2. PUBLIC INQUIRY SUBMISSION
        phone_raw = (request.form.get('phone') or '').strip()
        message = (request.form.get('message') or '').strip()
        user_id = session.get('user_id')

        # Server-side validation: require +260 country code and digits only
        import re
        if not re.match(r'^\+260\d{8,12}$', phone_raw):
            conn.close()
            flash('Please provide a valid phone number starting with +260 and digits only.', 'error')
            return redirect(url_for('market_place.product_detail', product_id=product_id))

        try:
            conn.execute("""
                INSERT INTO product_inquiries (product_id, user_id, phone, message)
                VALUES (?, ?, ?, ?)
            """, (product_id, user_id, phone_raw, message))
            conn.commit()
            flash('Inquiry sent — admin will get back to you shortly.', 'success')
        except Exception as e:
            print(f"Database Error: {e}")
            flash('Could not send inquiry. Please try again later.', 'danger')
        finally:
            conn.close()

        return redirect(url_for('market_place.product_detail', product_id=product_id))

    conn.close()
    return render_template('mp_product_detail.html', product=product, get_images=get_product_images)

# ==================================================
# ADMIN MANAGEMENT (ADD / EDIT / DELETE)
# ==================================================

@market_bp.route("/admin/add", methods=["GET", "POST"])
@login_required
def add_product():
    if session.get("role") not in ["admin", "super_admin"]:
        abort(403)

    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        price = request.form.get("price")
        
        files = request.files.getlist('images')
        filenames = []

        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        for i, file in enumerate(files):
            if file and file.filename != '' and allowed_file(file.filename):
                filename = f"{int(time.time())}_{i}_{secure_filename(file.filename)}"
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                filenames.append(filename)

        image_data = ",".join(filenames) if filenames else None

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO products (name, description, price, image, created_by, is_active, status)
            VALUES (?, ?, ?, ?, ?, 1, 'available')
        """, (name, description, price, image_data, session.get('user_id')))
        conn.commit()
        conn.close()
        flash("Product listed successfully.", "success")
        return redirect(url_for("market_place.admin_products"))

    return render_template("admin_add_product.html", product=None)

@market_bp.route("/admin/products")
@login_required
def admin_products():
    if session.get("role") not in ["admin", "super_admin"]:
        abort(403)
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("admin_products.html", products=products, get_images=get_product_images)

@market_bp.route("/admin/product/<int:product_id>/toggle")
@login_required
def toggle_product(product_id):
    if session.get("role") not in ["admin", "super_admin"]:
        abort(403)
    conn = get_db_connection()
    conn.execute("UPDATE products SET is_active = 1 - is_active WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    flash("Visibility toggled.", "info")
    return redirect(url_for("market_place.admin_products"))

@market_bp.route("/admin/product/<int:product_id>/delete")
@login_required
def delete_product(product_id):
    if session.get("role") not in ["admin", "super_admin"]:
        abort(403)
    conn = get_db_connection()
    product = conn.execute("SELECT image FROM products WHERE id = ?", (product_id,)).fetchone()
    
    if product and product['image']:
        for img in product['image'].split(','):
            path = os.path.join(UPLOAD_FOLDER, img.strip())
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
                
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    flash("Deleted successfully.", "success")
    return redirect(url_for("market_place.admin_products"))

@market_bp.route('/product/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if session.get('role') not in ['admin', 'super_admin']:
        abort(403)

    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()

    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        description = request.form.get('description')
        status = request.form.get('status')

        # Handle New Image Uploads
        files = request.files.getlist('images')
        new_filenames = []
        for i, file in enumerate(files):
            if file and file.filename != '' and allowed_file(file.filename):
                filename = f"{int(time.time())}_edit_{i}_{secure_filename(file.filename)}"
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                new_filenames.append(filename)

        # Merge new images with existing ones
        existing_images = product['image'] if product['image'] else ""
        if new_filenames:
            updated_images = (existing_images + "," if existing_images else "") + ",".join(new_filenames)
        else:
            updated_images = existing_images

        conn.execute("""
            UPDATE products 
            SET name = ?, price = ?, description = ?, status = ?, image = ?
            WHERE id = ?
        """, (name, price, description, status, updated_images, product_id))
        
        conn.commit()
        conn.close()
        flash("Product updated successfully!", "success")
        return redirect(url_for('market_place.product_detail', product_id=product_id))

    conn.close()
    return render_template('mp_edit_product.html', product=product, get_images=get_product_images)

@market_bp.route('/product/<int:product_id>/delete-image/<filename>')
@login_required
def delete_product_image(product_id, filename):
    if session.get('role') not in ['admin', 'super_admin']:
        abort(403)

    conn = get_db_connection()
    product = conn.execute("SELECT image FROM products WHERE id = ?", (product_id,)).fetchone()
    
    if product and product['image']:
        images = [img.strip() for img in product['image'].split(',') if img.strip()]
        if filename in images:
            images.remove(filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(path):
                try: os.remove(path)
                except: pass
            
            new_image_str = ",".join(images) if images else None
            conn.execute("UPDATE products SET image = ? WHERE id = ?", (new_image_str, product_id))
            conn.commit()
            flash("Image removed.", "info")
    
    conn.close()
    # Redirect back to edit page
    return redirect(url_for('market_place.edit_product', product_id=product_id))