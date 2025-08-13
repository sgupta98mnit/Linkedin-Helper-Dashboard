import os
import subprocess
import tempfile
import io
from flask import Flask, render_template, request, send_file
import google.generativeai as genai

# Configure the Gemini API key
# Make sure to set the GOOGLE_API_KEY environment variable
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tailor', methods=['POST'])
def tailor():
    resume = request.form['resume']
    job_description = request.form['job_description']

    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    prompt = f"""
You are an expert career coach and professional resume writer specializing in LaTeX resumes. Your task is to edit the provided LaTeX resume source code to tailor it for the given job description.

**IMPORTANT INSTRUCTIONS:**

1.  **Edit LaTeX Directly:** You MUST edit the LaTeX source code directly. Do NOT output plain text. The final output should be the complete, modified LaTeX source code, ready for compilation.
2.  **Preserve Structure:** Do not add or remove LaTeX packages, commands, or change the overall document structure unless it's necessary for content flow. Your goal is to improve the *content* within the existing structure.
3.  **ATS-Friendly Content:**
    *   Focus on quantifiable achievements. Use numbers and metrics wherever possible (e.g., "Increased efficiency by 20%" instead of "Improved efficiency").
    *   Integrate keywords from the job description naturally throughout the resume, especially in the 'Skills' and 'Experience' sections.
    *   Use strong, professional action verbs to start bullet points (e.g., "Engineered," "Orchestrated," "Implemented," "Streamlined").
4.  **Natural Language:**
    *   Rewrite sentences to sound human and confident. Avoid overly complex jargon or generic, AI-like phrasing. The tone should be professional yet authentic.
    *   Ensure the summary/objective section is a powerful and concise pitch tailored to the specific role.
5.  **Output:** Your response must ONLY be the raw, updated LaTeX code. Do not include any explanations, apologies, or introductory text like "Here is the updated LaTeX code:".

**Job Description:**
---
{job_description}
---

**Original LaTeX Resume:**
---
{resume}
---
"""

    response = model.generate_content(prompt)

    modified_latex = response.text

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            tex_filename = "resume.tex"
            tex_filepath = os.path.join(temp_dir, tex_filename)

            with open(tex_filepath, "w") as f:
                f.write(modified_latex)

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
                return f"<h1>PDF Compilation Failed</h1><pre>{log_content}</pre>", 500

            pdf_filepath = os.path.join(temp_dir, "resume.pdf")

            # Read the generated PDF into a buffer
            with open(pdf_filepath, 'rb') as f:
                pdf_buffer = io.BytesIO(f.read())

            # The temp_dir will be cleaned up here, but we have the PDF in memory.

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
        return f"<h1>An unexpected error occurred:</h1><pre>{str(e)}</pre>", 500

if __name__ == '__main__':
    app.run(debug=True)
