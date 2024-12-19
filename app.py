from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail
from flask_migrate import Migrate
from models import db, User, Task, Comment
from forms import RegistrationForm, LoginForm, ForgotPasswordForm, ResetPasswordForm, SettingsForm, CommentForm
from config import Config
from datetime import datetime, timedelta
import os

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


@app.route('/')
@login_required
def dashboard():
    # Fetch all tasks for the current user
    tasks_query = Task.query.filter_by(user_id=current_user.id).all()

    # Number of tasks completed per week/month
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    start_of_month = today.replace(day=1)

    completed_this_week = sum(
        1 for task in tasks_query
        if task.completed and task.due_date and start_of_week <= datetime.strptime(task.due_date, '%Y-%m-%d').date()
        <= end_of_week
    )
    completed_this_month = sum(
        1 for task in tasks_query
        if task.completed and task.due_date and start_of_month <= datetime.strptime(task.due_date, '%Y-%m-%d').date()
    )

    # Task categories for pie chart
    categories = ["Work", "Personal", "Urgent"]
    category_counts = {category: sum(1 for task in tasks_query if task.category == category) for category in categories}

    # Progress calculation
    total_tasks = len(tasks_query)
    completed_tasks = sum(1 for task in tasks_query if task.completed)
    progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    return render_template(
        'dashboard.html',
        completed_this_week=completed_this_week,
        completed_this_month=completed_this_month,
        category_counts=category_counts,
        progress=int(progress)
    )


@app.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    search_query = request.args.get("search", "")
    sort_by = request.args.get("sort_by", None)
    category_filter = request.args.get("category", None)

    # Start with all tasks for the user
    tasks_query = Task.query.filter_by(user_id=current_user.id)

    # Filter by search query if provided
    if search_query:
        tasks_query = tasks_query.filter(Task.name.ilike(f"%{search_query}%"))

    # Apply category filter if selected
    if category_filter:
        tasks_query = tasks_query.filter_by(category=category_filter)

    # Apply sorting
    if sort_by == "due_date":
        tasks_query = tasks_query.order_by(Task.due_date.asc())
    elif sort_by == "priority":
        tasks_query = tasks_query.order_by(Task.priority.asc())
    elif sort_by == "completed":
        tasks_query = tasks_query.order_by(Task.completed.asc())

    user_tasks = tasks_query.all()

    # Clear duplicate logic
    today = datetime.now().date()
    overdue_tasks = [
        task for task in user_tasks
        if task.due_date and not task.completed and datetime.strptime(task.due_date, '%Y-%m-%d').date() < today
    ]
    upcoming_tasks = [
        task for task in user_tasks
        if task.due_date and not task.completed and 0 <= (datetime.strptime(task.due_date, '%Y-%m-%d').date() - today).days <= 1
    ]

    # Ensure unique task IDs for rendering
    overdue_tasks = list({task.id: task for task in overdue_tasks}.values())
    upcoming_tasks = list({task.id: task for task in upcoming_tasks}.values())

    categories = ["Work", "Personal", "Urgent"]
    priorities = ["Low", "Medium", "High"]

    return render_template(
        'tasks.html',
        tasks=user_tasks,
        overdue_tasks=overdue_tasks,
        upcoming_tasks=upcoming_tasks,
        categories=categories,
        priorities=priorities,
    )


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
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
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


@app.route('/update/<int:task_id>', methods=['POST'])
@login_required
def update_task(task_id):
    task = db.session.get(Task, task_id)
    if task and task.user_id == current_user.id:
        task.completed = not task.completed
        db.session.commit()
        flash('Task updated successfully!', 'success')
    return redirect(url_for('tasks'))


@app.route('/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if task and task.user_id == current_user.id:
        db.session.delete(task)
        db.session.commit()
        flash('Task deleted successfully!', 'success')
    return redirect(url_for('tasks'))


@app.route('/settings', methods=["GET", "POST"])
@login_required
def set_settings():
    form = SettingsForm()

    if form.validate_on_submit():
        current_user.username = form.username.data
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('set_settings'))
    elif request.method == 'GET':
        form.username.data = current_user.username
    return render_template('settings.html', form=form, theme=session.get('theme', 'light'))


@app.route('/toggle_theme')
@login_required
def toggle_theme():
    current_theme = session.get('theme', 'light')
    new_theme = 'dark' if current_theme == 'light' else 'light'
    session['theme'] = new_theme
    return jsonify({'theme': new_theme})


@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    if request.is_json:
        data = request.get_json()
        name = data.get('name')
        category = data.get('category')
        priority = data.get('priority')
        due_date = data.get('due_date')
    else:
        name = request.form.get('name')
        category = request.form.get('category')
        priority = request.form.get('priority')
        due_date = request.form.get('due_date')

    if not name or not category or not priority:
        if request.is_json:
            return jsonify({"error": "All fields are required except due date."}), 400
        flash("All fields are required except due date.", "danger")
        return redirect(url_for("tasks"))

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

    if request.is_json:
        return jsonify({"message": "Task added successfully!"}), 200

    flash("Task added successfully!", "success")
    return redirect(url_for("tasks"))


@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    # Fetch all tasks for the current user
    tasks = Task.query.filter_by(user_id=current_user.id).all()

    today = datetime.now().date()
    upcoming_tasks = []
    overdue_tasks = []

    for task in tasks:
        if task.due_date and not task.completed:
            due_date = datetime.strptime(task.due_date, '%Y-%m-%d').date()
            if due_date < today:
                overdue_tasks.append({"name": task.name, "due_date": task.due_date})
            elif 0 <= (due_date - today).days <= 1:  # Tasks due in the next 1 day
                upcoming_tasks.append({"name": task.name, "due_date": task.due_date})

    return jsonify({
        "overdue_tasks": overdue_tasks,
        "upcoming_tasks": upcoming_tasks
    })


@app.route('/task/<int:task_id>/comment', methods=['POST'])
@login_required
def add_comment(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('You do not have permission to comment on this task.', 'danger')
        return redirect(url_for('tasks'))

    form = CommentForm()
    if form.validate_on_submit():
        new_comment = Comment(task_id=task_id, content=form.content.data)
        db.session.add(new_comment)
        db.session.commit()
        flash('Comment added successfully!', 'success')
    return redirect(url_for('task_details', task_id=task_id))

@app.route('/task/<int:task_id>')
@login_required
def task_details(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('You do not have permission to view this task.', 'danger')
        return redirect(url_for('tasks'))

    form = CommentForm()
    comments = Comment.query.filter_by(task_id=task.id).order_by(Comment.created_at.desc()).all()
    return render_template('task_details.html', task=task, form=form, comments=comments)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

if __name__ == "__main__":
    app.run(debug=True)
