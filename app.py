import os
import subprocess
import tempfile
import io
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from google import genai
from database import create_app, init_db, seed_db
from models import db, User

# Create Flask app using factory pattern
app = create_app()

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Configure the Gemini client
client = genai.Client(api_key=app.config['GOOGLE_API_KEY'])

def fix_latex_characters(latex_content):
    """Fix common LaTeX character escaping issues."""
    import re
    
    # Don't escape ampersands that are already part of LaTeX commands or in tabular environments
    # Only escape standalone ampersands that appear in regular text
    
    # First, protect existing LaTeX commands and table structures
    protected_patterns = [
        r'\\&',  # Already escaped ampersands
        r'&\s*\\\\',  # Table row separators
        r'&\s*\}',  # Table cell endings
        r'\{\s*&',  # Table cell beginnings
        r'\\begin\{tabular\}.*?\\end\{tabular\}',  # Entire tabular environments
        r'\\begin\{array\}.*?\\end\{array\}',  # Array environments
    ]
    
    # Temporarily replace protected patterns with placeholders
    placeholders = {}
    for i, pattern in enumerate(protected_patterns):
        placeholder = f"__PROTECTED_{i}__"
        matches = re.findall(pattern, latex_content, re.DOTALL)
        for j, match in enumerate(matches):
            specific_placeholder = f"{placeholder}_{j}"
            placeholders[specific_placeholder] = match
            latex_content = latex_content.replace(match, specific_placeholder, 1)
    
    # Now escape standalone ampersands in regular text
    # Look for ampersands that are not part of LaTeX syntax
    latex_content = re.sub(r'(?<!\\)&(?!\s*\\\\)(?!\s*\})', r'\\&', latex_content)
    
    # Restore protected patterns
    for placeholder, original in placeholders.items():
        latex_content = latex_content.replace(placeholder, original)
    
    # Fix other common LaTeX special characters that might cause issues
    # Only escape if not already escaped
    latex_content = re.sub(r'(?<!\\)%(?![^{]*\})', r'\\%', latex_content)  # Percent signs
    latex_content = re.sub(r'(?<!\\)\$(?![^{]*\})', r'\\$', latex_content)  # Dollar signs (outside math mode)
    
    # Fix encoding issues - ensure proper UTF-8 handling
    try:
        # Encode to UTF-8 and decode back to ensure proper encoding
        latex_content = latex_content.encode('utf-8', errors='replace').decode('utf-8')
    except UnicodeError:
        # If there are still encoding issues, replace problematic characters
        latex_content = latex_content.encode('ascii', errors='replace').decode('ascii')
    
    return latex_content

def remove_latex_comments(latex_content):
    """Remove LaTeX comments from the content."""
    import re
    
    # Remove specific comment patterns that appear in LaTeX resumes
    # Handle both escaped (\%) and unescaped (%) comments
    
    # Remove common comment patterns
    comment_patterns = [
        r'\\?%\s*Clear all header and footer fields',
        r'\\?%\s*Adjust margins',
        r'\\?%\s*Sections formatting',
        r'\\?%\s*Ensure that generate PDF is machine readable/ATS parsable',
        r'\\?%\s*Custom commands',
        r'\\?%\s*CV STARTS HERE',
        r'\\?%\s*HEADING',
        r'\\?%\s*SUMMARY',
        r'\\?%\s*EDUCATION',
        r'\\?%\s*EXPERIENCE',
        r'\\?%\s*PROJECTS',
        r'\\?%\s*SKILLS',
        r'\\?%\s*[-\-]+.*?[-\-]+',  # Decorative comment lines
        r'\\?%\s*[A-Za-z\s\-]+\s*\\',  # Comments followed by backslash
    ]
    
    # Apply all comment removal patterns
    for pattern in comment_patterns:
        latex_content = re.sub(pattern, '', latex_content, flags=re.IGNORECASE)
    
    # Remove lines that are purely comments (start with % or \% after optional whitespace)
    lines = latex_content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Skip lines that are purely comments
        if re.match(r'^\s*\\?%', line):
            continue
        
        # Remove any remaining inline comments at the end of lines
        line = re.sub(r'\\?%[^}]*$', '', line)
        
        # Keep the line (even if it's now empty, to preserve structure)
        cleaned_lines.append(line.rstrip())
    
    # Join lines back together
    cleaned_content = '\n'.join(cleaned_lines)
    
    # Remove excessive empty lines (more than 2 consecutive empty lines)
    cleaned_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_content)
    
    # Clean up any remaining whitespace issues
    cleaned_content = cleaned_content.strip()
    
    return cleaned_content

