# services/advisory/forms/advisory_request_form.py
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email

class AdvisoryRequestForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired()])
    email = EmailField("Email Address", validators=[DataRequired(), Email()])
    business_name = StringField("Business Name", validators=[DataRequired()])
    inquiry = TextAreaField("Your Inquiry", validators=[DataRequired()])
    submit = SubmitField("Submit Request")
