from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from wtforms.widgets import CheckboxInput, ListWidget
from models import User

class MultiCheckboxField(SelectMultipleField):
    """Custom field for multiple checkboxes."""
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class RegistrationForm(FlaskForm):
    """User registration form."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('password', message='Passwords must match')
    ])
    visa_status = SelectField('Visa Status', choices=[
        ('', 'Select your visa status'),
        ('F1', 'F1 Student Visa'),
        ('H1B', 'H1B Work Visa'),
        ('L1', 'L1 Intracompany Transfer'),
        ('O1', 'O1 Extraordinary Ability'),
        ('Green Card', 'Green Card Holder'),
        ('Citizen', 'US Citizen'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    
    experience_level = SelectField('Experience Level', choices=[
        ('', 'Select your experience level'),
        ('Entry', 'Entry Level (0-2 years)'),
        ('Mid', 'Mid Level (3-5 years)'),
        ('Senior', 'Senior Level (6+ years)')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Register')
    
    def validate_email(self, email):
        """Check if email is already registered."""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email.')

class LoginForm(FlaskForm):
    """User login form."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class ProfileForm(FlaskForm):
    """User profile management form."""
    visa_status = SelectField('Visa Status', choices=[
        ('F1', 'F1 Student Visa'),
        ('H1B', 'H1B Work Visa'),
        ('L1', 'L1 Intracompany Transfer'),
        ('O1', 'O1 Extraordinary Ability'),
        ('Green Card', 'Green Card Holder'),
        ('Citizen', 'US Citizen'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    
    experience_level = SelectField('Experience Level', choices=[
        ('Entry', 'Entry Level (0-2 years)'),
        ('Mid', 'Mid Level (3-5 years)'),
        ('Senior', 'Senior Level (6+ years)')
    ], validators=[DataRequired()])
    
    preferred_locations = MultiCheckboxField('Preferred Locations', choices=[
        ('San Francisco, CA', 'San Francisco, CA'),
        ('New York, NY', 'New York, NY'),
        ('Seattle, WA', 'Seattle, WA'),
        ('Austin, TX', 'Austin, TX'),
        ('Boston, MA', 'Boston, MA'),
        ('Chicago, IL', 'Chicago, IL'),
        ('Los Angeles, CA', 'Los Angeles, CA'),
        ('Denver, CO', 'Denver, CO'),
        ('Remote', 'Remote'),
        ('Other', 'Other')
    ])
    
    skills = MultiCheckboxField('Skills', choices=[
        ('Python', 'Python'),
        ('JavaScript', 'JavaScript'),
        ('Java', 'Java'),
        ('C++', 'C++'),
        ('React', 'React'),
        ('Node.js', 'Node.js'),
        ('SQL', 'SQL'),
        ('AWS', 'AWS'),
        ('Docker', 'Docker'),
        ('Machine Learning', 'Machine Learning'),
        ('Data Science', 'Data Science'),
        ('Frontend Development', 'Frontend Development'),
        ('Backend Development', 'Backend Development'),
        ('Full Stack Development', 'Full Stack Development'),
        ('DevOps', 'DevOps'),
        ('Mobile Development', 'Mobile Development')
    ])
    
    submit = SubmitField('Update Profile')