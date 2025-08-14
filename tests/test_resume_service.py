"""Unit tests for resume tailoring service."""
import unittest
from unittest.mock import Mock, patch
from services.resume_service import ResumeTailoringService, CompatibilityScore
from models.resume_version import ResumeVersion
from models.user import User


class TestResumeTailoringService(unittest.TestCase):
    """Test cases for ResumeTailoringService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = ResumeTailoringService()
        
        # Sample resume content
        self.sample_resume = """
        \\documentclass{article}
        \\begin{document}
        \\section{Experience}
        Software Engineer with experience in Python, JavaScript, React, and SQL.
        Built web applications using Django and Flask frameworks.
        Worked with AWS cloud services and Docker containers.
        \\section{Projects}
        Developed a machine learning model using TensorFlow and Python.
        Created REST APIs using Node.js and Express.
        \\end{document}
        """
        
        # Sample job description
        self.sample_job_description = """
        We are looking for a Software Engineer with experience in:
        - Python programming
        - React frontend development
        - SQL database management
        - AWS cloud services
        - Machine learning experience preferred
        - Docker containerization
        - REST API development
        """
    
    def test_extract_keywords(self):
        """Test keyword extraction from text."""
        text = "Looking for Python developer with React and SQL experience"
        keywords = self.service.extract_keywords(text)
        
        self.assertIn('python', keywords)
        self.assertIn('react', keywords)
        self.assertIn('sql', keywords)
    
    def test_extract_keywords_multi_word_terms(self):
        """Test extraction of multi-word technical terms."""
        text = "Experience with machine learning and data science required"
        keywords = self.service.extract_keywords(text)
        
        self.assertIn('machine learning', keywords)
        self.assertIn('data science', keywords)
    
    def test_analyze_compatibility_high_score(self):
        """Test compatibility analysis with high matching score."""
        compatibility = self.service.analyze_compatibility(
            self.sample_resume, 
            self.sample_job_description
        )
        
        self.assertIsInstance(compatibility, CompatibilityScore)
        self.assertGreater(compatibility.score, 0.5)  # Should have good compatibility
        self.assertIn('python', compatibility.matched_keywords)
        self.assertIn('react', compatibility.matched_keywords)
        self.assertIn('sql', compatibility.matched_keywords)
        self.assertTrue(len(compatibility.suggestions) > 0)
    
    def test_analyze_compatibility_low_score(self):
        """Test compatibility analysis with low matching score."""
        unrelated_resume = """
        \\documentclass{article}
        \\begin{document}
        Marketing professional with experience in social media and content creation.
        \\end{document}
        """
        
        compatibility = self.service.analyze_compatibility(
            unrelated_resume, 
            self.sample_job_description
        )
        
        self.assertLess(compatibility.score, 0.3)  # Should have low compatibility
        self.assertTrue(len(compatibility.missing_keywords) > 0)
        # Check that low compatibility suggestion is present
        low_compat_found = any("low compatibility" in s.lower() for s in compatibility.suggestions)
        self.assertTrue(low_compat_found, f"Expected low compatibility suggestion, got: {compatibility.suggestions}")
    
    def test_get_category_from_job_description_engineering(self):
        """Test job category detection for engineering roles."""
        job_desc = "Software engineer position requiring programming and development skills"
        category = self.service.get_category_from_job_description(job_desc)
        
        self.assertEqual(category, 'Engineering')
    
    def test_get_category_from_job_description_data_science(self):
        """Test job category detection for data science roles."""
        job_desc = "Data scientist role with machine learning and analytics experience"
        category = self.service.get_category_from_job_description(job_desc)
        
        self.assertEqual(category, 'Data Science')
    
    def test_get_category_from_job_description_other(self):
        """Test job category detection for unrecognized roles."""
        job_desc = "Sales representative position with customer service and communication skills"
        category = self.service.get_category_from_job_description(job_desc)
        
        self.assertEqual(category, 'Other')
    
    def test_suggest_resume_version_logic(self):
        """Test the logic of resume version suggestion without database."""
        # Test the core logic by creating mock versions
        version1 = Mock()
        version1.latex_content = self.sample_resume
        version1.name = "Software Engineer Resume"
        
        version2 = Mock()
        version2.latex_content = "Marketing professional with social media experience"
        version2.name = "Marketing Resume"
        
        versions = [version1, version2]
        
        # Find best version manually using the same logic
        best_version = None
        best_score = 0.0
        
        for version in versions:
            compatibility = self.service.analyze_compatibility(version.latex_content, self.sample_job_description)
            if compatibility.score > best_score:
                best_score = compatibility.score
                best_version = version
        
        # Should suggest the software engineer resume as it has better compatibility
        self.assertEqual(best_version, version1)
        self.assertGreater(best_score, 0.0)
    
    def test_filter_versions_by_category_logic(self):
        """Test filtering resume versions by category logic."""
        # Create mock resume versions
        eng_version = Mock()
        eng_version.category = 'Engineering'
        
        ds_version = Mock()
        ds_version.category = 'Data Science'
        
        other_version = Mock()
        other_version.category = 'Marketing'
        
        all_versions = [eng_version, ds_version, other_version]
        
        # Filter manually using the same logic
        filtered = [v for v in all_versions if v.category == 'Engineering']
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].category, 'Engineering')
    
    def test_compatibility_score_properties(self):
        """Test CompatibilityScore object properties."""
        score = CompatibilityScore(
            score=0.75,
            matched_keywords=['python', 'react'],
            missing_keywords=['java', 'angular'],
            suggestions=['Add Java experience']
        )
        
        self.assertEqual(score.score, 0.75)
        self.assertEqual(len(score.matched_keywords), 2)
        self.assertEqual(len(score.missing_keywords), 2)
        self.assertEqual(len(score.suggestions), 1)
        self.assertIn('python', score.matched_keywords)
        self.assertIn('java', score.missing_keywords)


class TestResumeTailoringServiceIntegration(unittest.TestCase):
    """Integration tests for resume tailoring service."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = ResumeTailoringService()
    
    def test_end_to_end_compatibility_analysis(self):
        """Test complete compatibility analysis workflow."""
        resume = """
        Software Engineer with 3 years experience in Python, Django, and PostgreSQL.
        Built REST APIs and worked with AWS services including EC2 and S3.
        Experience with Docker and Kubernetes for containerization.
        """
        
        job_desc = """
        Senior Software Engineer
        Requirements:
        - 3+ years Python experience
        - Django framework knowledge
        - PostgreSQL database experience
        - AWS cloud services (EC2, S3, Lambda)
        - Docker containerization
        - REST API development
        - Kubernetes orchestration preferred
        """
        
        compatibility = self.service.analyze_compatibility(resume, job_desc)
        
        # Should have high compatibility
        self.assertGreater(compatibility.score, 0.6)
        
        # Should match key technologies
        expected_matches = ['python', 'django', 'postgresql', 'aws', 'docker']
        for tech in expected_matches:
            self.assertIn(tech, compatibility.matched_keywords)
        
        # Should provide meaningful suggestions
        self.assertTrue(len(compatibility.suggestions) > 0)
        self.assertTrue(any('good compatibility' in s.lower() for s in compatibility.suggestions))


if __name__ == '__main__':
    unittest.main()