# admin/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, send_from_directory
from utils.database import get_db_connection
from auth.utils import verify_password
from auth.decorators import login_required, role_required
import os
from werkzeug.utils import secure_filename
import time 
from datetime import datetime

# ------------------------------
# Blueprint
# ------------------------------
admin_bp = Blueprint(
    'admin',
    __name__,
    template_folder='templates',
    url_prefix='/admin'
)

# ------------------------------
# Config
# ------------------------------
UPLOAD_BASE = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')
BLOG_UPLOAD_FOLDER = os.path.join(UPLOAD_BASE, 'blogs')
PRODUCT_UPLOAD_FOLDER = os.path.join(UPLOAD_BASE, 'products')
LOAN_UPLOAD_FOLDER = os.path.join(UPLOAD_BASE, 'loans')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'tiff', 'jfif', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------------------
# Admin Login (No Changes)
# ------------------------------
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        db = get_db_connection()
        admin = db.execute(
            "SELECT * FROM users WHERE email = ? AND role IN ('admin','super_admin')",
            (email,)
        ).fetchone()
        db.close()
        if not admin or not verify_password(password, admin['password']):
            flash("Invalid admin credentials", "error")
            return redirect(request.url)
        session.clear()
        session['user_id'] = admin['id']
        session['role'] = admin['role']
        return redirect(url_for('admin.dashboard'))
    return render_template('admin_login.html')

# ------------------------------
# Admin Dashboard (No Changes)
# ------------------------------
@admin_bp.route('/dashboard')
@login_required
@role_required('admin', 'super_admin')
def dashboard():
    db = get_db_connection()
    blogs = db.execute("SELECT id, title, created_at, status FROM blogs ORDER BY created_at DESC").fetchall()
    comments = db.execute("""
        SELECT comments.id, comments.blog_id, comments.content, comments.created_at, users.email AS user_email
        FROM comments
        JOIN users ON users.id = comments.user_id
        ORDER BY comments.created_at DESC
    """).fetchall()
    loans = db.execute("""
        SELECT la.id, la.application_number, la.loan_type, la.status, la.applied_date, u.email
        FROM loan_applications la
        JOIN users u ON u.id = la.user_id
        ORDER BY la.applied_date DESC
        LIMIT 5
    """).fetchall()
    db.close()
    return render_template('dashboard.html', blogs=blogs, comments=comments, loans=loans)

# ------------------------------
# Blog Routes (FIXED INDENTATION ERROR)
# ------------------------------
@admin_bp.route('/create-blog', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'super_admin')
def create_blog():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        status = request.form.get('status', 'published')
        file = request.files.get('image')
        image_filename = None
        if file and file.filename != '':
            if allowed_file(file.filename):
                filename = f"{int(time.time())}_{secure_filename(file.filename)}"
                os.makedirs(BLOG_UPLOAD_FOLDER, exist_ok=True)
                file.save(os.path.join(BLOG_UPLOAD_FOLDER, filename))
                image_filename = filename
            else:
                flash("File type not allowed.", "error")
        db = get_db_connection()
        db.execute("INSERT INTO blogs (title, content, image, created_by, status) VALUES (?, ?, ?, ?, ?)",
                   (title, content, image_filename, session['user_id'], status))
        db.commit()
        db.close()
        flash("Blog created successfully!", "success")
        return redirect(url_for('admin.dashboard'))
    return render_template('admin_create.html', blog={})

