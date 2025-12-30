"""
Projects Recommendation Agent
Helps users discover, design, and track meaningful project ideas
based on their skills, interests, career goals, and learning progress.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_client import llm
from typing import Dict, List, Any, Optional
import json


class ProjectsAgent:
    """
    Projects Recommendation Agent
    
    Responsibilities:
    1. Read and understand user's current profile (skills, education, career goal)
    2. Analyze user profile to infer skill strengths, weaknesses, and appropriate difficulty
    3. Suggest personalized project ideas aligned with career goals
    4. Improve user-provided project ideas to industry-level quality
    5. Generate structured JSON for database storage
    """
    
    SYSTEM_PROMPT = """You are an expert Projects Recommendation Agent for an AI Career Platform.

Your role is to help users discover, design, and track meaningful project ideas that will:
- Build their portfolio
- Strengthen their skills
- Align with their career goals
- Be valuable for job applications and interviews

CORE RULES:
1. Never hallucinate or invent user skills - use ONLY what is provided
2. Suggest projects appropriate to the user's current skill level
3. Always consider the user's career goal when making suggestions
4. Projects should be realistic, implementable, and portfolio-worthy
5. Include specific technical details and features
6. Be encouraging, professional, and mentor-like in tone

DIFFICULTY GUIDELINES:
- Beginner: 1-2 weeks, basic concepts, guided structure
- Intermediate: 2-4 weeks, combines multiple skills, some complexity
- Advanced: 1-2 months, production-level, complex architecture

