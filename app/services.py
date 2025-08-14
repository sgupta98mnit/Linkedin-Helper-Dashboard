import os
import subprocess
import tempfile
import io
import google.generativeai as genai
from flask import current_app
import datetime

def log_message(message):
    with open("debug.log", "a") as f:
        f.write(f"[{datetime.datetime.now()}] {message}\n")

def tailor_resume_service(resume, job_description):
    log_message("Entered tailor_resume_service.")
    model_name = current_app.config['GEMINI_MODEL']
    model = genai.GenerativeModel(model_name)

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
    log_message("Calling Gemini API...")
    response = model.generate_content(prompt)
    log_message("Gemini API call complete.")
    modified_latex = response.text

    with tempfile.TemporaryDirectory() as temp_dir:
        tex_filepath = os.path.join(temp_dir, "resume.tex")

        with open(tex_filepath, "w") as f:
            f.write(modified_latex)

        log_message("Calling pdflatex...")
        compile_process = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", temp_dir, tex_filepath],
            capture_output=True,
            text=True
        )
        log_message("pdflatex call complete.")

        if compile_process.returncode != 0:
            log_filepath = os.path.join(temp_dir, "resume.log")
            log_content = "Could not read log file."
            if os.path.exists(log_filepath):
                with open(log_filepath, "r") as log_file:
                    log_content = log_file.read()
            raise Exception(f"PDF Compilation Failed:\n{log_content}")

        pdf_filepath = os.path.join(temp_dir, "resume.pdf")

        with open(pdf_filepath, 'rb') as f:
            pdf_buffer = io.BytesIO(f.read())

        pdf_buffer.seek(0)
        log_message("Service finished successfully.")
        return pdf_buffer
