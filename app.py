from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from flask_migrate import Migrate
from models import db, User, Task
from forms import RegistrationForm, LoginForm, ForgotPasswordForm, ResetPasswordForm, TaskForm
from config import Config

# Flask app initialization
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Flask-Mail setup
mail = Mail(app)

# Flask-Migrate setup
migrate = Migrate(app, db)

# Flask-Login setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Initialize the database
with app.app_context():
    db.create_all()

@app.route("/")
@login_required
def home():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    categories = ['Work', 'Personal', 'Other']
    priorities = ['Low', 'Medium', 'High']
    return render_template("home.html", tasks=tasks, categories=categories, priorities=priorities)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken!', 'danger')
            return redirect(url_for('register'))
        new_user = User(username=form.username.data, email=form.email.data)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user = current_user
    Task.query.filter_by(user_id=user.id).delete()  # Delete user's tasks
    db.session.delete(user)
    db.session.commit()
    flash('Your account has been deleted.', 'success')
    return redirect(url_for('register'))

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash("User verified. Please reset your password.", "success")
            return redirect(url_for('reset_password', user_id=user.id))
        else:
            flash("No user found with this email.", "danger")
    return render_template("forgot_password.html", form=form)

@app.route("/reset_password/<int:user_id>", methods=["GET", "POST"])
def reset_password(user_id):
    form = ResetPasswordForm()
    user = User.query.get(user_id)
    if not user:
        flash("Invalid user.", "danger")
        return redirect(url_for('login'))

    if form.validate_on_submit():
        user.set_password(form.password.data)  # Hash new password
        db.session.commit()
        flash("Your password has been updated!", "success")
        return redirect(url_for('login'))
    return render_template("reset_password.html", form=form)

@app.route("/add", methods=["POST"])
@login_required
def add_task():
    name = request.form.get('name')
    category = request.form.get('category')
    priority = request.form.get('priority')
    due_date = request.form.get('due_date')

    if not name or not category or not priority:
        flash("All fields are required except due date.", "danger")
        return redirect(url_for("home"))

    task = Task(
        user_id=current_user.id,
        name=name,
        category=category,
        priority=priority,
        due_date=due_date,
        completed=False,
    )
    db.session.add(task)
    db.session.commit()
    flash("Task added successfully!", "success")
    return redirect(url_for("home"))

@app.route('/update/<int:task_id>', methods=['POST'])
@login_required
def update_task(task_id):
    task = db.session.get(Task, task_id)
    if task and task.user_id == current_user.id:
        task.completed = not task.completed
        db.session.commit()
        flash('Task updated successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if task and task.user_id == current_user.id:
        db.session.delete(task)
        db.session.commit()
        flash('Task deleted successfully!', 'success')
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)









