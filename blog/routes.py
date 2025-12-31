from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from auth.decorators import login_required
from utils.database import get_db_connection

blog_bp = Blueprint(
    'blog',
    __name__,
    url_prefix='/blog',
    template_folder='templates'
)

# ------------------------------
# Blog Home: list all blogs with comments
# ------------------------------
@blog_bp.route('/', methods=['GET'])
def blog_home():
    conn = get_db_connection()
    blogs = conn.execute("""
        SELECT id, title, content, image, created_at
        FROM blogs
        ORDER BY created_at DESC
    """).fetchall()

    blogs_with_comments = []
    for blog in blogs:
        comments = conn.execute("""
            SELECT c.id, c.content, c.created_at, u.email AS user_email
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.blog_id = ?
            ORDER BY c.created_at ASC
        """, (blog['id'],)).fetchall()

        b = dict(blog)
        b['comments'] = [dict(c) for c in comments]
        blogs_with_comments.append(b)

    conn.close()
    return render_template("blog_home.html", blogs=blogs_with_comments)


# ------------------------------
# Blog Detail: single blog view with comments
# ------------------------------
@blog_bp.route('/<int:blog_id>', methods=['GET', 'POST'])
@login_required
def blog_detail(blog_id):
    conn = get_db_connection()
    blog = conn.execute("SELECT * FROM blogs WHERE id = ?", (blog_id,)).fetchone()

    if not blog:
        conn.close()
        flash('Blog not found.', 'error')
        return redirect(url_for('blog.blog_home'))

    # Handle new comment submission
    if request.method == 'POST':
        content = request.form.get('content')
        if not content:
            flash('Comment cannot be empty.', 'error')
            return redirect(request.url)

        conn.execute(
            "INSERT INTO comments (blog_id, user_id, content) VALUES (?, ?, ?)",
            (blog_id, session['user_id'], content)
        )
        conn.commit()
        flash('Comment submitted!', 'success')
        return redirect(request.url)

    # Fetch comments
    comments = conn.execute("""
        SELECT c.id, c.content, c.created_at, u.email AS user_email
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.blog_id = ?
        ORDER BY c.created_at ASC
    """, (blog_id,)).fetchall()

    conn.close()
    return render_template('blog_detail.html', blog=blog, comments=comments)


# ------------------------------
# Delete Comment (admin only)
# ------------------------------
@blog_bp.route('/delete-comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    if session.get('role') not in ['admin', 'super_admin']:
        flash("Unauthorized", "error")
        return redirect(request.referrer or url_for('blog.blog_home'))

    conn = get_db_connection()
    conn.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    conn.commit()
    conn.close()

    flash("Comment deleted successfully.", "success")
    return redirect(request.referrer or url_for('blog.blog_home'))
