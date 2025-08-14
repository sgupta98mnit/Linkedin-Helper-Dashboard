"""Resume tailoring and compatibility analysis service."""
import re
from typing import List, Dict, Tuple, Optional
from collections import Counter
from models.resume_version import ResumeVersion
from models.user import User


class CompatibilityScore:
    """Represents the compatibility between a resume and job description."""
    
    def __init__(self, score: float, matched_keywords: List[str], 
                 missing_keywords: List[str], suggestions: List[str]):
        self.score = score  # 0.0 to 1.0
        self.matched_keywords = matched_keywords
        self.missing_keywords = missing_keywords
        self.suggestions = suggestions


class ResumeTailoringService:
    """Service for resume tailoring and compatibility analysis."""
    
    # Common technical keywords by category
    CATEGORY_KEYWORDS = {
        'Engineering': [
            'python', 'java', 'javascript', 'react', 'node.js', 'sql', 'aws', 'docker',
            'kubernetes', 'git', 'api', 'microservices', 'database', 'frontend', 'backend',
            'full-stack', 'agile', 'scrum', 'ci/cd', 'testing', 'debugging'
        ],
        'Data Science': [
            'python', 'r', 'sql', 'machine learning', 'deep learning', 'tensorflow',
            'pytorch', 'pandas', 'numpy', 'scikit-learn', 'statistics', 'data analysis',
            'data visualization', 'tableau', 'power bi', 'jupyter', 'spark', 'hadoop'
        ],
        'Product': [
            'product management', 'roadmap', 'stakeholder', 'user research', 'analytics',
            'a/b testing', 'metrics', 'kpi', 'agile', 'scrum', 'jira', 'wireframes',
            'user experience', 'market research', 'competitive analysis'
        ],
        'Design': [
            'ui/ux', 'figma', 'sketch', 'adobe', 'photoshop', 'illustrator', 'wireframes',
            'prototyping', 'user research', 'design systems', 'responsive design',
            'accessibility', 'user testing', 'visual design', 'interaction design'
        ]
    }
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text."""
        import re
        
        # Convert to lowercase and remove special characters
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # Common technical terms and skills
        keywords = []
        
        # Extract programming languages (using word boundaries for single letters)
        prog_languages = [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
            'php', 'ruby', 'swift', 'kotlin', 'scala', 'matlab'
        ]
        
        # Special handling for single-letter languages
        single_letter_langs = ['r']
        
        # Extract frameworks and libraries
        frameworks = [
            'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask',
            'spring', 'laravel', 'rails', 'tensorflow', 'pytorch', 'pandas', 'numpy'
        ]
        
        # Extract tools and technologies
        tools = [
            'git', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'jenkins', 'jira',
            'confluence', 'slack', 'figma', 'sketch', 'tableau', 'power bi'
        ]
        
        # Extract databases
        databases = ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch']
        
        # Combine all keyword lists (excluding single letter languages)
        all_keywords = prog_languages + frameworks + tools + databases
        
        # Find keywords in text
        for keyword in all_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        # Handle single-letter programming languages with word boundaries
        for lang in single_letter_langs:
            if re.search(r'\b' + lang + r'\b', text):
                keywords.append(lang)
        
        # Extract multi-word technical terms
        multi_word_terms = [
            'machine learning', 'deep learning', 'data science', 'data analysis',
            'software engineering', 'full stack', 'front end', 'back end',
            'user experience', 'user interface', 'product management', 'project management',
            'agile development', 'test driven development', 'continuous integration',
            'continuous deployment', 'cloud computing', 'artificial intelligence'
        ]
        
        for term in multi_word_terms:
            if term in text:
                keywords.append(term)
        
        return list(set(keywords))  # Remove duplicates
    
    def analyze_compatibility(self, resume_content: str, job_description: str) -> CompatibilityScore:
        """Analyze compatibility between resume and job description."""
        resume_keywords = set(self.extract_keywords(resume_content))
        job_keywords = set(self.extract_keywords(job_description))
        
        # Find matched and missing keywords
        matched_keywords = list(resume_keywords.intersection(job_keywords))
        missing_keywords = list(job_keywords - resume_keywords)
        
        # Calculate compatibility score
        if not job_keywords:
            score = 0.0
        else:
            score = len(matched_keywords) / len(job_keywords)
        
        # Generate suggestions
        suggestions = []
        if missing_keywords:
            suggestions.append(f"Consider adding these skills to your resume: {', '.join(missing_keywords[:5])}")
        
        if score < 0.3:
            suggestions.append("Your resume has low compatibility with this job. Consider using a different resume version or adding more relevant experience.")
        elif score < 0.6:
            suggestions.append("Your resume has moderate compatibility. Consider emphasizing relevant projects and skills.")
        else:
            suggestions.append("Your resume has good compatibility with this job!")
        
        return CompatibilityScore(score, matched_keywords, missing_keywords, suggestions)
    
    def suggest_resume_version(self, user_id: int, job_description: str) -> Optional[ResumeVersion]:
        """Suggest the best resume version for a job based on compatibility."""
        user = User.query.get(user_id)
        if not user or not user.resume_versions:
            return None
        
        best_version = None
        best_score = 0.0
        
        for version in user.resume_versions:
            compatibility = self.analyze_compatibility(version.latex_content, job_description)
            if compatibility.score > best_score:
                best_score = compatibility.score
                best_version = version
        
        return best_version
    
    def get_category_from_job_description(self, job_description: str) -> str:
        """Determine job category from job description."""
        job_text = job_description.lower()
        
        # Check for specific role indicators first
        if any(term in job_text for term in ['software engineer', 'developer', 'programming']):
            return 'Engineering'
        elif any(term in job_text for term in ['data scientist', 'machine learning', 'analytics']):
            return 'Data Science'
        elif any(term in job_text for term in ['product manager', 'product']):
            return 'Product'
        elif any(term in job_text for term in ['designer', 'ui/ux', 'design']):
            return 'Design'
        
        # Fallback to keyword scoring with word boundaries
        import re
        category_scores = {}
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                # Use word boundaries for single-letter keywords, regular search for others
                if len(keyword) == 1:
                    if re.search(r'\b' + re.escape(keyword) + r'\b', job_text):
                        score += 1
                else:
                    if keyword in job_text:
                        score += 1
            category_scores[category] = score
        
        # Return category with highest score, or 'Other' if no clear match
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            if category_scores[best_category] > 0:
                return best_category
        
        return 'Other'
    
    def get_resume_versions_by_category(self, user_id: int, category: str) -> List[ResumeVersion]:
        """Get resume versions filtered by category."""
        user = User.query.get(user_id)
        if not user:
            return []
        
        return [v for v in user.resume_versions if v.category == category]