# admin/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.database import get_db_connection
from auth.utils import verify_password
from auth.decorators import login_required, role_required
import os
from werkzeug.utils import secure_filename
import time  # add at top

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
BLOG_UPLOAD_FOLDER = os.path.join(
    os.path.dirname(__file__), '..', 'static', 'uploads', 'blogs'
)
PRODUCT_UPLOAD_FOLDER = os.path.join(
    os.path.dirname(__file__), '..', 'static', 'uploads', 'products'
)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------------------
# Admin Login
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
# Admin Dashboard
# ------------------------------
@admin_bp.route('/dashboard')
@login_required
@role_required('admin', 'super_admin')
def dashboard():
    db = get_db_connection()

    blogs = db.execute("""
        SELECT id, title, created_at
        FROM blogs
        ORDER BY created_at DESC
    """).fetchall()

    comments = db.execute("""
        SELECT
            comments.id,
            comments.blog_id,
            comments.content,
            comments.created_at,
            users.email AS user_email
        FROM comments
        JOIN users ON users.id = comments.user_id
        ORDER BY comments.created_at DESC
    """).fetchall()

    db.close()

    return render_template(
        'dashboard.html',
        blogs=blogs,
        comments=comments
    )

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
        
        # DEBUG: Check if file actually reached the server
        if file:
            print(f"DEBUG: Filename received: {file.filename}")
        
        if file and file.filename != '':
            # Ensure the extension is allowed (check your ALLOWED_EXTENSIONS list)
            if allowed_file(file.filename):
                filename = f"{int(time.time())}_{secure_filename(file.filename)}"
                
                # Use current_app.root_path to be 100% sure of the location
                from flask import current_app
                upload_path = os.path.join(current_app.root_path, 'static', 'uploads', 'blogs')
                
                if not os.path.exists(upload_path):
                    os.makedirs(upload_path)
                
                save_path = os.path.join(upload_path, filename)
                file.save(save_path)
                image_filename = filename
                print(f"DEBUG: File saved to: {save_path}") # Check your console for this!
            else:
                print("DEBUG: File extension not allowed")

        db = get_db_connection()
        db.execute(
            "INSERT INTO blogs (title, content, image, created_by, status) VALUES (?, ?, ?, ?, ?)",
            (title, content, image_filename, session['user_id'], status)
        )
        db.commit()
        db.close()

        flash("Blog created successfully!", "success")
        return redirect(url_for('admin.dashboard'))

    return render_template('admin_create.html', blog={})

# ------------------------------
# Edit Blog
# ------------------------------
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
        status = request.form.get('status') # Get the new status (draft/published)
        file = request.files.get('image')

        image_filename = blog['image']  # Keep the old image by default

        # Logic to handle a NEW image upload
        if file and file.filename != '':
            if allowed_file(file.filename):
                # Create a unique filename
                filename = f"{int(time.time())}_{secure_filename(file.filename)}"
                
                # Ensure the directory exists
                from flask import current_app
                upload_path = os.path.join(current_app.root_path, 'static', 'uploads', 'blogs')
                os.makedirs(upload_path, exist_ok=True)
                
                # Save the new file
                file.save(os.path.join(upload_path, filename))
                image_filename = filename 
                
                # Optional: Delete the old physical file from the folder to save space
                if blog['image']:
                    old_path = os.path.join(upload_path, blog['image'])
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except:
                            pass

        # UPDATE EVERYTHING: title, content, image, AND status
        db.execute(
            """
            UPDATE blogs 
            SET title = ?, content = ?, image = ?, status = ? 
            WHERE id = ?
            """,
            (title, content, image_filename, status, blog_id)
        )
        db.commit()
        db.close()

        flash("Blog updated successfully.", "success")
        return redirect(url_for('admin.dashboard'))

    db.close()
    # Make sure your edit template is using the fixed version I gave you earlier
    return render_template('admin_edit_blog.html', blog=blog)

# ------------------------------
# Delete Blog
# ------------------------------
@admin_bp.route('/delete-blog/<int:blog_id>', methods=['POST'])
@login_required
@role_required('admin', 'super_admin')
def delete_blog(blog_id):
    db = get_db_connection()
    db.execute("DELETE FROM comments WHERE blog_id = ?", (blog_id,))
    db.execute("DELETE FROM blogs WHERE id = ?", (blog_id,))
    db.commit()
    db.close()

    flash("Blog deleted successfully.", "success")
    return redirect(url_for('admin.dashboard'))