When generating project suggestions, ensure they:
- Have clear learning outcomes
- Use skills the user already has or is learning
- Can be explained well in interviews
- Show practical, real-world application"""
    
    def __init__(self):
        self.name = "ProjectsAgent"
    
    def analyze_user_profile(
        self,
        skills: List[Dict],
        career_goal: str,
        education: Optional[Dict] = None,
        completed_projects: Optional[List[Dict]] = None,
        skill_gaps: Optional[List[Dict]] = None,
        learning_progress: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze user profile to determine project recommendations context
        
        Args:
            skills: User's current skills with levels
            career_goal: Target role/career objective
            education: Education background
            completed_projects: Previously completed projects
            skill_gaps: Identified skill gaps
            learning_progress: Current learning status
        
        Returns:
            Analysis of user's project readiness and recommendations context
        """
        # Format skills
        skills_str = ', '.join([
            f"{s.get('skill_name', s.get('name', ''))} ({s.get('level', 'beginner')})" 
            for s in (skills or [])
        ])
        
        # Format completed projects
        projects_str = "None"
        if completed_projects:
            projects_str = ', '.join([
                p.get('project_title', p.get('title', '')) 
                for p in completed_projects[:5]
            ])
        
        # Format skill gaps
        gaps_str = "None identified"
        if skill_gaps:
            gaps_str = ', '.join([
                f"{g.get('skill_name', '')} ({g.get('priority', 'medium')} priority)"
                for g in skill_gaps[:5]
            ])
        
        prompt = f"""Analyze this user's profile to determine the best project recommendations context:

## User Profile
- Career Goal: {career_goal or 'Not specified'}
- Education: {education.get('degree', 'Not specified') if education else 'Not specified'}
- Current Skills: {skills_str or 'None added'}
- Completed Projects: {projects_str}
- Skill Gaps to Address: {gaps_str}
- Learning Progress: {learning_progress.get('summary', 'Starting journey') if learning_progress else 'Starting journey'}

Provide analysis in JSON:
{{
    "skill_level": "<beginner|intermediate|advanced>",
    "strongest_skills": ["skill1", "skill2", "skill3"],
    "skills_to_develop": ["skill1", "skill2"],
    "recommended_difficulty": "<Beginner|Intermediate|Advanced>",
    "recommended_domains": ["domain1", "domain2"],
    "portfolio_gaps": ["what's missing from their portfolio"],
    "readiness_assessment": "<brief assessment of their project readiness>",
    "focus_areas": ["area1", "area2"],
    "opening_message": "<personalized greeting and summary for the user>"
}}"""
        
        result = llm.call_json(prompt, self.SYSTEM_PROMPT, temperature=0.3)
        
        if result:
            return {
                "agent": self.name,
                "status": "success",
                "analysis": result
            }
        else:
            # Fallback analysis
            return {
                "agent": self.name,
                "status": "fallback",
                "analysis": {
                    "skill_level": "beginner",
                    "strongest_skills": [s.get('skill_name', '') for s in (skills or [])[:3]],
                    "skills_to_develop": [g.get('skill_name', '') for g in (skill_gaps or [])[:3]],
                    "recommended_difficulty": "Beginner",
                    "recommended_domains": ["Web Development", "Data Processing"],
                    "portfolio_gaps": ["Portfolio projects", "Real-world applications"],
                    "readiness_assessment": "Ready to start building foundational projects",
                    "focus_areas": ["Core skills practice", "Portfolio building"],
                    "opening_message": f"Based on your profile, I can suggest projects tailored to your goal of becoming a {career_goal or 'developer'}. Do you already have any project idea in mind?"
                }
            }
    
    def suggest_projects(
        self,
        user_profile: Dict,
        skills: List[Dict],
        career_goal: str,
        skill_gaps: Optional[List[Dict]] = None,
        completed_projects: Optional[List[Dict]] = None,
        count: int = 5
    ) -> Dict[str, Any]:
        """
        Generate personalized project suggestions
        
        Args:
            user_profile: User profile information
            skills: User's current skills
            career_goal: Target career role
            skill_gaps: Skills to develop
            completed_projects: Already completed projects
            count: Number of suggestions
        
        Returns:
            List of project suggestions
        """
        # Format skills
        skills_list = [
            f"{s.get('skill_name', s.get('name', ''))} ({s.get('level', 'beginner')})" 
            for s in (skills or [])
        ]
        
        # Format skill gaps
        gaps_list = [
            g.get('skill_name', '') for g in (skill_gaps or [])
        ]
        
        # Format completed projects to avoid repetition
        completed_titles = [
            p.get('project_title', p.get('title', '')) 
            for p in (completed_projects or [])
        ]
        
        prompt = f"""Generate {count} personalized project suggestions for this user:

## User Context
- Career Goal: {career_goal or 'Software Developer'}
- Current Skills: {', '.join(skills_list) or 'None specified'}
- Skills to Develop: {', '.join(gaps_list) or 'Not specified'}
- Already Completed: {', '.join(completed_titles) or 'None'}
- Experience Level: {user_profile.get('current_level', 'beginner')}

Generate EXACTLY {count} project suggestions in JSON:
{{
    "suggestions": [
        {{
            "project_title": "<Creative, descriptive project name>",
            "difficulty": "<Beginner|Intermediate|Advanced>",
            "description": "<2-3 sentence description of what the project does and why it's valuable>",
            "skills_used": ["skill1", "skill2", "skill3"],
            "features": [
                "<Feature 1: Specific implementation detail>",
                "<Feature 2: Specific implementation detail>",
                "<Feature 3: Specific implementation detail>",
                "<Feature 4: Specific implementation detail>",
                "<Feature 5: Specific implementation detail>"
            ],
            "tech_stack": {{
                "frontend": ["tech1", "tech2"],
                "backend": ["tech1"],
                "database": ["tech1"],
                "other": ["tool1"]
            }},
            "learning_outcomes": [
                "<What the user will learn 1>",
                "<What the user will learn 2>",
                "<What the user will learn 3>"
            ],
            "estimated_duration": "<e.g., 2-3 weeks>",
            "resume_value": "<Why this project matters for their resume and interviews>",
            "interview_talking_points": ["<Point 1>", "<Point 2>"]
        }}
    ],
    "recommendation_note": "<Brief note about why these projects were chosen>"
}}

IMPORTANT:
1. Mix difficulty levels (at least one Beginner, one Intermediate)
2. Projects should align with the career goal: {career_goal}
3. Use skills the user has OR skills from their skill gaps
4. Each project must be unique and portfolio-worthy
5. DO NOT suggest projects similar to what they've already completed"""
        
        result = llm.call_json(prompt, self.SYSTEM_PROMPT, temperature=0.6)
        
        if result and 'suggestions' in result:
            return {
                "agent": self.name,
                "status": "success",
                "suggestions": result['suggestions'],
                "recommendation_note": result.get('recommendation_note', ''),
                "count": len(result['suggestions'])
            }
        else:
            return self._fallback_suggestions(career_goal, skills)
    
    def improve_user_idea(
        self,
        user_idea: str,
        user_profile: Dict,
        skills: List[Dict],
        career_goal: str
    ) -> Dict[str, Any]:
        """
        Improve and structure a user-provided project idea
        
        Args:
            user_idea: User's raw project idea description
            user_profile: User profile information
            skills: User's current skills
            career_goal: Target career role
        
        Returns:
            Improved, structured project definition
        """
        skills_list = [
            f"{s.get('skill_name', s.get('name', ''))} ({s.get('level', 'beginner')})" 
            for s in (skills or [])
        ]
        
        prompt = f"""The user has shared their project idea. Your job is to:
1. Understand their idea completely
2. Improve it technically
3. Add missing features
4. Suggest better scope and structure
5. Upgrade it to industry-level quality

## User's Idea:
"{user_idea}"

## User Context:
- Career Goal: {career_goal or 'Software Developer'}
- Current Skills: {', '.join(skills_list) or 'General programming'}
- Experience Level: {user_profile.get('current_level', 'beginner')}

Transform this into a production-grade project in JSON:
{{
    "original_idea_summary": "<Brief summary of what the user wanted>",
    "project_title": "<Professional, marketable project name>",
    "difficulty": "<Beginner|Intermediate|Advanced>",
    "description": "<3-4 sentence professional description of the improved project>",
    "skills_used": ["skill1", "skill2", "skill3", "skill4"],
    "features": [
        "<Core Feature 1>",
        "<Core Feature 2>",
        "<Core Feature 3>",
        "<Advanced Feature 1>",
        "<Advanced Feature 2>",
        "<Bonus Feature (if time permits)>"
    ],
    "tech_stack": {{
        "frontend": ["tech1", "tech2"],
        "backend": ["tech1", "tech2"],
        "database": ["tech1"],
        "ai": ["<if applicable>"],
        "other": ["tool1", "tool2"]
    }},
    "learning_outcomes": [
        "<What they will learn 1>",
        "<What they will learn 2>",
        "<What they will learn 3>",
        "<What they will learn 4>"
    ],
    "estimated_duration": "<realistic time estimate>",
    "resume_value": "<Why this project will impress recruiters>",
    "improvements_made": [
        "<How you improved the original idea 1>",
        "<How you improved the original idea 2>",
        "<How you improved the original idea 3>"
    ],
    "implementation_phases": [
        {{
            "phase": 1,
            "name": "<Phase name>",
            "tasks": ["<task1>", "<task2>"],
            "duration": "<time>"
        }},
        {{
            "phase": 2,
            "name": "<Phase name>",
            "tasks": ["<task1>", "<task2>"],
            "duration": "<time>"
        }},
        {{
            "phase": 3,
            "name": "<Phase name>",
            "tasks": ["<task1>", "<task2>"],
            "duration": "<time>"
        }}
    ],
    "interview_talking_points": [
        "<Technical challenge solved>",
        "<Design decision made>",
        "<Impact/result achieved>"
    ]
}}

CRITICAL: Keep the project achievable based on the user's skill level while still making it impressive."""
        
        result = llm.call_json(prompt, self.SYSTEM_PROMPT, temperature=0.5)
        
        if result:
            return {
                "agent": self.name,
                "status": "success",
                "improved_project": result,
                "original_idea": user_idea
            }
        else:
            return {
                "agent": self.name,
                "status": "error",
                "message": "Could not improve the project idea. Please try rephrasing.",
                "original_idea": user_idea
            }
    
    def convert_to_saveable_format(
        self,
        project_data: Dict,
        user_id: int = None
    ) -> Dict[str, Any]:
        """
        Convert project data to database-saveable JSON format
        
        Args:
            project_data: Project suggestion or improved project data
            user_id: Optional user ID
        
        Returns:
            Clean JSON ready for database insertion
        """
        # Ensure all required fields are present
        saveable = {
            "project_title": project_data.get('project_title', 'Untitled Project'),
            "difficulty": project_data.get('difficulty', 'Intermediate'),
            "description": project_data.get('description', ''),
            "skills_used": project_data.get('skills_used', []),
            "features": project_data.get('features', []),
            "tech_stack": project_data.get('tech_stack', {}),
            "learning_outcomes": project_data.get('learning_outcomes', []),
            "resume_value": project_data.get('resume_value', ''),
            "status": "planned"
        }
        
        # Add optional fields if present
        if 'implementation_phases' in project_data:
            saveable['implementation_phases'] = project_data['implementation_phases']
        
        if 'estimated_duration' in project_data:
            saveable['estimated_duration'] = project_data['estimated_duration']
        
        if 'interview_talking_points' in project_data:
            saveable['interview_talking_points'] = project_data['interview_talking_points']
        
        if 'original_idea_summary' in project_data:
            saveable['original_idea'] = project_data.get('original_idea_summary', '')
        
        return {
            "agent": self.name,
            "status": "success",
            "project_data": saveable
        }
    
    def chat_response(
        self,
        message: str,
        user_profile: Dict,
        skills: List[Dict],
        career_goal: str,
        conversation_stage: str = "initial",
        previous_suggestions: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Handle conversational interactions about projects
        
        Args:
            message: User's message
            user_profile: User profile
            skills: User's skills
            career_goal: Career goal
            conversation_stage: Where in the conversation we are
            previous_suggestions: Previously shown suggestions
        
        Returns:
            Appropriate response based on message content
        """
        skills_list = [s.get('skill_name', '') for s in (skills or [])]
        
        prompt = f"""You are chatting with a user about project ideas. Analyze their message and respond appropriately.

## User Message:
"{message}"

## User Context:
- Career Goal: {career_goal or 'Software Developer'}
- Skills: {', '.join(skills_list) or 'Not specified'}
- Conversation Stage: {conversation_stage}

## Previous Suggestions Shown:
{json.dumps([s.get('project_title', '') for s in (previous_suggestions or [])]) if previous_suggestions else 'None yet'}

Determine the user's intent and respond in JSON:
{{
    "intent": "<suggest_projects|has_own_idea|select_project|ask_question|confirm|other>",
    "response_text": "<Your natural, friendly response to the user>",
    "action_needed": "<none|generate_suggestions|improve_idea|save_project|clarify>",
    "extracted_idea": "<If user shared a project idea, extract it here, otherwise null>",
    "selected_project_index": <If user selected a project by number, put index here, otherwise null>,
    "needs_more_info": <true|false>
}}

GUIDELINES:
- If user says they have NO idea → action_needed = "generate_suggestions"
- If user describes a project idea → action_needed = "improve_idea", extract the idea
- If user says "yes" or confirms → action_needed = "save_project"
- If user picks a number (like "1" or "project 2") → extract the index
- Be conversational, helpful, and encouraging"""
        
        result = llm.call_json(prompt, self.SYSTEM_PROMPT, temperature=0.5)
        
        if result and isinstance(result, dict):
            # Ensure response_text field exists and use fallback if missing
            response_text = result.get('response_text', '') or result.get('response', '')
            if not response_text:
                # If no response text, provide a default based on intent
                intent = result.get('intent', 'other')
                if intent == 'suggest_projects':
                    response_text = "I'd be happy to suggest some project ideas for you!"
                elif intent == 'has_own_idea':
                    response_text = "Great! Tell me about your project idea and I'll help you refine it."
                else:
                    response_text = "How can I help you with your projects today?"
            
            return {
                "agent": self.name,
                "status": "success",
                "intent": result.get('intent', 'other'),
                "response": response_text,
                "action": result.get('action_needed', 'none'),
                "extracted_idea": result.get('extracted_idea'),
                "selected_index": result.get('selected_project_index'),
                "needs_more_info": result.get('needs_more_info', False)
            }
        else:
            return {
                "agent": self.name,
                "status": "fallback",
                "intent": "other",
                "response": "I'd be happy to help you with project ideas! Could you tell me more about what you're looking for?",
                "action": "clarify",
                "extracted_idea": None,
                "selected_index": None,
                "needs_more_info": True
            }
    
    def _fallback_suggestions(self, career_goal: str, skills: List[Dict]) -> Dict[str, Any]:
        """Generate fallback suggestions when LLM fails"""
        goal_lower = (career_goal or '').lower()
        
        suggestions = []
        
        # Web Development suggestions
        if 'web' in goal_lower or 'frontend' in goal_lower or 'full' in goal_lower:
            suggestions = [
                {
                    "project_title": "Personal Portfolio Website",
                    "difficulty": "Beginner",
                    "description": "A responsive portfolio website showcasing your skills, projects, and experience.",
                    "skills_used": ["HTML", "CSS", "JavaScript", "React"],
                    "features": ["Responsive design", "Project showcase", "Contact form", "Dark mode"],
                    "tech_stack": {"frontend": ["React", "CSS"], "hosting": ["Netlify"]},
                    "learning_outcomes": ["Responsive design", "Component architecture", "Deployment"],
                    "resume_value": "Shows frontend skills and attention to design"
                },
                {
                    "project_title": "Task Management Application",
                    "difficulty": "Intermediate",
                    "description": "A full-stack task management app with user authentication and CRUD operations.",
                    "skills_used": ["React", "Node.js", "SQL", "REST APIs"],
                    "features": ["User auth", "CRUD tasks", "Categories", "Due dates", "Search"],
                    "tech_stack": {"frontend": ["React"], "backend": ["Node.js", "Express"], "database": ["MySQL"]},
                    "learning_outcomes": ["Full-stack development", "Authentication", "Database design"],
                    "resume_value": "Demonstrates complete application development cycle"
                }
            ]
        # Data Science / ML suggestions
        elif 'data' in goal_lower or 'machine' in goal_lower or 'ai' in goal_lower:
            suggestions = [
                {
                    "project_title": "Data Visualization Dashboard",
                    "difficulty": "Beginner",
                    "description": "An interactive dashboard visualizing real-world data with charts and filters.",
                    "skills_used": ["Python", "Pandas", "Matplotlib", "Plotly"],
                    "features": ["Multiple chart types", "Filtering", "Data export", "Responsive layout"],
                    "tech_stack": {"backend": ["Python", "Flask"], "visualization": ["Plotly", "D3.js"]},
                    "learning_outcomes": ["Data manipulation", "Visualization", "Dashboard design"],
                    "resume_value": "Shows data analysis and visualization skills"
                },
                {
                    "project_title": "Sentiment Analysis Tool",
                    "difficulty": "Intermediate",
                    "description": "An NLP tool that analyzes text sentiment using machine learning.",
                    "skills_used": ["Python", "NLP", "Machine Learning", "APIs"],
                    "features": ["Text analysis", "Sentiment scoring", "Batch processing", "API endpoint"],
                    "tech_stack": {"backend": ["Python", "FastAPI"], "ml": ["scikit-learn", "NLTK"]},
                    "learning_outcomes": ["NLP basics", "ML pipelines", "API development"],
                    "resume_value": "Demonstrates ML and NLP application"
                }
            ]
        else:
            # Generic suggestions
            suggestions = [
                {
                    "project_title": "Personal Blog Platform",
                    "difficulty": "Beginner",
                    "description": "A blog platform where users can create, edit, and publish articles.",
                    "skills_used": ["HTML", "CSS", "JavaScript", "SQL"],
                    "features": ["Article CRUD", "Categories", "Search", "Comments"],
                    "tech_stack": {"frontend": ["HTML", "CSS", "JS"], "backend": ["PHP"], "database": ["MySQL"]},
                    "learning_outcomes": ["Web fundamentals", "Database operations", "CRUD patterns"],
                    "resume_value": "Shows fundamental web development skills"
                },
                {
                    "project_title": "Weather Application",
                    "difficulty": "Beginner",
                    "description": "A weather app that fetches and displays weather data from a public API.",
                    "skills_used": ["JavaScript", "APIs", "CSS"],
                    "features": ["Current weather", "5-day forecast", "Location search", "Weather icons"],
                    "tech_stack": {"frontend": ["JavaScript", "CSS"], "api": ["OpenWeatherMap"]},
                    "learning_outcomes": ["API integration", "Async JavaScript", "UI design"],
                    "resume_value": "Demonstrates API integration skills"
                }
            ]
        
        return {
            "agent": self.name,
            "status": "fallback",
            "suggestions": suggestions,
            "recommendation_note": f"These projects are tailored for your goal of becoming a {career_goal or 'developer'}.",
            "count": len(suggestions)
        }


# Create singleton instance
projects_agent = ProjectsAgent()