def extract_projects_section(latex_content):
    """Extract the Projects section from LaTeX content."""
    import re
    
    # Pattern to match the entire Projects section
    # From \section{Projects} to the next \section or end of document
    pattern = r'(\\section\{Projects\}.*?)(?=\\section\{[^}]+\}|\\end\{document\}|$)'
    
    match = re.search(pattern, latex_content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def replace_projects_section(original_latex, new_projects_section):
    """Replace the Projects section in the original LaTeX with the new one."""
    import re
    
    if not new_projects_section:
        return original_latex
    
    # Pattern to match the entire Projects section in the original
    pattern = r'(\\section\{Projects\}.*?)(?=\\section\{[^}]+\}|\\end\{document\}|$)'
    
    # Find the match in the original
    match = re.search(pattern, original_latex, flags=re.DOTALL | re.IGNORECASE)
    
    if match:
        # Get the start and end positions of the match
        start_pos = match.start(1)
        end_pos = match.end(1)
        
        # Replace by reconstructing the string
        result = original_latex[:start_pos] + new_projects_section + original_latex[end_pos:]
        return result
    else:
        # If no Projects section found, return original
        return original_latex

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    from forms import RegistrationForm
    form = RegistrationForm()
    
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            visa_status=form.visa_status.data,
            experience_level=form.experience_level.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    from forms import LoginForm
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            
            # Redirect to next page if specified, otherwise to index
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """User logout route."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management route."""
    from forms import ProfileForm
    form = ProfileForm()
    
    if form.validate_on_submit():
        current_user.visa_status = form.visa_status.data
        current_user.experience_level = form.experience_level.data
        current_user.preferred_locations = form.preferred_locations.data
        current_user.skills = form.skills.data
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    # Pre-populate form with current user data
    if request.method == 'GET':
        form.visa_status.data = current_user.visa_status
        form.experience_level.data = current_user.experience_level
        form.preferred_locations.data = current_user.preferred_locations or []
        form.skills.data = current_user.skills or []
    
    return render_template('auth/profile.html', form=form)

@app.route('/tailor', methods=['GET', 'POST'])
@login_required
def tailor():
    from services.resume_service import ResumeTailoringService
    from models.resume_version import ResumeVersion
    
    tailoring_service = ResumeTailoringService()
    
    if request.method == 'GET':
        # Show the tailoring form with resume version selection
        resume_versions = current_user.resume_versions.all()
        return render_template('tailor_form.html', resume_versions=resume_versions)
    
    # Handle POST request
    resume_version_id = request.form.get('resume_version_id')
    job_description = request.form['job_description']
    
    # Get resume content either from version or direct input
    if resume_version_id:
        resume_version = ResumeVersion.query.filter_by(
            id=resume_version_id,
            user_id=current_user.id
        ).first_or_404()
        resume = resume_version.latex_content
        selected_version = resume_version
    else:
        resume = request.form['resume']
        selected_version = None
    
    # Analyze compatibility
    compatibility = tailoring_service.analyze_compatibility(resume, job_description)
    
    # Suggest best resume version if none was selected
    suggested_version = None
    if not resume_version_id:
        suggested_version = tailoring_service.suggest_resume_version(current_user.id, job_description)
        
        # If we have a better suggestion, use it
        if suggested_version and compatibility.score < 0.5:
            resume = suggested_version.latex_content
            selected_version = suggested_version
            compatibility = tailoring_service.analyze_compatibility(resume, job_description)

    prompt = f"""
You are an expert career coach and professional resume writer specializing in LaTeX resumes. Your task is to edit ONLY the \\section{{Projects}} content in the provided LaTeX resume to make it more ATS-friendly for the given job description.

**CRITICAL INSTRUCTIONS:**

1.  **ONLY EDIT PROJECTS SECTION:** You MUST ONLY modify the content within the \\section{{Projects}} section. Do NOT change ANY other part of the resume including headers, formatting, other sections, LaTeX commands, packages, or document structure.

2.  **Preserve ALL Formatting:** Keep the exact same LaTeX formatting, commands, and structure. Do NOT change \\resumeSubItem, \\resumeSubHeadingListStart, or any other LaTeX commands.

3.  **Projects Content Only:** Only modify the project descriptions and titles within the Projects section to:
    *   Add relevant keywords from the job description
    *   Use strong action verbs (Engineered, Developed, Implemented, etc.)
    *   Include quantifiable metrics where possible
    *   Make descriptions more ATS-friendly

4.  **Keep Everything Else Identical:** Do NOT modify:
    *   Document class or packages
    *   Any other sections (Summary, Education, Experience, Skills, etc.)
    *   LaTeX formatting or commands
    *   Document structure or spacing

5.  **LaTeX Character Handling:** Be careful with special LaTeX characters. Use \\& for ampersands in regular text, \\% for percent signs, and \\$ for dollar signs outside math mode.

6.  **No Comments:** Do NOT add any LaTeX comments. Keep the code clean without any comments.

7.  **Output:** Your response must ONLY be the complete, raw LaTeX code with ONLY the Projects section content modified. Everything else must remain exactly the same.

**Job Description:**
---
{job_description}
---

**Original LaTeX Resume:**
---
{resume}
---
"""

    response = client.models.generate_content(
        model='models/gemini-2.0-flash',
        contents=prompt
    )

    modified_latex = response.text
    
    # Clean up the response - remove markdown code blocks if present
    if modified_latex.startswith('```latex'):
        # Remove the opening ```latex and closing ```
        lines = modified_latex.split('\n')
        if lines[0].strip() == '```latex' or lines[0].strip().startswith('```latex'):
            lines = lines[1:]  # Remove first line
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]  # Remove last line
        modified_latex = '\n'.join(lines)
    elif modified_latex.startswith('```'):
        # Handle generic code blocks
        lines = modified_latex.split('\n')
        if lines[0].strip().startswith('```'):
            lines = lines[1:]  # Remove first line
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]  # Remove last line
        modified_latex = '\n'.join(lines)
    
    # Remove any leading/trailing whitespace
    modified_latex = modified_latex.strip()
    
    # Remove any LaTeX comments that might have been added FIRST
    modified_latex = remove_latex_comments(modified_latex)
    
    # Then fix LaTeX character escaping issues
    modified_latex = fix_latex_characters(modified_latex)

    # Extract only the Projects section from the AI-generated content
    new_projects_section = extract_projects_section(modified_latex)
    
    if new_projects_section:
        # Clean the extracted projects section only
        new_projects_section = remove_latex_comments(new_projects_section)
        new_projects_section = fix_latex_characters(new_projects_section)
        
        # Replace the Projects section in the original resume
        final_latex = replace_projects_section(resume, new_projects_section)
    else:
        # If extraction failed, use the original resume
        final_latex = resume
    
    # Return the LaTeX content for review instead of immediately generating PDF
    return render_template('latex_preview.html', 
                         latex_content=final_latex,
                         original_resume=resume,
                         compatibility=compatibility,
                         selected_version=selected_version,
                         suggested_version=suggested_version)

