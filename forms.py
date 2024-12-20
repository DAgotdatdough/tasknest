from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length


# Registration form for user sign-up
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


# Login form for user authentication
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


# Form for initiating a password reset
class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Submit')


# Form for resetting the password
class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField('Reset Password')


# Form for creating and editing tasks
class TaskForm(FlaskForm):
    name = StringField('Task Name', validators=[DataRequired()])
    category = SelectField(
        'Category',
        choices=[('Work', 'Work'), ('Personal', 'Personal'), ('Other', 'Other')],
        validators=[DataRequired()],
    )
    priority = SelectField(
        'Priority',
        choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')],
        validators=[DataRequired()],
    )
    due_date = StringField('Due Date')  # Optional field for due dates
    completed = BooleanField('Completed')
    submit = SubmitField('Add Task')


# Form for updating user settings
class SettingsForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    submit = SubmitField('Update Profile')


# Form for adding comments to tasks
class CommentForm(FlaskForm):
    content = TextAreaField('Add a comment', validators=[DataRequired()])
    submit = SubmitField('Post Comment')
