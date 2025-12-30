"""
Reasoning Agent
Analyzes user profile and decides career paths, job readiness
This is the core thinking engine of the agentic system
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_client import llm
from typing import Dict, List, Any


class ReasoningAgent:
    """
    The Reasoning Agent is responsible for:
    1. Analyzing user profiles deeply
    2. Deciding realistic career paths
    3. Ranking job readiness
    4. Providing reasoning explanations
    """
    
    SYSTEM_PROMPT = """You are an expert career advisor and AI reasoning agent. Your role is to:
1. Deeply analyze user profiles, skills, and goals
2. Provide realistic career path recommendations
3. Calculate job readiness scores based on skill alignment
4. Give clear, actionable reasoning for your decisions

Always be encouraging but realistic. Focus on growth potential and practical next steps.
Consider industry trends and job market realities in your analysis."""
    
    def __init__(self):
        self.name = "ReasoningAgent"
    
    def analyze_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a user's complete profile and provide career insights
        
        Args:
            profile: User profile data including skills, goals, experience
        
        Returns:
            Analysis result with readiness score, recommendations, reasoning
        """
        prompt = f"""Analyze this career profile and provide comprehensive insights:

## User Profile
- Name: {profile.get('name', 'User')}
- Current Level: {profile.get('current_level', 'beginner')}
- Career Goal: {profile.get('career_goal', 'Not specified')}

## Education
{self._format_list(profile.get('education', []))}

## Skills
{self._format_skills(profile.get('skills', []))}

## Experience
{self._format_list(profile.get('experience', []))}

## Interests
{', '.join(profile.get('interests', []))}

## Target Role
{profile.get('target_role', profile.get('career_goal', 'Not specified'))}

---

Provide your analysis in the following JSON format:
{{
    "readiness_score": <0-100>,
    "readiness_level": "<not_ready|developing|almost_ready|ready>",
    "recommended_roles": [
        {{"role": "<role name>", "match_percentage": <0-100>, "reason": "<why this fits>"}}
    ],
    "strengths": ["<strength 1>", "<strength 2>"],
    "growth_areas": ["<area 1>", "<area 2>"],
    "immediate_actions": ["<action 1>", "<action 2>", "<action 3>"],
    "reasoning": "<detailed explanation of your analysis>",
    "career_trajectory": "<short-term and long-term career path suggestion>",
    "market_insights": "<relevant job market observations>"
}}"""
        
        result = llm.call_json(prompt, self.SYSTEM_PROMPT, temperature=0.3)
        
        if not result:
            return self._fallback_analysis(profile)
        
        return {
            "agent": self.name,
            "status": "success",
            "analysis": result
        }
    
    def compare_roles(self, profile: Dict[str, Any], target_roles: List[str]) -> Dict[str, Any]:
        """
        Compare user profile against multiple target roles
        
        Args:
            profile: User profile data
            target_roles: List of potential target roles
        
        Returns:
            Comparison analysis with rankings
        """
        skills_str = self._format_skills(profile.get('skills', []))
        
        prompt = f"""Compare this user's profile against these target roles:

## User Skills
{skills_str}

## Current Level: {profile.get('current_level', 'beginner')}

## Target Roles to Analyze:
{', '.join(target_roles)}

For each role, provide:
1. Match percentage (0-100)
2. Key matching skills
3. Missing critical skills
4. Time to job-ready estimate

Respond in JSON format:
{{
    "role_comparisons": [
        {{
            "role": "<role name>",
            "match_percentage": <0-100>,
            "matching_skills": ["<skill1>", "<skill2>"],
            "missing_skills": ["<skill1>", "<skill2>"],
            "time_to_ready": "<estimated time>",
            "difficulty": "<low|medium|high>",
            "recommendation": "<should pursue / needs work / not recommended>"
        }}
    ],
    "best_fit": "<recommended role>",
    "reasoning": "<explanation of ranking>"
}}"""
        
        result = llm.call_json(prompt, self.SYSTEM_PROMPT, temperature=0.3)
        
        return {
            "agent": self.name,
            "status": "success" if result else "fallback",
            "comparison": result or {"error": "Analysis unavailable"}
        }
    
    def calculate_readiness(self, skills: List[Dict], target_role: str) -> Dict[str, Any]:
        """
        Calculate detailed job readiness score for a specific role
        
        Args:
            skills: User's current skills with levels
            target_role: The target job role
        
        Returns:
            Readiness analysis with score breakdown
        """
        skills_str = self._format_skills(skills)
        
        prompt = f"""Calculate job readiness for this target role:

## Target Role: {target_role}

## Current Skills:
{skills_str}

Analyze the readiness and provide a detailed breakdown in JSON:
{{
    "overall_score": <0-100>,
    "category_scores": {{
        "technical_skills": <0-100>,
        "soft_skills": <0-100>,
        "experience": <0-100>,
        "education": <0-100>
    }},
    "ready_skills": ["<skills already sufficient>"],
    "developing_skills": ["<skills that need more work>"],
    "missing_skills": ["<skills not present>"],
    "confidence_level": "<low|medium|high>",
    "estimated_prep_time": "<time needed>",
    "key_recommendation": "<most important next step>"
}}"""
        
        result = llm.call_json(prompt, self.SYSTEM_PROMPT, temperature=0.3)
        
        return {
            "agent": self.name,
            "status": "success" if result else "fallback",
            "readiness": result or self._fallback_readiness(skills, target_role)
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
                formatted.append(f"- {name}: {level}")
            else:
                formatted.append(f"- {skill}")
        
        return '\n'.join(formatted)
    
    def _format_list(self, items: List) -> str:
        """Format a list for prompt"""
        if not items:
            return "None listed"
        
        formatted = []
        for item in items:
            if isinstance(item, dict):
                formatted.append(f"- {', '.join(f'{k}: {v}' for k, v in item.items())}")
            else:
                formatted.append(f"- {item}")
        
        return '\n'.join(formatted)
    
    def _fallback_analysis(self, profile: Dict) -> Dict[str, Any]:
        """Fallback analysis when LLM is unavailable"""
        skills_count = len(profile.get('skills', []))
        base_score = min(skills_count * 10 + 20, 70)
        
        return {
            "agent": self.name,
            "status": "fallback",
            "analysis": {
                "readiness_score": base_score,
                "readiness_level": "developing",
                "recommended_roles": [
                    {"role": profile.get('career_goal', 'Software Developer'), 
                     "match_percentage": base_score, 
                     "reason": "Based on stated goals"}
                ],
                "strengths": ["Self-motivated learner", "Clear career goals"],
                "growth_areas": ["Technical depth", "Industry experience"],
                "immediate_actions": [
                    "Build a portfolio project",
                    "Practice coding challenges",
                    "Network with professionals"
                ],
                "reasoning": "Analysis based on profile completeness and skill count.",
                "career_trajectory": "Focus on building foundational skills first.",
                "market_insights": "Tech industry continues to value practical skills."
            }
        }
    
    def _fallback_readiness(self, skills: List, target_role: str) -> Dict[str, Any]:
        """Fallback readiness calculation"""
        skill_count = len(skills)
        score = min(skill_count * 12 + 15, 75)
        
        return {
            "overall_score": score,
            "category_scores": {
                "technical_skills": score,
                "soft_skills": 60,
                "experience": 40,
                "education": 50
            },
            "ready_skills": [s.get('skill_name', s) for s in skills[:3]] if skills else [],
            "developing_skills": [],
            "missing_skills": ["Advanced concepts", "System design"],
            "confidence_level": "medium",
            "estimated_prep_time": "3-6 months",
            "key_recommendation": "Focus on building practical projects"
        }


# Global instance
reasoning_agent = ReasoningAgent()
