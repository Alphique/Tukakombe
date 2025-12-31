# admin/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.database import get_db_connection
from auth.utils import verify_password
from auth.decorators import login_required, role_required
import os
from werkzeug.utils import secure_filename

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
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads', 'blogs')
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

# ------------------------------
# User Management (Super Admin Only)
# ------------------------------
@admin_bp.route('/users')
@login_required
@role_required('super_admin')
def users():
    db = get_db_connection()
    users = db.execute("SELECT id, email, role FROM users").fetchall()
    db.close()
    return render_template('users.html', users=users)

# ------------------------------
# Blog Creation
# ------------------------------
@admin_bp.route('/create-blog', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'super_admin')
def create_blog():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        file = request.files.get('image')

        image_filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            image_filename = filename

        db = get_db_connection()
        db.execute(
            "INSERT INTO blogs (title, content, image, created_by) VALUES (?, ?, ?, ?)",
            (title, content, image_filename, session['user_id'])
        )
        db.commit()
        db.close()

        flash("Blog created successfully!", "success")
        return redirect(url_for('admin.create_blog'))

    return render_template('admin_create.html')

# ------------------------------
# Edit Blog
# ------------------------------
@admin_bp.route('/edit-blog/<int:blog_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'super_admin')
def edit_blog(blog_id):
    db = get_db_connection()
    blog = db.execute(
        "SELECT * FROM blogs WHERE id = ?", (blog_id,)
    ).fetchone()

    if not blog:
        db.close()
        flash("Blog not found.", "error")
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')

        db.execute(
            "UPDATE blogs SET title = ?, content = ? WHERE id = ?",
            (title, content, blog_id)
        )
        db.commit()
        db.close()

        flash("Blog updated successfully.", "success")
        return redirect(url_for('admin.dashboard'))

    db.close()
    return render_template('admin_edit_blog.html', blog=blog)

# ------------------------------
# Delete Blog
# ------------------------------
@admin_bp.route('/delete-blog/<int:blog_id>', methods=['POST'])
@login_required
@role_required('admin', 'super_admin')
def delete_blog(blog_id):
    db = get_db_connection()

    # delete comments first (important!)
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
    flash("Comment deleted successfully.", "success")
    return redirect(request.referrer or url_for('admin.dashboard'))
