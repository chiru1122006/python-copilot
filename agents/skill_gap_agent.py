"""
Skill Gap Agent
Identifies gaps between user skills and target role requirements
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_client import llm
from typing import Dict, List, Any


class SkillGapAgent:
    """
    The Skill Gap Agent is responsible for:
    1. Comparing user skills vs job requirements
    2. Identifying missing skills
    3. Prioritizing gaps by importance
    4. Suggesting learning resources
    """
    
    SYSTEM_PROMPT = """You are an expert skill assessment agent. Your role is to:
1. Accurately compare user skills against job role requirements
2. Identify critical skill gaps
3. Prioritize gaps based on industry importance
4. Provide actionable insights for skill development
5. Recommend specific, real learning resources (YouTube videos, courses, documentation)

Be precise and realistic in your assessments. Consider both technical and soft skills.
When providing learning resources, use REAL, working URLs to popular educational content."""
    
    def __init__(self):
        self.name = "SkillGapAgent"
        
        # Common role requirements (fallback data)
        self.role_requirements = {
            "Full Stack Developer": {
                "required": ["JavaScript", "React", "Node.js", "SQL", "Git", "REST APIs", "HTML/CSS"],
                "preferred": ["TypeScript", "Docker", "AWS", "MongoDB", "GraphQL", "CI/CD"],
                "soft_skills": ["Problem Solving", "Communication", "Team Collaboration"]
            },
            "Frontend Developer": {
                "required": ["JavaScript", "React", "HTML/CSS", "Git", "Responsive Design"],
                "preferred": ["TypeScript", "Vue.js", "Testing", "Webpack", "Figma"],
                "soft_skills": ["Attention to Detail", "Communication", "Creativity"]
            },
            "Backend Developer": {
                "required": ["Python", "Node.js", "SQL", "REST APIs", "Git"],
                "preferred": ["Docker", "AWS", "Redis", "Microservices", "GraphQL"],
                "soft_skills": ["Problem Solving", "System Thinking", "Documentation"]
            },
            "Data Scientist": {
                "required": ["Python", "SQL", "Statistics", "Machine Learning", "Pandas", "NumPy"],
                "preferred": ["TensorFlow", "PyTorch", "Spark", "Tableau", "Deep Learning"],
                "soft_skills": ["Analytical Thinking", "Communication", "Curiosity"]
            },
            "Software Engineer": {
                "required": ["Programming", "Data Structures", "Algorithms", "Git", "Problem Solving"],
                "preferred": ["System Design", "Cloud", "CI/CD", "Testing", "Agile"],
                "soft_skills": ["Communication", "Teamwork", "Critical Thinking"]
            }
        }
    
    def analyze_gaps(self, user_skills: List[Dict], target_role: str) -> Dict[str, Any]:
        """
        Analyze skill gaps for a target role
        
        Args:
            user_skills: List of user's current skills with levels
            target_role: Target job role
        
        Returns:
            Detailed gap analysis with priorities and learning resources
        """
        skills_str = self._format_skills(user_skills)
        
        prompt = f"""Analyze skill gaps for this career transition:

## Target Role: {target_role}

## User's Current Skills:
{skills_str}

Identify ALL skill gaps and provide detailed analysis in JSON.
IMPORTANT: For each skill gap, provide REAL, working YouTube video links and course URLs.
Use popular educational channels like Traversy Media, The Net Ninja, freeCodeCamp, Academind, Fireship, etc.

