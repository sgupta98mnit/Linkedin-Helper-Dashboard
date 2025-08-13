import os
from flask import Flask, render_template, request
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
    You are an expert resume writer. Rewrite the following resume to be tailored for the given job description.
    Make sure to highlight the skills and experiences that are most relevant to the job.
    Output the result in a professional resume format.

    Resume:
    {resume}

    Job Description:
    {job_description}
    """

    response = model.generate_content(prompt)

    return render_template('result.html', tailored_resume=response.text)

if __name__ == '__main__':
    app.run(debug=True)
