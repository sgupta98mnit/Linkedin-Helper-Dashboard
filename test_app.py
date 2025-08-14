import unittest
import os
import google.generativeai as genai
from app import create_app

class TailorTestCase(unittest.TestCase):

    def setUp(self):
        print("Starting setUp...")
        # Set the API key for the test environment
        api_key = 'AIzaSyBPSib0097zkkagb4yVwWwh6RLy_1IDGP8'

        print("Configuring Gemini...")
        genai.configure(api_key=api_key)
        print("Gemini configured.")

        print("Creating app...")
        self.app = create_app()
        self.app.config.update({
            "TESTING": True,
        })
        print("App created.")

        self.client = self.app.test_client()
        print("Test client created.")

    def test_tailor_endpoint(self):
        print("Starting test_tailor_endpoint...")
        # Sample LaTeX resume
        latex_resume = r"""
\documentclass{article}
\author{John Doe}
\title{Resume}
\date{}
\begin{document}
\maketitle
\section*{Summary}
A highly motivated software engineer with 3+ years of experience in Python and web development.
\end{document}
"""
        # Sample job description
        job_description = "We are looking for a Python Developer."

        # Send a POST request to the tailor endpoint
        print("Sending POST request to /tailor...")
        response = self.client.post('/tailor', data={
            'resume': latex_resume,
            'job_description': job_description
        })

        # Assertions
        print(f"Response status code: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        print(f"Response mimetype: {response.mimetype}")
        self.assertEqual(response.mimetype, 'application/pdf')
        print(f"Content-Disposition header: {response.headers['Content-Disposition']}")
        self.assertIn('attachment', response.headers['Content-Disposition'])

        print("Checking PDF content...")
        self.assertTrue(response.data.startswith(b'%PDF-'))
        print("Test passed!")

if __name__ == '__main__':
    unittest.main()
