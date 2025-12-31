from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from auth.decorators import login_required
from utils.database import get_db_connection

blog_bp = Blueprint(
    'blog',
    __name__,
    url_prefix='/blog',
    template_folder='templates'
)

# Public blog home (summary)
@blog_bp.route('/', methods=['GET'])
def blog_home():
    conn = get_db_connection()
    blogs = conn.execute("""
        SELECT id, title, substr(content, 1, 150) || '...' AS summary, created_at 
        FROM blogs 
        ORDER BY created_at DESC
    """).fetchall()
    conn.close()
    return render_template('blog_home.html', blogs=blogs)


# Full blog detail (requires login)
@blog_bp.route('/<int:blog_id>', methods=['GET', 'POST'])
@login_required
def blog_detail(blog_id):
    conn = get_db_connection()
    blog = conn.execute("SELECT * FROM blogs WHERE id = ?", (blog_id,)).fetchone()
    if not blog:
        conn.close()
        flash('Blog not found.', 'error')
        return redirect(url_for('blog.blog_home'))

    # Handle comments submission
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

    comments = conn.execute("""
        SELECT c.id, c.content, c.user_id, c.created_at, u.email AS user_email
        FROM comments c 
        LEFT JOIN users u ON c.user_id = u.id
        WHERE c.blog_id = ?
        ORDER BY c.created_at ASC
    """, (blog_id,)).fetchall()
    conn.close()

    return render_template('blog_detail.html', blog=blog, comments=comments)
