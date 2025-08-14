import io
from flask import render_template, request, send_file
from app.main import main
from app.services import tailor_resume_service

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/tailor', methods=['POST'])
def tailor():
    resume = request.form.get('resume')
    job_description = request.form.get('job_description')

    if not resume or not job_description:
        return "Missing resume or job description", 400

    try:
        pdf_buffer = tailor_resume_service(resume, job_description)
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name='tailored_resume.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        return f"<h1>An error occurred:</h1><pre>{str(e)}</pre>", 500
