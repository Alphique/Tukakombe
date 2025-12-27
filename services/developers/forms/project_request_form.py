# services/developers/forms/project_request_form.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, EmailField
from wtforms.validators import DataRequired, Email, Length

class ProjectRequestForm(FlaskForm):
    name = StringField(
        "Full Name",
        validators=[DataRequired(), Length(min=2, max=100)]
    )
    email = EmailField(
        "Email Address",
        validators=[DataRequired(), Email()]
    )
    project_title = StringField(
        "Project Title",
        validators=[DataRequired(), Length(min=2, max=150)]
    )
    description = TextAreaField(
        "Project Description",
        validators=[DataRequired(), Length(min=10)]
    )
    submit = SubmitField("Submit Request")