# ------------------------------
# Delete Comment
# ------------------------------
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
# Product Creation
# ------------------------------
@admin_bp.route('/products/create', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'super_admin')
def create_product():
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        description = request.form.get('description')
        image = request.files.get('image')

        filename = None
        if image and allowed_file(image.filename):
            os.makedirs(PRODUCT_UPLOAD_FOLDER, exist_ok=True)
            filename = secure_filename(image.filename)
            image.save(os.path.join(PRODUCT_UPLOAD_FOLDER, filename))

        db = get_db_connection()
        db.execute("""
            INSERT INTO products (name, description, price, image)
            VALUES (?, ?, ?, ?)
        """, (name, description, price, filename))
        db.commit()
        db.close()

        flash("Product added successfully.", "success")
        return redirect(url_for('market_place.home'))

    return render_template('admin_create_product.html')

# ------------------------------
# Delete Product
# ------------------------------
@admin_bp.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
@role_required('admin', 'super_admin')
def delete_product(product_id):
    db = get_db_connection()
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    db.close()

    flash("Product deleted.", "success")
    return redirect(url_for('market_place.home'))

# ------------------------------
# Delete Product Inquiry
# ------------------------------
@admin_bp.route('/product-inquiries/delete/<int:inquiry_id>', methods=['POST'])
@login_required
@role_required('admin', 'super_admin')
def delete_product_inquiry(inquiry_id):
    db = get_db_connection()
    db.execute(
        "DELETE FROM product_inquiries WHERE id = ?",
        (inquiry_id,)
    )
    db.commit()
    db.close()

    flash("Inquiry deleted.", "success")
    return redirect(url_for('admin.product_inquiries'))

# ------------------------------
# View Product Inquiries
# ------------------------------
@admin_bp.route('/product-inquiries')
@login_required
@role_required('admin', 'super_admin')
def product_inquiries_view():
    db = get_db_connection()

    inquiries = db.execute("""
        SELECT
            product_inquiries.id,
            product_inquiries.message,
            product_inquiries.created_at,
            products.name AS product_name
        FROM product_inquiries
        JOIN products ON products.id = product_inquiries.product_id
        ORDER BY product_inquiries.created_at DESC
    """).fetchall()

    db.close()

    return render_template(
        'admin_product_inquiries.html',
        inquiries=inquiries
    )

#---------------------------------------
# Loan Management Routes
#--------------------------------------
@admin_bp.route('/loans-manage', endpoint='loans')
@login_required
@role_required('admin', 'super_admin')
def manage_loans():
    db = get_db_connection()
    loans = db.execute("""
        SELECT
            loan_applications.id,
            loan_applications.business_name,
            loan_applications.loan_amount,
            loan_applications.status,
            loan_applications.created_at,
            users.email AS applicant_email
        FROM loan_applications
        JOIN users ON users.id = loan_applications.user_id
        ORDER BY loan_applications.created_at DESC
    """).fetchall()
    db.close()

    return render_template(
        'admin_loan_management.html',
        loans=loans
    )


@admin_bp.route('/loans/<int:loan_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'super_admin')
def view_loan(loan_id):
    db = get_db_connection()

    loan = db.execute("""
        SELECT loan_applications.*, users.email
        FROM loan_applications
        JOIN users ON users.id = loan_applications.user_id
        WHERE loan_applications.id = ?
    """, (loan_id,)).fetchone()

    attachments = db.execute("""
        SELECT * FROM loan_attachments
        WHERE loan_id = ?
    """, (loan_id,)).fetchall()

    if request.method == 'POST':
        status = request.form.get('status')
        admin_notes = request.form.get('admin_notes')

        db.execute("""
            UPDATE loan_applications
            SET status = ?, admin_notes = ?
            WHERE id = ?
        """, (status, admin_notes, loan_id))
        db.commit()

        flash("Loan status updated.", "success")
        return redirect(url_for('admin.manage_loans'))

    db.close()
    return render_template(
        'admin_view_loan.html',
        loan=loan,
        attachments=attachments
    )
