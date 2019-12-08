from flask_wtf import FlaskForm
from wtforms import StringField, DateTimeField, SubmitField
from wtforms.validators import DataRequired


class SearchForm(FlaskForm):
    source = StringField('Departure city', validators=[DataRequired()])
    destination = StringField('Destination city', validators=[DataRequired()])
    date = DateTimeField('Date', format='%Y-%m-%d', validators=[DataRequired()])