@app.route('/resume-versions')
@login_required
def resume_versions():
    """Display all resume versions for the current user."""
    versions = current_user.resume_versions.order_by(db.desc(db.text('created_at'))).all()
    return render_template('resume_versions.html', versions=versions)

@app.route('/resume-versions/new', methods=['GET', 'POST'])
@login_required
def new_resume_version():
    """Create a new resume version."""
    from forms import ResumeVersionForm
    from models.resume_version import ResumeVersion
    
    form = ResumeVersionForm()
    
    if form.validate_on_submit():
        # Check if user already has a resume with this name
        existing = ResumeVersion.query.filter_by(
            user_id=current_user.id,
            name=form.name.data
        ).first()
        
        if existing:
            flash('You already have a resume version with this name. Please choose a different name.', 'error')
            return render_template('resume_version_form.html', form=form, title='New Resume Version')
        
        version = ResumeVersion(
            user_id=current_user.id,
            name=form.name.data,
            category=form.category.data,
            latex_content=form.latex_content.data
        )
        
        db.session.add(version)
        db.session.commit()
        
        flash(f'Resume version "{form.name.data}" created successfully!', 'success')
        return redirect(url_for('resume_versions'))
    
    return render_template('resume_version_form.html', form=form, title='New Resume Version')

@app.route('/resume-versions/<int:version_id>')
@login_required
def view_resume_version(version_id):
    """View a specific resume version."""
    from models.resume_version import ResumeVersion
    
    version = ResumeVersion.query.filter_by(
        id=version_id,
        user_id=current_user.id
    ).first_or_404()
    
    return render_template('resume_version_detail.html', version=version)

