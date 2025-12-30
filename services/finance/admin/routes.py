from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, session
import os

# Blueprint for finance admin
finance_admin_bp = Blueprint(
    'finance_admin',
    __name__,
    url_prefix='/finance/admin',
    template_folder='templates'
)

# Path to uploaded finance documents
DOCUMENTS_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../uploads/finance'))

# Example document database (replace with real DB queries)
DOCUMENTS = {
    1: {'client_name': 'Alice', 'type': 'ID', 'filename': 'ids/alice_id.pdf'},
    2: {'client_name': 'Bob', 'type': 'Bank Statement', 'filename': 'bank_statements/bob_bank.pdf'},
    3: {'client_name': 'Charlie', 'type': 'Business Doc', 'filename': 'business_docs/charlie_docs.pdf'}
}

# --- Admin Login ---
@finance_admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Simple example auth (replace with real logic)
        if username == 'admin' and password == 'password':
            session['admin_logged_in'] = True
            flash('Logged in successfully!', 'success')
            return redirect(url_for('finance_admin.dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('admin_login.html')


# --- Admin Logout ---
@finance_admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('finance_admin.login'))


# --- Admin Dashboard ---
@finance_admin_bp.route('/')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('finance_admin.login'))
    return render_template('admin_dashboard.html')


# --- Documents List ---
@finance_admin_bp.route('/documents')
def documents():
    if not session.get('admin_logged_in'):
        return redirect(url_for('finance_admin.login'))
    return render_template('documents.html', documents=DOCUMENTS)


# --- View a specific document in browser ---
@finance_admin_bp.route('/documents/view/<int:doc_id>')
def view_document(doc_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('finance_admin.login'))
    
    doc = DOCUMENTS.get(doc_id)
    if doc:
        filepath = os.path.join(DOCUMENTS_FOLDER, doc['filename'])
        if os.path.exists(filepath):
            return send_from_directory(DOCUMENTS_FOLDER, doc['filename'])
        flash('File not found on server.', 'danger')
    else:
        flash('Document not found.', 'danger')
    return redirect(url_for('finance_admin.documents'))


# --- Download a specific document ---
@finance_admin_bp.route('/documents/download/<int:doc_id>')
def download_document(doc_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('finance_admin.login'))
    
    doc = DOCUMENTS.get(doc_id)
    if doc:
        filepath = os.path.join(DOCUMENTS_FOLDER, doc['filename'])
        if os.path.exists(filepath):
            return send_from_directory(DOCUMENTS_FOLDER, doc['filename'], as_attachment=True)
        flash('File not found on server.', 'danger')
    else:
        flash('Document not found.', 'danger')
    return redirect(url_for('finance_admin.documents'))
