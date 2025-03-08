from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'home'

# Mô hình User
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
# Mô hình Post
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route('/favicon.ico')
def favicon():
    return '', 204

# Đăng ký tài khoản
@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    
    if not username or not email or not password:
        flash("Vui lòng nhập đầy đủ thông tin.", "danger")
        return redirect(url_for("home"))

    if User.query.filter_by(email=email).first():
        flash("Email đã tồn tại. Vui lòng sử dụng email khác.", "danger")
        return redirect(url_for("home"))
    
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
    return redirect(url_for("home"))

# Đăng nhập
@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    user = User.query.filter_by(email=email).first()
    
    if user and bcrypt.check_password_hash(user.password, password):
        if user.is_blocked:
            flash("Tài khoản của bạn đã bị khóa.", "danger")
            return redirect(url_for("home"))
        login_user(user)
        return redirect(url_for("admin" if user.is_admin else "dashboard"))
    
    flash("Thông tin đăng nhập không hợp lệ.", "danger")
    return redirect(url_for("home"))

# Đăng xuất
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

# Bảng điều khiển
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        if not title or not content:
            flash("Tiêu đề và nội dung không được để trống.", "danger")
        else:
            new_post = Post(title=title, content=content, user_id=current_user.id)
            db.session.add(new_post)
            db.session.commit()
            flash("Đăng bài thành công!", "success")
        return redirect(url_for("dashboard"))
    
    posts = Post.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", user=current_user, posts=posts)

# Xóa nhiều bài viết
@app.route("/delete_posts", methods=["POST"])
@login_required
def delete_posts():
    post_ids = request.json.get("post_ids", [])
    if not post_ids:
        return jsonify({"message": "Không có bài viết nào được chọn."}), 400
    
    Post.query.filter(Post.id.in_(post_ids), Post.user_id == current_user.id).delete(synchronize_session=False)
    db.session.commit()
    
    return jsonify({"message": "Xóa thành công."}), 200

# Quản trị viên quản lý tài khoản
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        action = request.form.get('action')

        print(f"DEBUG: user_id={user_id}, action={action}")  # Debug giá trị nhận được

        if not user_id:
            flash("ID người dùng không hợp lệ!", "danger")
            return redirect(url_for('admin'))

        user = User.query.get(user_id)
        if not user:
            flash("Không tìm thấy người dùng!", "danger")
            return redirect(url_for('admin'))
        
        # Xử lý các hành động
        if user.is_admin and action == "block":
            flash("Không thể khóa tài khoản admin!", "danger")
        elif action == "block":
            user.is_blocked = True
            flash(f"Đã khóa tài khoản {user.username}", "warning")
        elif action == "unblock":
            user.is_blocked = False
            flash(f"Đã mở khóa tài khoản {user.username}", "success")
        elif action == "reset":
            user.set_password("111111")
            flash(f"Mật khẩu của {user.username} đã đặt lại thành '111111'", "info")

        db.session.commit()
        return redirect(url_for('admin'))

    users = User.query.all()
    return render_template('admin.html', users=users)


@app.route('/reset_password', methods=['POST'])
@login_required
def reset_password():
    if not current_user.is_admin:
        flash("Bạn không có quyền thực hiện thao tác này!", "danger")
        return redirect(url_for('admin'))

    user_id = request.form.get('user_id')
    user = User.query.get(user_id)

    if user:
        user.set_password("111111")  # Hàm này sẽ hash mật khẩu trước khi lưu
        db.session.commit()

        flash(f"Mật khẩu của {user.username} đã được đặt lại thành '111111'!", "success")
    else:
        flash("Không tìm thấy người dùng!", "danger")

    return redirect(url_for('admin'))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            admin_user = User(username="admin", email="admin@gmail.com", password=bcrypt.generate_password_hash("admin123").decode('utf-8'), is_admin=True)
            db.session.add(admin_user)
            db.session.commit()
    app.run(debug=True)