@app.route('/resume-versions/<int:version_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_resume_version(version_id):
    """Edit an existing resume version."""
    from forms import ResumeVersionForm
    from models.resume_version import ResumeVersion
    
    version = ResumeVersion.query.filter_by(
        id=version_id,
        user_id=current_user.id
    ).first_or_404()
    
    form = ResumeVersionForm()
    
    if form.validate_on_submit():
        # Check if user is trying to rename to an existing name (excluding current version)
        existing = ResumeVersion.query.filter_by(
            user_id=current_user.id,
            name=form.name.data
        ).filter(ResumeVersion.id != version_id).first()
        
        if existing:
            flash('You already have a resume version with this name. Please choose a different name.', 'error')
            return render_template('resume_version_form.html', form=form, title='Edit Resume Version')
        
        version.name = form.name.data
        version.category = form.category.data
        version.latex_content = form.latex_content.data
        
        db.session.commit()
        
        flash(f'Resume version "{form.name.data}" updated successfully!', 'success')
        return redirect(url_for('view_resume_version', version_id=version.id))
    
    # Pre-populate form with current data
    if request.method == 'GET':
        form.name.data = version.name
        form.category.data = version.category
        form.latex_content.data = version.latex_content
    
    return render_template('resume_version_form.html', form=form, title='Edit Resume Version', version=version)

@app.route('/resume-versions/<int:version_id>/delete', methods=['POST'])
@login_required
def delete_resume_version(version_id):
    """Delete a resume version."""
    from models.resume_version import ResumeVersion
    
    version = ResumeVersion.query.filter_by(
        id=version_id,
        user_id=current_user.id
    ).first_or_404()
    
    version_name = version.name
    db.session.delete(version)
    db.session.commit()
    
    flash(f'Resume version "{version_name}" deleted successfully!', 'success')
    return redirect(url_for('resume_versions'))

@app.route('/resume-versions/<int:version_id>/duplicate', methods=['POST'])
@login_required
def duplicate_resume_version(version_id):
    """Duplicate an existing resume version."""
    from models.resume_version import ResumeVersion
    
    original = ResumeVersion.query.filter_by(
        id=version_id,
        user_id=current_user.id
    ).first_or_404()
    
    # Create a unique name for the duplicate
    base_name = f"{original.name} (Copy)"
    duplicate_name = base_name
    counter = 1
    
    while ResumeVersion.query.filter_by(user_id=current_user.id, name=duplicate_name).first():
        duplicate_name = f"{base_name} {counter}"
        counter += 1
    
    duplicate = ResumeVersion(
        user_id=current_user.id,
        name=duplicate_name,
        category=original.category,
        latex_content=original.latex_content
    )
    
    db.session.add(duplicate)
    db.session.commit()
    
    flash(f'Resume version duplicated as "{duplicate_name}"!', 'success')
    return redirect(url_for('resume_versions'))

@app.route('/api/analyze-compatibility', methods=['POST'])
@login_required
def analyze_compatibility():
    """API endpoint for resume-job compatibility analysis."""
    from services.resume_service import ResumeTailoringService
    from models.resume_version import ResumeVersion
    
    data = request.get_json()
    if not data:
        return {'error': 'No data provided'}, 400
    
    job_description = data.get('job_description', '')
    resume_version_id = data.get('resume_version_id')
    resume_content = data.get('resume_content', '')
    
    if not job_description:
        return {'error': 'Job description is required'}, 400
    
    # Get resume content
    if resume_version_id:
        version = ResumeVersion.query.filter_by(
            id=resume_version_id,
            user_id=current_user.id
        ).first()
        if not version:
            return {'error': 'Resume version not found'}, 404
        resume_content = version.latex_content
    elif not resume_content:
        return {'error': 'Resume content or version ID is required'}, 400
    
    # Analyze compatibility
    tailoring_service = ResumeTailoringService()
    compatibility = tailoring_service.analyze_compatibility(resume_content, job_description)
    
    # Get suggested version
    suggested_version = tailoring_service.suggest_resume_version(current_user.id, job_description)
    
    return {
        'compatibility': {
            'score': compatibility.score,
            'matched_keywords': compatibility.matched_keywords,
            'missing_keywords': compatibility.missing_keywords,
            'suggestions': compatibility.suggestions
        },
        'suggested_version': {
            'id': suggested_version.id,
            'name': suggested_version.name,
            'category': suggested_version.category
        } if suggested_version else None
    }

@app.route('/api/resume-versions/<int:version_id>/content')
@login_required
def get_resume_version_content(version_id):
    """API endpoint to get resume version content."""
    from models.resume_version import ResumeVersion
    
    version = ResumeVersion.query.filter_by(
        id=version_id,
        user_id=current_user.id
    ).first_or_404()
    
    return {
        'id': version.id,
        'name': version.name,
        'category': version.category,
        'content': version.latex_content,
        'created_at': version.created_at.isoformat()
    }

@app.route('/generate_pdf', methods=['POST'])
@login_required
def generate_pdf():
    latex_content = request.form['latex_content']
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            tex_filename = "resume.tex"
            tex_filepath = os.path.join(temp_dir, tex_filename)

            with open(tex_filepath, "w", encoding='utf-8') as f:
                f.write(latex_content)

            compile_process = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", temp_dir, tex_filepath],
                capture_output=True,
                text=True
            )

            if compile_process.returncode != 0:
                log_filename = "resume.log"
                log_filepath = os.path.join(temp_dir, log_filename)
                with open(log_filepath, "r") as log_file:
                    log_content = log_file.read()
                
                # Return to preview with error message
                return render_template('latex_preview.html', 
                                     latex_content=latex_content,
                                     error_message="PDF Compilation Failed",
                                     error_log=log_content)

            pdf_filepath = os.path.join(temp_dir, "resume.pdf")

            # Read the generated PDF into a buffer
            with open(pdf_filepath, 'rb') as f:
                pdf_buffer = io.BytesIO(f.read())

            # Seek to the beginning of the buffer
            pdf_buffer.seek(0)

            # Send the buffer as a file download
            return send_file(
                pdf_buffer,
                as_attachment=True,
                download_name='tailored_resume.pdf',
                mimetype='application/pdf'
            )

    except Exception as e:
        return render_template('latex_preview.html', 
                             latex_content=latex_content,
                             error_message="An unexpected error occurred",
                             error_log=str(e))

if __name__ == '__main__':
    # Initialize database on first run
    with app.app_context():
        init_db(app)
        seed_db(app)
    
    app.run(debug=True)