@admin_bp.route('/edit-blog/<int:blog_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'super_admin')
def edit_blog(blog_id):
    db = get_db_connection()
    blog = db.execute("SELECT * FROM blogs WHERE id = ?", (blog_id,)).fetchone()
    if not blog:
        db.close()
        flash("Blog not found.", "error")
        return redirect(url_for('admin.dashboard'))
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        status = request.form.get('status')
        file = request.files.get('image')
        image_filename = blog['image']
        if file and file.filename != '':
            if allowed_file(file.filename):
                filename = f"{int(time.time())}_{secure_filename(file.filename)}"
                os.makedirs(BLOG_UPLOAD_FOLDER, exist_ok=True)
                file.save(os.path.join(BLOG_UPLOAD_FOLDER, filename))
                image_filename = filename
                if blog['image']:
                    old_path = os.path.join(BLOG_UPLOAD_FOLDER, blog['image'])
                    if os.path.exists(old_path): os.remove(old_path)
        db.execute("UPDATE blogs SET title = ?, content = ?, image = ?, status = ? WHERE id = ?",
                   (title, content, image_filename, status, blog_id))
        db.commit()
        db.close()
        return redirect(url_for('admin.dashboard'))
    db.close()
    return render_template('admin_edit_blog.html', blog=blog)

@admin_bp.route('/delete-blog/<int:blog_id>', methods=['POST'])
@login_required
@role_required('admin', 'super_admin')
def delete_blog(blog_id):
    db = get_db_connection()
    blog = db.execute("SELECT image FROM blogs WHERE id = ?", (blog_id,)).fetchone()
    if blog and blog['image']:
        try:
            os.remove(os.path.join(BLOG_UPLOAD_FOLDER, blog['image']))
        except:
            pass
    db.execute("DELETE FROM comments WHERE blog_id = ?", (blog_id,))
    db.execute("DELETE FROM blogs WHERE id = ?", (blog_id,))
    db.commit()
    db.close()
    flash("Blog deleted successfully.", "success")
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/delete-comment/<int:comment_id>', methods=['POST'])
@login_required
@role_required('admin', 'super_admin')
def delete_comment(comment_id):
    db = get_db_connection()
    db.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    db.commit()
    db.close()
    flash("Comment deleted.", "success")
    return redirect(request.referrer or url_for('admin.dashboard'))

# ------------------------------
# Product Routes (FIXED FOR MULTI-IMAGE)
# ------------------------------
@admin_bp.route('/products/create', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'super_admin')
def create_product():
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        description = request.form.get('description')
        
        # FIX: Capture multiple images (input name is 'images' in the template)
        files = request.files.getlist('images')
        filenames = []

        if not os.path.exists(PRODUCT_UPLOAD_FOLDER):
            os.makedirs(PRODUCT_UPLOAD_FOLDER, exist_ok=True)

        for i, file in enumerate(files):
            if file and file.filename != '' and allowed_file(file.filename):
                # include index to help ensure uniqueness when multiple files uploaded
                filename = f"{int(time.time())}_{i}_{secure_filename(file.filename)}"
                file.save(os.path.join(PRODUCT_UPLOAD_FOLDER, filename))
                filenames.append(filename)

        image_data = ",".join(filenames) if filenames else None

        db = get_db_connection()
        db.execute(
            "INSERT INTO products (name, description, price, image) VALUES (?, ?, ?, ?)",
            (name, description, price, image_data)
        )
        db.commit()
        db.close()

        flash("Product added successfully.", "success")
        return redirect(url_for('market_place.home'))

    return render_template('admin_create_product.html')

@admin_bp.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
@role_required('admin', 'super_admin')
def delete_product(product_id):
    db = get_db_connection()
    product = db.execute("SELECT image FROM products WHERE id = ?", (product_id,)).fetchone()
    
    # FIX: Delete every image in the comma-separated string
    if product and product['image']:
        for img in product['image'].split(','):
            try:
                path = os.path.join(PRODUCT_UPLOAD_FOLDER, img.strip())
                if os.path.exists(path): os.remove(path)
            except:
                pass

    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    db.close()

    flash("Product deleted.", "success")
    return redirect(url_for('market_place.home'))

# ------------------------------
# Product Inquiries (No Changes)
# ------------------------------
@admin_bp.route('/product-inquiries')
@login_required
@role_required('admin', 'super_admin')
def product_inquiries_view():
    db = get_db_connection()
    inquiries = db.execute("""
        SELECT pi.id, pi.message, pi.created_at, p.name AS product_name
        FROM product_inquiries pi
        JOIN products p ON p.id = pi.product_id
        ORDER BY pi.created_at DESC
    """).fetchall()
    db.close()
    return render_template('admin_product_inquiries.html', inquiries=inquiries)

@admin_bp.route('/product-inquiries/delete/<int:inquiry_id>', methods=['POST'])
@login_required
@role_required('admin', 'super_admin')
def delete_product_inquiry(inquiry_id):
    db = get_db_connection()
    db.execute("DELETE FROM product_inquiries WHERE id = ?", (inquiry_id,))
    db.commit()
    db.close()
    flash("Inquiry deleted.", "success")
    return redirect(url_for('admin.product_inquiries_view'))

# ------------------------------
# Loan Routes (No Changes)
# ------------------------------
@admin_bp.route('/loans')
@login_required
@role_required('admin', 'super_admin')
def list_loans():
    db = get_db_connection()
    query = """
        SELECT la.id, la.application_number, la.loan_type, la.status, la.applied_date, u.email,
        COALESCE(p.full_name, b.business_name, 'Unknown') AS display_name
        FROM loan_applications la
        JOIN users u ON u.id = la.user_id
        LEFT JOIN personal_loan_details p ON la.id = p.application_id
        LEFT JOIN business_loan_details b ON la.id = b.application_id
        ORDER BY la.applied_date DESC
    """
    loans = db.execute(query).fetchall()
    db.close()
    return render_template('admin_loans_list.html', loans=loans)

@admin_bp.route('/loans/<int:loan_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'super_admin')
def view_loan(loan_id):
    db = get_db_connection()
    if request.method == 'POST':
        status = request.form.get('status')
        admin_notes = request.form.get('admin_notes')
        db.execute("""
            UPDATE loan_applications SET status = ?, admin_notes = ?, updated_date = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, admin_notes, loan_id))
        db.commit()
        return redirect(url_for('admin.view_loan', loan_id=loan_id))
    loan = db.execute("SELECT la.*, u.email AS applicant_email FROM loan_applications la JOIN users u ON u.id = la.user_id WHERE la.id = ?", (loan_id,)).fetchone()
    personal_details = db.execute("SELECT * FROM personal_loan_details WHERE application_id = ?", (loan_id,)).fetchone()
    business_details = db.execute("SELECT * FROM business_loan_details WHERE application_id = ?", (loan_id,)).fetchone()
    collateral_items = db.execute("SELECT * FROM collateral_items WHERE application_id = ?", (loan_id,)).fetchall()
    m_revenue = business_details['monthly_revenue'] if business_details and business_details['monthly_revenue'] else 0.0
    b_address = business_details['business_address'] if business_details and business_details['business_address'] else 'Not specified'
    attachments_raw = db.execute("SELECT * FROM application_attachments WHERE application_id = ?", (loan_id,)).fetchall()
    attachments = [dict(row) for row in attachments_raw]
    db.close()
    return render_template('admin_loan_management.html', loan=loan, attachments=attachments, collateral_items=collateral_items, personal_details=personal_details, business_details=business_details, monthly_revenue=m_revenue, business_address=b_address)

@admin_bp.route('/loans/filter')
@login_required
@role_required('admin', 'super_admin')
def filter_loans():
    status, loan_type = request.args.get('status'), request.args.get('loan_type')
    db = get_db_connection()
    query = "SELECT la.id, la.application_number, la.loan_type, la.status, la.applied_date, u.email FROM loan_applications la JOIN users u ON u.id = la.user_id WHERE 1=1"
    params = []
    if status: query += " AND la.status = ?"; params.append(status)
    if loan_type: query += " AND la.loan_type = ?"; params.append(loan_type)
    loans = db.execute(query + " ORDER BY la.applied_date DESC", params).fetchall()
    db.close()
    return render_template('admin_loans_list.html', loans=loans, filter_status=status, loan_type=loan_type)

@admin_bp.route('/loans/attachments/<path:filename>')
@login_required
@role_required('admin', 'super_admin')
def download_attachment(filename):
    try:
        if os.path.exists(os.path.join(LOAN_UPLOAD_FOLDER, filename)):
            return send_from_directory(LOAN_UPLOAD_FOLDER, filename, as_attachment=True)
        return send_from_directory(LOAN_UPLOAD_FOLDER, filename.split('uploads/loans/')[-1], as_attachment=True)
    except:
        flash("File not found.", "error")
        return redirect(url_for('admin.list_loans'))

@admin_bp.route('/loans/delete/<int:loan_id>', methods=['POST'])
@login_required
@role_required('admin', 'super_admin')
def delete_loan(loan_id):
    db = get_db_connection()
    db.execute("DELETE FROM loan_applications WHERE id = ?", (loan_id,))
    db.commit()
    db.close()
    return redirect(url_for('admin.list_loans'))

# ------------------------------
# View Inquiries
# ------------------------------
@admin_bp.route("/tukakula/queries")
@login_required
@role_required('admin', 'super_admin')
def tukakula_queries():
    conn = get_db_connection()
    queries = conn.execute("""
        SELECT id, full_name, company_name, email, phone, whatsapp, 
               inquiry_target, service, subject, reason, message, 
               created_at, status 
        FROM tukakula_queries 
        ORDER BY created_at DESC
    """).fetchall()
    conn.close()
    return render_template("admin_tukakula_queries.html", queries=queries)

# ------------------------------
# Toggle Status (FIXED ROUTE TYPE)
# ------------------------------
@admin_bp.route("/tukakula/queries/toggle-status/<string:query_id>", methods=["POST"])
@login_required
@role_required('admin', 'super_admin')
def toggle_query_status(query_id):
    conn = get_db_connection()
    query = conn.execute("SELECT status FROM tukakula_queries WHERE id = ?", (query_id,)).fetchone()
    
    if query:
        new_status = 'resolved' if query['status'] == 'new' else 'new'
        conn.execute("UPDATE tukakula_queries SET status = ? WHERE id = ?", (new_status, query_id))
        conn.commit()
        flash(f"Inquiry marked as {new_status}!", "success")
    
    conn.close()
    return redirect(url_for('admin.tukakula_queries'))

# ------------------------------
# Delete Inquiry
# ------------------------------
@admin_bp.route("/tukakula/queries/delete/<string:query_id>", methods=["POST"])
@login_required
@role_required('admin', 'super_admin')
def delete_inquiry(query_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM tukakula_queries WHERE id = ?", (query_id,))
    conn.commit()
    conn.close()
    flash("Inquiry deleted successfully!", "success")
    return redirect(url_for('admin.tukakula_queries'))