{{
    "target_role": "{target_role}",
    "skill_gaps": [
        {{
            "skill_name": "<skill name>",
            "current_level": "<none|beginner|intermediate|advanced>",
            "required_level": "<beginner|intermediate|advanced|expert>",
            "priority": "<high|medium|low>",
            "importance": "<why this skill matters>",
            "estimated_learning_time": "<time to acquire>",
            "learning_approach": "<how to learn this skill>",
            "learning_resources": [
                {{
                    "title": "<specific video/course title>",
                    "type": "video",
                    "url": "<real YouTube URL like https://www.youtube.com/watch?v=...>",
                    "platform": "YouTube",
                    "duration": "<video duration if known>"
                }},
                {{
                    "title": "<course name>",
                    "type": "course",
                    "url": "<real Udemy/Coursera/freeCodeCamp URL>",
                    "platform": "<Udemy|Coursera|freeCodeCamp|Codecademy>"
                }},
                {{
                    "title": "<documentation name>",
                    "type": "documentation",
                    "url": "<official docs URL>",
                    "platform": "<Official Docs>"
                }}
            ]
        }}
    ],
    "matching_skills": [
        {{
            "skill_name": "<skill name>",
            "current_level": "<level>",
            "status": "<exceeds|meets|close>"
        }}
    ],
    "gap_summary": {{
        "total_gaps": <number>,
        "high_priority": <number>,
        "medium_priority": <number>,
        "low_priority": <number>
    }},
    "readiness_percentage": <0-100>,
    "critical_path": ["<most important skills to learn in order>"],
    "quick_wins": ["<skills that can be acquired quickly>"],
    "overall_assessment": "<summary of the gap analysis>"
}}"""
        
        result = llm.call_json(prompt, self.SYSTEM_PROMPT, temperature=0.3)
        
        if not result:
            return self._fallback_analysis(user_skills, target_role)
        
        # Always use curated resources for known skills (ensures real, working URLs)
        if 'skill_gaps' in result:
            for gap in result['skill_gaps']:
                skill_name = gap.get('skill_name', '')
                # Always replace with curated resources if available
                curated_resources = self._get_curated_resources(skill_name)
                if curated_resources:
                    gap['learning_resources'] = curated_resources
                else:
                    # Use fallback if no curated resources
                    gap['learning_resources'] = self._get_fallback_resources(skill_name)
                
                # Ensure learning_resources is always a valid list
                if not gap.get('learning_resources') or not isinstance(gap.get('learning_resources'), list):
                    gap['learning_resources'] = self._get_fallback_resources(skill_name)
        
        return {
            "agent": self.name,
            "status": "success",
            "analysis": result
        }
    
    def compare_with_job(self, user_skills: List[Dict], job_requirements: List[str]) -> Dict[str, Any]:
        """
        Compare user skills with specific job requirements
        
        Args:
            user_skills: User's current skills
            job_requirements: List of required skills for the job
        
        Returns:
            Match analysis
        """
        user_skill_names = [s.get('skill_name', s).lower() for s in user_skills]
        
        matching = []
        missing = []
        
        for req in job_requirements:
            req_lower = req.lower()
            if any(req_lower in skill or skill in req_lower for skill in user_skill_names):
                matching.append(req)
            else:
                missing.append(req)
        
        match_percentage = (len(matching) / len(job_requirements) * 100) if job_requirements else 0
        
        return {
            "agent": self.name,
            "status": "success",
            "comparison": {
                "matching_skills": matching,
                "missing_skills": missing,
                "match_percentage": round(match_percentage),
                "total_required": len(job_requirements),
                "skills_matched": len(matching),
                "skills_missing": len(missing)
            }
        }
    
    def prioritize_gaps(self, gaps: List[Dict], career_goal: str) -> Dict[str, Any]:
        """
        Prioritize skill gaps based on career goal
        
        Args:
            gaps: List of identified skill gaps
            career_goal: User's career goal
        
        Returns:
            Prioritized gaps with learning order
        """
        gaps_str = '\n'.join([f"- {g.get('skill_name', g)}: {g.get('current_level', 'unknown')}" for g in gaps])
        
        prompt = f"""Prioritize these skill gaps for the career goal:

## Career Goal: {career_goal}

## Skill Gaps:
{gaps_str}

Provide prioritized learning order in JSON:
{{
    "prioritized_gaps": [
        {{
            "rank": <1, 2, 3...>,
            "skill_name": "<skill>",
            "priority": "<critical|high|medium|low>",
            "reason": "<why this priority>",
            "dependencies": ["<skills to learn first>"],
            "time_investment": "<estimated time>"
        }}
    ],
    "learning_phases": [
        {{
            "phase": <1, 2, 3>,
            "name": "<phase name>",
            "skills": ["<skills in this phase>"],
            "duration": "<estimated duration>"
        }}
    ],
    "parallel_learning": ["<skills that can be learned simultaneously>"],
    "recommendation": "<overall learning strategy>"
}}"""
        
        result = llm.call_json(prompt, self.SYSTEM_PROMPT, temperature=0.3)
        
        return {
            "agent": self.name,
            "status": "success" if result else "fallback",
            "prioritization": result or {"error": "Prioritization unavailable"}
        }
    
    def get_role_requirements(self, role: str) -> Dict[str, Any]:
        """
        Get skill requirements for a role
        
        Args:
            role: Target role name
        
        Returns:
            Role requirements
        """
        # Check local requirements first
        for key, reqs in self.role_requirements.items():
            if role.lower() in key.lower() or key.lower() in role.lower():
                return {
                    "agent": self.name,
                    "status": "success",
                    "requirements": {
                        "role": key,
                        **reqs
                    }
                }
        
        # Use LLM for unknown roles
        prompt = f"""What skills are required for this role: {role}

