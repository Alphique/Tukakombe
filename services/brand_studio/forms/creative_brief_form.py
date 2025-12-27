# services/brand_studio/forms/creative_brief_form.py
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email

class CreativeBriefForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired()])
    email = EmailField("Email Address", validators=[DataRequired(), Email()])
    company = StringField("Company / Brand Name", validators=[DataRequired()])
    project_type = StringField("Project Type", validators=[DataRequired()])
    brief = TextAreaField("Creative Brief", validators=[DataRequired()])
    submit = SubmitField("Submit Brief")
