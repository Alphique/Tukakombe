from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from auth.decorators import login_required, role_required
from utils.database import get_db_connection

blog_admin_bp = Blueprint(
    'blog_admin',
    __name__,
    url_prefix='/admin/blog',
    template_folder='templates'
)

# Dashboard - manage blogs
@login_required
@role_required('blog_admin', 'super_admin')
@blog_admin_bp.route('/dashboard', methods=['GET'])
def dashboard():
    conn = get_db_connection()
    blogs = conn.execute("SELECT * FROM blogs ORDER BY created_at DESC").fetchall()
    comments = conn.execute("""
        SELECT c.id, c.content, c.user_id, c.blog_id, u.email AS user_email 
        FROM comments c LEFT JOIN users u ON c.user_id = u.id 
        ORDER BY c.created_at DESC
    """).fetchall()
    conn.close()
    return render_template('admin_create.html', blogs=blogs, comments=comments)


# Create new blog
@login_required
@role_required('blog_admin', 'super_admin')
@blog_admin_bp.route('/create', methods=['GET', 'POST'])
def blog_create():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        author_id = session.get('user_id')

        if not title or not content:
            flash('Title and content are required.', 'error')
            return redirect(request.url)

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO blogs (title, content, author_id) VALUES (?, ?, ?)",
            (title, content, author_id)
        )
        conn.commit()
        conn.close()

        flash('Blog created successfully!', 'success')
        return redirect(url_for('blog_admin.dashboard'))

    return render_template('admin_create.html')


# Delete blog
@login_required
@role_required('blog_admin', 'super_admin')
@blog_admin_bp.route('/delete/<int:blog_id>')
def delete_blog(blog_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM blogs WHERE id = ?", (blog_id,))
    conn.commit()
    conn.close()
    flash('Blog deleted.', 'success')
    return redirect(url_for('blog_admin.dashboard'))


# Delete comment
@login_required
@role_required('blog_admin', 'super_admin')
@blog_admin_bp.route('/comment/delete/<int:comment_id>')
def delete_comment(comment_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    conn.commit()
    conn.close()
    flash('Comment deleted.', 'success')
    return redirect(url_for('blog_admin.dashboard'))