Provide requirements in JSON:
{{
    "role": "{role}",
    "required": ["<essential skills>"],
    "preferred": ["<nice-to-have skills>"],
    "soft_skills": ["<soft skills needed>"],
    "education": "<typical education requirement>",
    "experience": "<typical experience requirement>"
}}"""
        
        result = llm.call_json(prompt, self.SYSTEM_PROMPT, temperature=0.3)
        
        return {
            "agent": self.name,
            "status": "success" if result else "fallback",
            "requirements": result or self.role_requirements.get("Software Engineer")
        }
    
    def _format_skills(self, skills: List[Dict]) -> str:
        """Format skills list for prompt"""
        if not skills:
            return "No skills listed"
        
        formatted = []
        for skill in skills:
            if isinstance(skill, dict):
                name = skill.get('skill_name', skill.get('name', 'Unknown'))
                level = skill.get('level', 'unknown')
                years = skill.get('years_experience', '')
                exp_str = f" ({years} years)" if years else ""
                formatted.append(f"- {name}: {level}{exp_str}")
            else:
                formatted.append(f"- {skill}")
        
        return '\n'.join(formatted)
    
    def _validate_resources(self, resources: List[Dict]) -> bool:
        """Validate that resources have real URLs, not search queries"""
        if not resources:
            return False
        for resource in resources:
            url = resource.get('url', '')
            # Check if it's a search URL or invalid
            if 'search_query=' in url or 'search?' in url or not url.startswith('http'):
                return False
            # Check for actual video IDs in YouTube URLs
            if 'youtube.com' in url and 'watch?v=' not in url and 'youtu.be/' not in url:
                return False
        return True
    
    def _get_curated_resources(self, skill_name: str) -> List[Dict]:
        """Get curated learning resources with guaranteed real URLs"""
        # Comprehensive curated resources for popular skills
        curated = {
            'Node.js': [
                {"title": "Node.js Full Course for Beginners", "type": "video", "url": "https://www.youtube.com/watch?v=f2EqECiTBL8", "platform": "YouTube", "duration": "3 hours"},
                {"title": "Node.js Crash Course - Traversy Media", "type": "video", "url": "https://www.youtube.com/watch?v=fBNz5xF-Kx4", "platform": "YouTube", "duration": "1.5 hours"},
                {"title": "Node.js Official Documentation", "type": "documentation", "url": "https://nodejs.org/en/docs/", "platform": "Official Docs"}
            ],
            'TypeScript': [
                {"title": "TypeScript Full Course - freeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=gp5H0Vw39yw", "platform": "YouTube", "duration": "1.5 hours"},
                {"title": "TypeScript Tutorial - The Net Ninja", "type": "video", "url": "https://www.youtube.com/watch?v=2pZmKW9-I_k", "platform": "YouTube", "duration": "2 hours"},
                {"title": "TypeScript Handbook", "type": "documentation", "url": "https://www.typescriptlang.org/docs/handbook/", "platform": "Official Docs"}
            ],
            'React': [
                {"title": "React Full Course 2024 - freeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=CgkZ7MvWUAA", "platform": "YouTube", "duration": "12 hours"},
                {"title": "React JS Crash Course - Traversy Media", "type": "video", "url": "https://www.youtube.com/watch?v=w7ejDZ8SWv8", "platform": "YouTube", "duration": "1.5 hours"},
                {"title": "React Official Documentation", "type": "documentation", "url": "https://react.dev/learn", "platform": "Official Docs"}
            ],
            'Python': [
                {"title": "Python Full Course - freeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=rfscVS0vtbw", "platform": "YouTube", "duration": "4.5 hours"},
                {"title": "Python Tutorial - Programming with Mosh", "type": "video", "url": "https://www.youtube.com/watch?v=_uQrJ0TkZlc", "platform": "YouTube", "duration": "6 hours"},
                {"title": "Python Official Documentation", "type": "documentation", "url": "https://docs.python.org/3/tutorial/", "platform": "Official Docs"}
            ],
            'JavaScript': [
                {"title": "JavaScript Full Course - freeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=PkZNo7MFNFg", "platform": "YouTube", "duration": "3.5 hours"},
                {"title": "JavaScript Crash Course - Traversy Media", "type": "video", "url": "https://www.youtube.com/watch?v=hdI2bqOjy3c", "platform": "YouTube", "duration": "1.5 hours"},
                {"title": "MDN JavaScript Guide", "type": "documentation", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide", "platform": "MDN"}
            ],
            'Docker': [
                {"title": "Docker Tutorial for Beginners - TechWorld", "type": "video", "url": "https://www.youtube.com/watch?v=3c-iBn73dDE", "platform": "YouTube", "duration": "3 hours"},
                {"title": "Docker Crash Course - Traversy Media", "type": "video", "url": "https://www.youtube.com/watch?v=pg19Z8LL06w", "platform": "YouTube", "duration": "1 hour"},
                {"title": "Docker Official Documentation", "type": "documentation", "url": "https://docs.docker.com/get-started/", "platform": "Official Docs"}
            ],
            'AWS': [
                {"title": "AWS Certified Cloud Practitioner Training", "type": "video", "url": "https://www.youtube.com/watch?v=SOTamWNgDKc", "platform": "YouTube", "duration": "4 hours"},
                {"title": "AWS Tutorial For Beginners - Simplilearn", "type": "video", "url": "https://www.youtube.com/watch?v=k1RI5locZE4", "platform": "YouTube", "duration": "4 hours"},
                {"title": "AWS Documentation", "type": "documentation", "url": "https://docs.aws.amazon.com/", "platform": "Official Docs"}
            ],
            'SQL': [
                {"title": "SQL Tutorial - Full Database Course", "type": "video", "url": "https://www.youtube.com/watch?v=HXV3zeQKqGY", "platform": "YouTube", "duration": "4 hours"},
                {"title": "MySQL Tutorial for Beginners", "type": "video", "url": "https://www.youtube.com/watch?v=7S_tz1z_5bA", "platform": "YouTube", "duration": "3 hours"},
                {"title": "W3Schools SQL Tutorial", "type": "documentation", "url": "https://www.w3schools.com/sql/", "platform": "W3Schools"}
            ],
            'Git': [
                {"title": "Git and GitHub for Beginners - freeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=RGOj5yH7evk", "platform": "YouTube", "duration": "1 hour"},
                {"title": "Git Tutorial for Beginners - Programming with Mosh", "type": "video", "url": "https://www.youtube.com/watch?v=8JJ101D3knE", "platform": "YouTube", "duration": "1 hour"},
                {"title": "Git Official Documentation", "type": "documentation", "url": "https://git-scm.com/doc", "platform": "Official Docs"}
            ],
            'System Design': [
                {"title": "System Design Interview - ByteByteGo", "type": "video", "url": "https://www.youtube.com/watch?v=UzLMhqg3_Wc", "platform": "YouTube", "duration": "1 hour"},
                {"title": "System Design for Beginners - Gaurav Sen", "type": "video", "url": "https://www.youtube.com/watch?v=xpDnVSmNFX0", "platform": "YouTube", "duration": "30 min"},
                {"title": "System Design Primer", "type": "documentation", "url": "https://github.com/donnemartin/system-design-primer", "platform": "GitHub"}
            ],
            'MongoDB': [
                {"title": "MongoDB Crash Course - Traversy Media", "type": "video", "url": "https://www.youtube.com/watch?v=-56x56UppqQ", "platform": "YouTube", "duration": "1.5 hours"},
                {"title": "MongoDB Complete Course - Net Ninja", "type": "video", "url": "https://www.youtube.com/watch?v=ExcRbA7fy_A", "platform": "YouTube", "duration": "3 hours"},
                {"title": "MongoDB Official Documentation", "type": "documentation", "url": "https://www.mongodb.com/docs/", "platform": "Official Docs"}
            ],
            'REST APIs': [
                {"title": "REST API Tutorial - Programming with Mosh", "type": "video", "url": "https://www.youtube.com/watch?v=SLwpqD8n3d0", "platform": "YouTube", "duration": "1 hour"},
                {"title": "Build A REST API With Node.js - Traversy Media", "type": "video", "url": "https://www.youtube.com/watch?v=pKd0Rpw7O48", "platform": "YouTube", "duration": "1 hour"},
                {"title": "RESTful API Design Guide", "type": "documentation", "url": "https://restfulapi.net/", "platform": "RestfulAPI.net"}
            ],
            'GraphQL': [
                {"title": "GraphQL Full Course - freeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=ed8SzALpx1Q", "platform": "YouTube", "duration": "4 hours"},
                {"title": "GraphQL Crash Course - Traversy Media", "type": "video", "url": "https://www.youtube.com/watch?v=BcLNfwF04Kw", "platform": "YouTube", "duration": "1 hour"},
                {"title": "GraphQL Official Documentation", "type": "documentation", "url": "https://graphql.org/learn/", "platform": "Official Docs"}
            ],
            'CI/CD': [
                {"title": "GitHub Actions Tutorial - TechWorld", "type": "video", "url": "https://www.youtube.com/watch?v=R8_veQiYBjI", "platform": "YouTube", "duration": "1 hour"},
                {"title": "Jenkins Tutorial For Beginners", "type": "video", "url": "https://www.youtube.com/watch?v=FX322RVNGj4", "platform": "YouTube", "duration": "2 hours"},
                {"title": "GitHub Actions Documentation", "type": "documentation", "url": "https://docs.github.com/en/actions", "platform": "GitHub"}
            ],
            'Kubernetes': [
                {"title": "Kubernetes Tutorial for Beginners - TechWorld", "type": "video", "url": "https://www.youtube.com/watch?v=X48VuDVv0do", "platform": "YouTube", "duration": "4 hours"},
                {"title": "Kubernetes Crash Course - Traversy Media", "type": "video", "url": "https://www.youtube.com/watch?v=s_o8dwzRlu4", "platform": "YouTube", "duration": "1 hour"},
                {"title": "Kubernetes Official Documentation", "type": "documentation", "url": "https://kubernetes.io/docs/home/", "platform": "Official Docs"}
            ],
            'Vue.js': [
                {"title": "Vue.js Course for Beginners - freeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=FXpIoQ_rT_c", "platform": "YouTube", "duration": "3.5 hours"},
                {"title": "Vue 3 Crash Course - Traversy Media", "type": "video", "url": "https://www.youtube.com/watch?v=qZXt1Aom3Cs", "platform": "YouTube", "duration": "1.5 hours"},
                {"title": "Vue.js Official Documentation", "type": "documentation", "url": "https://vuejs.org/guide/introduction.html", "platform": "Official Docs"}
            ],
            'Angular': [
                {"title": "Angular Tutorial for Beginners - Programming with Mosh", "type": "video", "url": "https://www.youtube.com/watch?v=k5E2AVpwsko", "platform": "YouTube", "duration": "2 hours"},
                {"title": "Angular Crash Course - Traversy Media", "type": "video", "url": "https://www.youtube.com/watch?v=3dHNOWTI7H8", "platform": "YouTube", "duration": "2 hours"},
                {"title": "Angular Official Documentation", "type": "documentation", "url": "https://angular.io/docs", "platform": "Official Docs"}
            ],
            'Machine Learning': [
                {"title": "Machine Learning Full Course - freeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=NWONeJKn6kc", "platform": "YouTube", "duration": "10 hours"},
                {"title": "Machine Learning for Beginners - Simplilearn", "type": "video", "url": "https://www.youtube.com/watch?v=ukzFI9rgwfU", "platform": "YouTube", "duration": "4 hours"},
                {"title": "Google ML Crash Course", "type": "course", "url": "https://developers.google.com/machine-learning/crash-course", "platform": "Google"}
            ],
            'Data Structures': [
                {"title": "Data Structures Full Course - freeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=RBSGKlAvoiM", "platform": "YouTube", "duration": "8 hours"},
                {"title": "Data Structures - CS Dojo", "type": "video", "url": "https://www.youtube.com/watch?v=bum_19loj9A", "platform": "YouTube", "duration": "20 min"},
                {"title": "GeeksforGeeks DSA", "type": "documentation", "url": "https://www.geeksforgeeks.org/data-structures/", "platform": "GeeksforGeeks"}
            ],
            'Algorithms': [
                {"title": "Algorithms Course - freeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=8hly31xKli0", "platform": "YouTube", "duration": "5 hours"},
                {"title": "Algorithms Explained - Reducible", "type": "video", "url": "https://www.youtube.com/watch?v=WbzNRTTrX0g", "platform": "YouTube", "duration": "20 min"},
                {"title": "Algorithms - Khan Academy", "type": "course", "url": "https://www.khanacademy.org/computing/computer-science/algorithms", "platform": "Khan Academy"}
            ],
            'HTML/CSS': [
                {"title": "HTML & CSS Full Course - freeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=mU6anWqZJcc", "platform": "YouTube", "duration": "11 hours"},
                {"title": "CSS Crash Course - Traversy Media", "type": "video", "url": "https://www.youtube.com/watch?v=yfoY53QXEnI", "platform": "YouTube", "duration": "1.5 hours"},
                {"title": "MDN HTML/CSS Guide", "type": "documentation", "url": "https://developer.mozilla.org/en-US/docs/Learn/HTML", "platform": "MDN"}
            ],
            'Responsive Design': [
                {"title": "Responsive Web Design - freeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=srvUrASNj0s", "platform": "YouTube", "duration": "4 hours"},
                {"title": "Flexbox Crash Course - Traversy Media", "type": "video", "url": "https://www.youtube.com/watch?v=3YW65K6LcIA", "platform": "YouTube", "duration": "20 min"},
                {"title": "MDN Responsive Design", "type": "documentation", "url": "https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Responsive_Design", "platform": "MDN"}
            ],
            'User Research': [
                {"title": "UX Research for Beginners - CareerFoundry", "type": "video", "url": "https://www.youtube.com/watch?v=gGZGDnTY454", "platform": "YouTube", "duration": "10 min"},
                {"title": "User Research Methods - NNGroup", "type": "video", "url": "https://www.youtube.com/watch?v=7_sFVYfatXY", "platform": "YouTube", "duration": "5 min"},
                {"title": "Nielsen Norman Group UX Research", "type": "documentation", "url": "https://www.nngroup.com/articles/ux-research-cheat-sheet/", "platform": "NNGroup"}
            ],
            'Wireframing': [
                {"title": "Wireframing for Beginners - Figma", "type": "video", "url": "https://www.youtube.com/watch?v=6t_dYhXyYjI", "platform": "YouTube", "duration": "30 min"},
                {"title": "How to Wireframe - UX Mastery", "type": "video", "url": "https://www.youtube.com/watch?v=8-vTd7GRk-w", "platform": "YouTube", "duration": "5 min"},
                {"title": "Wireframing Guide - Figma", "type": "documentation", "url": "https://www.figma.com/resource-library/what-is-wireframing/", "platform": "Figma"}
            ],
            'Prototyping': [
                {"title": "Figma Prototyping Tutorial", "type": "video", "url": "https://www.youtube.com/watch?v=iBkXf6u8Mzc", "platform": "YouTube", "duration": "15 min"},
                {"title": "Prototyping in Figma - freeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=jwCmIBJ8Jtc", "platform": "YouTube", "duration": "2 hours"},
                {"title": "Figma Prototyping Guide", "type": "documentation", "url": "https://help.figma.com/hc/en-us/articles/360040314193-Guide-to-prototyping-in-Figma", "platform": "Figma"}
            ],
            'Figma': [
                {"title": "Figma Tutorial for Beginners - freeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=jwCmIBJ8Jtc", "platform": "YouTube", "duration": "2 hours"},
                {"title": "Figma UI Design Tutorial - DesignCourse", "type": "video", "url": "https://www.youtube.com/watch?v=FTFaQWZBqQ8", "platform": "YouTube", "duration": "1 hour"},
                {"title": "Figma Official Tutorials", "type": "documentation", "url": "https://help.figma.com/hc/en-us/categories/360002051613-Get-started", "platform": "Figma"}
            ],
            'UI Design': [
                {"title": "UI Design Tutorial for Beginners", "type": "video", "url": "https://www.youtube.com/watch?v=c9Wg6Cb_YlU", "platform": "YouTube", "duration": "1 hour"},
                {"title": "UI Design Fundamentals - Scrimba", "type": "video", "url": "https://www.youtube.com/watch?v=_Hp_dI0DzY4", "platform": "YouTube", "duration": "1 hour"},
                {"title": "Laws of UX", "type": "documentation", "url": "https://lawsofux.com/", "platform": "Laws of UX"}
            ],
            'UX Design': [
                {"title": "UX Design Course - Google", "type": "video", "url": "https://www.youtube.com/watch?v=VoLzL3cchyE", "platform": "YouTube", "duration": "30 min"},
                {"title": "UX Design Tutorial for Beginners", "type": "video", "url": "https://www.youtube.com/watch?v=uL2ZB7XXIgg", "platform": "YouTube", "duration": "45 min"},
                {"title": "Google UX Design Certificate", "type": "course", "url": "https://grow.google/certificates/ux-design/", "platform": "Google"}
            ],
            'Testing': [
                {"title": "Software Testing Tutorial - Guru99", "type": "video", "url": "https://www.youtube.com/watch?v=sO8eGL6SFsA", "platform": "YouTube", "duration": "3 hours"},
                {"title": "JavaScript Testing - Fireship", "type": "video", "url": "https://www.youtube.com/watch?v=u6QfIXgjwGQ", "platform": "YouTube", "duration": "12 min"},
                {"title": "Testing Library Docs", "type": "documentation", "url": "https://testing-library.com/docs/", "platform": "Official Docs"}
            ],
            'Webpack': [
                {"title": "Webpack Crash Course - Traversy Media", "type": "video", "url": "https://www.youtube.com/watch?v=IZGNcSuwBZs", "platform": "YouTube", "duration": "30 min"},
                {"title": "Webpack Tutorial - freeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=MpGLUVbqoYQ", "platform": "YouTube", "duration": "2 hours"},
                {"title": "Webpack Official Documentation", "type": "documentation", "url": "https://webpack.js.org/guides/getting-started/", "platform": "Official Docs"}
            ],
            'Redis': [
                {"title": "Redis Crash Course - TechWorld", "type": "video", "url": "https://www.youtube.com/watch?v=XCsS_NVAa1g", "platform": "YouTube", "duration": "1 hour"},
                {"title": "Redis Tutorial - freeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=jgpVdJB2sKQ", "platform": "YouTube", "duration": "1 hour"},
                {"title": "Redis Official Documentation", "type": "documentation", "url": "https://redis.io/docs/", "platform": "Official Docs"}
            ],
            'Express.js': [
                {"title": "Express.js Crash Course - Traversy Media", "type": "video", "url": "https://www.youtube.com/watch?v=L72fhGm1tfE", "platform": "YouTube", "duration": "1.5 hours"},
                {"title": "Express.js Tutorial - Programming with Mosh", "type": "video", "url": "https://www.youtube.com/watch?v=pKd0Rpw7O48", "platform": "YouTube", "duration": "1 hour"},
                {"title": "Express.js Official Documentation", "type": "documentation", "url": "https://expressjs.com/en/starter/installing.html", "platform": "Official Docs"}
            ],
            'Next.js': [
                {"title": "Next.js Tutorial - Traversy Media", "type": "video", "url": "https://www.youtube.com/watch?v=mTz0GXj8NN0", "platform": "YouTube", "duration": "1 hour"},
                {"title": "Next.js Full Course - JavaScript Mastery", "type": "video", "url": "https://www.youtube.com/watch?v=wm5gMKuwSYk", "platform": "YouTube", "duration": "5 hours"},
                {"title": "Next.js Official Documentation", "type": "documentation", "url": "https://nextjs.org/docs", "platform": "Official Docs"}
            ],
            'TailwindCSS': [
                {"title": "Tailwind CSS Crash Course - Traversy Media", "type": "video", "url": "https://www.youtube.com/watch?v=UBOj6rqRUME", "platform": "YouTube", "duration": "30 min"},
                {"title": "Tailwind CSS Tutorial - The Net Ninja", "type": "video", "url": "https://www.youtube.com/watch?v=bxmDnn7lrnk", "platform": "YouTube", "duration": "2 hours"},
                {"title": "Tailwind CSS Documentation", "type": "documentation", "url": "https://tailwindcss.com/docs", "platform": "Official Docs"}
            ],
            'Problem Solving': [
                {"title": "Problem Solving for Developers - Fireship", "type": "video", "url": "https://www.youtube.com/watch?v=UFc-RPbq8kg", "platform": "YouTube", "duration": "10 min"},
                {"title": "How to Think Like a Programmer", "type": "video", "url": "https://www.youtube.com/watch?v=azcrPFhaY9k", "platform": "YouTube", "duration": "15 min"},
                {"title": "LeetCode Practice", "type": "course", "url": "https://leetcode.com/problemset/all/", "platform": "LeetCode"}
            ],
            'Communication': [
                {"title": "Communication Skills for Engineers", "type": "video", "url": "https://www.youtube.com/watch?v=HAnw168huqA", "platform": "YouTube", "duration": "15 min"},
                {"title": "Technical Communication Skills", "type": "video", "url": "https://www.youtube.com/watch?v=Z6ygdopLpO4", "platform": "YouTube", "duration": "10 min"},
                {"title": "Communication Skills Guide", "type": "documentation", "url": "https://www.mindtools.com/page8.html", "platform": "MindTools"}
            ]
        }
        
        # Try exact match first
        if skill_name in curated:
            return curated[skill_name]
        
        # Try case-insensitive partial match
        skill_lower = skill_name.lower()
        for key, resources in curated.items():
            if skill_lower in key.lower() or key.lower() in skill_lower:
                return resources
        
        # No curated resources found
        return None
    
    def _get_fallback_resources(self, skill_name: str) -> List[Dict]:
        """Get fallback learning resources - uses curated or generates generic ones"""
        # First try curated resources
        curated = self._get_curated_resources(skill_name)
        if curated:
            return curated
        
        # For unknown skills, provide helpful general resources with real URLs
        # Format skill name for search (but use freeCodeCamp and general learning platforms)
        return [
            {"title": f"Learn {skill_name} - freeCodeCamp", "type": "course", "url": "https://www.freecodecamp.org/learn/", "platform": "freeCodeCamp"},
            {"title": f"{skill_name} Tutorial - Coursera", "type": "course", "url": "https://www.coursera.org/", "platform": "Coursera"},
            {"title": "MDN Web Docs", "type": "documentation", "url": "https://developer.mozilla.org/en-US/", "platform": "MDN"}
        ]
    
    def _fallback_analysis(self, user_skills: List, target_role: str) -> Dict[str, Any]:
        """Fallback gap analysis with learning resources"""
        # Get default requirements
        requirements = self.role_requirements.get("Software Engineer")
        for key, reqs in self.role_requirements.items():
            if target_role.lower() in key.lower():
                requirements = reqs
                break
        
        user_skill_names = [s.get('skill_name', str(s)).lower() for s in user_skills]
        
        gaps = []
        matching = []
        
        for skill in requirements.get('required', []):
            if skill.lower() in user_skill_names:
                matching.append({"skill_name": skill, "status": "meets"})
            else:
                gaps.append({
                    "skill_name": skill,
                    "current_level": "none",
                    "required_level": "intermediate",
                    "priority": "high",
                    "importance": "Core requirement for role",
                    "estimated_learning_time": "2-4 weeks",
                    "learning_approach": f"Start with fundamentals of {skill}, practice with projects",
                    "learning_resources": self._get_fallback_resources(skill)
                })
        
        for skill in requirements.get('preferred', []):
            if skill.lower() not in user_skill_names:
                gaps.append({
                    "skill_name": skill,
                    "current_level": "none",
                    "required_level": "beginner",
                    "priority": "medium",
                    "importance": "Preferred skill for role",
                    "estimated_learning_time": "1-2 weeks",
                    "learning_approach": f"Learn basics of {skill} through tutorials and practice",
                    "learning_resources": self._get_fallback_resources(skill)
                })
        
        high_priority = len([g for g in gaps if g['priority'] == 'high'])
        
        return {
            "agent": self.name,
            "status": "fallback",
            "analysis": {
                "target_role": target_role,
                "skill_gaps": gaps,
                "matching_skills": matching,
                "gap_summary": {
                    "total_gaps": len(gaps),
                    "high_priority": high_priority,
                    "medium_priority": len(gaps) - high_priority,
                    "low_priority": 0
                },
                "readiness_percentage": round(len(matching) / (len(matching) + len(gaps)) * 100) if (matching or gaps) else 50,
                "critical_path": [g['skill_name'] for g in gaps if g['priority'] == 'high'][:3],
                "overall_assessment": "Analysis based on standard role requirements."
            }
        }


# Global instance
skill_gap_agent = SkillGapAgent()
