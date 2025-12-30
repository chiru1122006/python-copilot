"""
Feedback Agent
Career Feedback Analysis Agent - Analyzes job application rejections, 
interview feedback, and user self-reflections to identify improvement areas.
"""
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_client import llm
from typing import Dict, List, Any, Optional


class FeedbackAgent:
    """
    The Career Feedback Analysis Agent is responsible for:
    1. Analyzing job application rejections, interview feedback, and self-reflections
    2. Identifying rejection reasons and skill gaps
    3. Detecting behavioral or communication issues
    4. Identifying resume or project weaknesses
    5. Suggesting concrete improvements
    6. Generating actionable recovery plans
    7. Updating learning priorities
    8. Detecting patterns across multiple feedback entries
    """
    
    SYSTEM_PROMPT = """You are a Career Feedback Analysis Agent - an expert career coach specializing in feedback analysis and improvement strategies.

Your role is to analyze job application rejections, interview feedback, and user self-reflections to identify why the user was rejected and how they can improve.

You must combine:
- User profile (skills, education, projects, experience)
- Job role and company (if provided)
- Feedback text (email, message, or self-written reflection)
- Past application history (if available)

Your goals:
1. Identify the most likely rejection reasons
2. Classify the feedback type
3. Detect skill gaps
4. Identify behavioral or communication issues
5. Detect resume or project weaknesses
6. Suggest concrete improvements
7. Generate an actionable recovery plan
8. Update learning priorities

IMPORTANT RULES:
- Never blame the user
- Be constructive and supportive
- Do not hallucinate company feedback
- Infer carefully and explain reasoning
- If feedback text is empty, rely on skill profile
- Be concise but insightful
- Maintain an encouraging, mentor-style tone

Rejection Reason Categories:
- Skill gap
- Lack of experience
- Weak projects
- Poor interview communication
- Weak problem solving
- Poor system design
- Resume issues
- Cultural fit
- Behavioral answers
- Role mismatch
- Unknown / generic rejection"""
    
    def __init__(self):
        self.name = "FeedbackAgent"
    
    def analyze_rejection(self, rejection_data: Dict) -> Dict[str, Any]:
        """
        Analyze a job rejection and extract insights
        
        Args:
            rejection_data: Details about the rejection
        
        Returns:
            Analysis with insights and action items
        """
        prompt = f"""Analyze this job rejection and provide insights:

## Rejection Details
- Company: {rejection_data.get('company', 'Unknown')}
- Role: {rejection_data.get('role', 'Unknown')}
- Stage: {rejection_data.get('stage', 'Unknown')}
- Feedback Received: {rejection_data.get('message', 'No specific feedback')}
- Interview Type: {rejection_data.get('interview_type', 'Unknown')}

## User's Skills:
{rejection_data.get('user_skills', 'Not provided')}

Provide analysis in JSON:
{{
    "rejection_analysis": {{
        "likely_reasons": ["<possible reasons for rejection>"],
        "skill_gaps_identified": ["<skills that may have been lacking>"],
        "interview_performance": {{
            "strengths_shown": ["<what went well>"],
            "areas_for_improvement": ["<what could be better>"]
        }},
        "company_fit_analysis": "<assessment of fit with company>",
        "competition_factor": "<how competitive was this role likely>"
    }},
    "action_items": [
        {{
            "action": "<specific action to take>",
            "priority": "<high|medium|low>",
            "timeline": "<when to do this>",
            "expected_outcome": "<what this will improve>"
        }}
    ],
    "roadmap_updates": [
        "<suggested changes to learning plan>"
    ],
    "skills_to_focus": ["<skills to prioritize>"],
    "encouragement": "<motivational message>",
    "next_steps": ["<immediate actions>"],
    "similar_role_tips": "<advice for similar applications>"
}}"""
        
        result = llm.call_json(prompt, self.SYSTEM_PROMPT, temperature=0.4)
        
        if not result:
            return self._fallback_rejection_analysis(rejection_data)
        
        return {
            "agent": self.name,
            "status": "success",
            "analysis": result
        }
    
    def analyze_interview_feedback(self, feedback_data: Dict) -> Dict[str, Any]:
        """
        Analyze interview feedback to extract learnings
        
        Args:
            feedback_data: Interview feedback details
        
        Returns:
            Detailed analysis with improvement suggestions
        """
        prompt = f"""Analyze this interview feedback:

## Interview Details
- Company: {feedback_data.get('company', 'Unknown')}
- Role: {feedback_data.get('role', 'Unknown')}
- Interview Type: {feedback_data.get('type', 'Unknown')}
- Duration: {feedback_data.get('duration', 'Unknown')}

## Feedback Received:
{feedback_data.get('message', 'No specific feedback')}

## Questions Asked (if available):
{feedback_data.get('questions', 'Not provided')}

## Self-Assessment:
{feedback_data.get('self_assessment', 'Not provided')}

Provide analysis in JSON:
{{
    "performance_breakdown": {{
        "technical_skills": {{
            "score": "<weak|average|strong>",
            "notes": "<specific observations>"
        }},
        "communication": {{
            "score": "<weak|average|strong>",
            "notes": "<specific observations>"
        }},
        "problem_solving": {{
            "score": "<weak|average|strong>",
            "notes": "<specific observations>"
        }},
        "cultural_fit": {{
            "score": "<weak|average|strong>",
            "notes": "<specific observations>"
        }}
    }},
    "key_insights": ["<important takeaways>"],
    "strengths_demonstrated": ["<what you did well>"],
    "improvement_areas": [
        {{
            "area": "<what to improve>",
            "specific_feedback": "<details>",
            "how_to_improve": "<action steps>",
            "resources": ["<helpful resources>"]
        }}
    ],
    "practice_recommendations": ["<what to practice>"],
    "mindset_adjustments": ["<mental approach changes>"],
    "next_interview_tips": ["<tips for next time>"]
}}"""
        
        result = llm.call_json(prompt, self.SYSTEM_PROMPT, temperature=0.4)
        
        return {
            "agent": self.name,
            "status": "success" if result else "fallback",
            "analysis": result or {"message": "Analysis unavailable"}
        }
    
    def detect_patterns(self, feedback_history: List[Dict]) -> Dict[str, Any]:
        """
        Detect patterns across multiple feedback entries
        
        Args:
            feedback_history: List of previous feedback entries
        
        Returns:
            Pattern analysis with systemic insights
        """
        if not feedback_history:
            return {
                "agent": self.name,
                "status": "no_data",
                "patterns": {"message": "No feedback history to analyze"}
            }
        
        # Format feedback history
        history_str = ""
        for i, fb in enumerate(feedback_history[:10], 1):
            history_str += f"""
{i}. {fb.get('source', 'Unknown')} - {fb.get('company', 'Unknown')}
   Message: {fb.get('message', 'N/A')}
   Analysis: {fb.get('analysis', 'N/A')}
"""
        
        prompt = f"""Analyze patterns across this feedback history:

{history_str}

Identify patterns in JSON:
{{
    "recurring_themes": [
        {{
            "theme": "<pattern identified>",
            "frequency": "<how often it appears>",
            "severity": "<critical|significant|minor>",
            "examples": ["<specific instances>"]
        }}
    ],
    "skill_gaps_pattern": ["<consistently missing skills>"],
    "strength_patterns": ["<consistently positive areas>"],
    "interview_stage_analysis": {{
        "early_stage_issues": ["<problems in initial stages>"],
        "later_stage_issues": ["<problems in final stages>"]
    }},
    "root_causes": ["<underlying causes>"],
    "systemic_recommendations": [
        {{
            "recommendation": "<what to change>",
            "addresses": "<which pattern this fixes>",
            "implementation": "<how to implement>"
        }}
    ],
    "priority_improvements": ["<most impactful changes>"],
    "positive_trends": ["<improvements over time>"],
    "summary": "<overall pattern analysis>"
}}"""
        
        result = llm.call_json(prompt, self.SYSTEM_PROMPT, temperature=0.4)
        
        return {
            "agent": self.name,
            "status": "success" if result else "fallback",
            "patterns": result or self._fallback_patterns(feedback_history)
        }
    
    def analyze_progress(self, progress_data: Dict) -> Dict[str, Any]:
        """
        Analyze learning progress and provide feedback
        
        Args:
            progress_data: Progress metrics and completion data
        
        Returns:
            Progress analysis with recommendations
        """
        prompt = f"""Analyze this learning progress:

## Progress Data
- Tasks Completed: {progress_data.get('completed_tasks', 0)}
- Total Tasks: {progress_data.get('total_tasks', 0)}
- Completion Rate: {progress_data.get('completion_rate', 0)}%
- Weeks Elapsed: {progress_data.get('weeks_elapsed', 0)}
- Skills Improved: {progress_data.get('skills_improved', [])}
- Challenges Faced: {progress_data.get('challenges', [])}

## Weekly Breakdown:
{progress_data.get('weekly_breakdown', 'Not available')}

Provide progress analysis in JSON:
{{
    "progress_assessment": {{
        "overall_status": "<on_track|ahead|behind|needs_attention>",
        "completion_rate_analysis": "<assessment of completion rate>",
        "pace_analysis": "<is the pace sustainable?>"
    }},
    "achievements": ["<notable accomplishments>"],
    "areas_of_concern": ["<potential issues>"],
    "momentum_tips": ["<how to maintain progress>"],
    "schedule_adjustments": ["<suggested changes>"],
    "motivation_boosters": ["<encouragement>"],
    "next_week_focus": ["<what to prioritize>"],
    "celebration_worthy": ["<achievements to celebrate>"]
}}"""
        
        result = llm.call_json(prompt, self.SYSTEM_PROMPT, temperature=0.4)
        
        return {
            "agent": self.name,
            "status": "success" if result else "fallback",
            "analysis": result or self._fallback_progress(progress_data)
        }
    
    def generate_weekly_report(self, user_data: Dict) -> Dict[str, Any]:
        """
        Generate a weekly AI progress report
        
        Args:
            user_data: User's weekly data including progress, activities, etc.
        
        Returns:
            Comprehensive weekly report
        """
        prompt = f"""Generate a weekly progress report:

## User Data
- Name: {user_data.get('name', 'User')}
- Target Role: {user_data.get('target_role', 'Not set')}
- Current Week: {user_data.get('current_week', 1)}

## This Week's Activities
- Tasks Completed: {user_data.get('tasks_completed', [])}
- Hours Spent: {user_data.get('hours_spent', 0)}
- New Skills: {user_data.get('new_skills', [])}
- Applications Sent: {user_data.get('applications', 0)}

## Challenges
{user_data.get('challenges', 'None reported')}

Generate a comprehensive weekly report in JSON:
{{
    "report_title": "<catchy title>",
    "week_summary": "<brief overview>",
    "key_accomplishments": ["<achievements>"],
    "skills_progress": [
        {{"skill": "<skill>", "progress": "<description>", "level_change": "<if any>"}}
    ],
    "readiness_change": {{
        "previous": <score>,
        "current": <score>,
        "delta": <change>,
        "trend": "<improving|stable|declining>"
    }},
    "insights": ["<AI observations>"],
    "challenges_addressed": ["<how challenges were handled>"],
    "next_week_preview": {{
        "focus_areas": ["<priorities>"],
        "goals": ["<specific goals>"],
        "recommendations": ["<suggestions>"]
    }},
    "motivation_message": "<personalized encouragement>",
    "agent_thoughts": "<AI's perspective on progress>"
}}"""
        
        result = llm.call_json(prompt, self.SYSTEM_PROMPT, temperature=0.5)
        
        return {
            "agent": self.name,
            "status": "success" if result else "fallback",
            "report": result or self._fallback_report(user_data)
        }
    
    def comprehensive_feedback_analysis(
        self, 
        feedback_data: Dict,
        user_profile: Optional[Dict] = None,
        user_skills: Optional[List[Dict]] = None,
        application_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        COMPREHENSIVE Career Feedback Analysis
        
        This is the main analysis method that provides a complete breakdown
        of feedback for career coaching purposes.
        
        Args:
            feedback_data: The feedback to analyze including:
                - source: 'rejection_email' | 'interview_feedback' | 'self_reflection' | 'mentor_feedback'
                - company: Company name (optional)
                - role: Role name (optional)
                - message: The feedback text
                - interview_type: Type of interview if applicable
                - stage: Interview stage if applicable
            user_profile: User's profile data (education, experience, etc.)
            user_skills: User's current skills list
            application_history: Previous application history
        
        Returns:
            Comprehensive analysis with structured output for storage
        """
        start_time = time.time()
        
        # Build context strings
        source = feedback_data.get('source', 'unknown')
        source_display = source.replace('_', ' ').title()
        
        skills_str = "Not provided"
        if user_skills:
            skills_str = ", ".join([f"{s.get('skill_name', s.get('name', 'Unknown'))} ({s.get('level', 'unknown')})" 
                                   for s in user_skills[:15]])
        
        profile_str = "Not provided"
        if user_profile:
            profile_parts = []
            if user_profile.get('name'):
                profile_parts.append(f"Name: {user_profile['name']}")
            if user_profile.get('target_role'):
                profile_parts.append(f"Target Role: {user_profile['target_role']}")
            if user_profile.get('current_level'):
                profile_parts.append(f"Level: {user_profile['current_level']}")
            if user_profile.get('education_level'):
                profile_parts.append(f"Education: {user_profile['education_level']}")
            if user_profile.get('field_of_study'):
                profile_parts.append(f"Field: {user_profile['field_of_study']}")
            if user_profile.get('experience_years'):
                profile_parts.append(f"Experience: {user_profile['experience_years']} years")
            profile_str = " | ".join(profile_parts) if profile_parts else "Not provided"
        
        history_str = "No previous applications"
        if application_history:
            history_parts = []
            for app in application_history[:5]:
                history_parts.append(f"- {app.get('company', 'Unknown')} ({app.get('role', 'Unknown')}): {app.get('status', 'unknown')}")
            history_str = "\n".join(history_parts)
        
        prompt = f"""Perform a COMPREHENSIVE career feedback analysis.

## Feedback Source
Type: {source_display}

## Feedback Details
- Company: {feedback_data.get('company', 'Not specified')}
- Role: {feedback_data.get('role', 'Not specified')}
- Interview Type: {feedback_data.get('interview_type', 'Not specified')}
- Stage: {feedback_data.get('stage', 'Not specified')}

## Feedback Message/Text
{feedback_data.get('message', 'No feedback text provided')}

## User Profile
{profile_str}

## User's Current Skills
{skills_str}

## Application History
{history_str}

Analyze this feedback comprehensively and return a JSON response with this EXACT structure:

{{
    "source": "{source}",
    "company": "{feedback_data.get('company', '')}",
    "role": "{feedback_data.get('role', '')}",
    "identified_reasons": [
        "<List 2-5 specific reasons for rejection or areas of concern inferred from the feedback>"
    ],
    "skill_gaps": [
        "<List technical or domain skills that appear to be lacking>"
    ],
    "behavioral_gaps": [
        "<List behavioral issues like communication, confidence, clarity, teamwork>"
    ],
    "resume_issues": [
        "<List any resume-related problems mentioned or inferred (weak descriptions, missing metrics, etc.)>"
    ],
    "technical_gaps": [
        "<List specific technical areas needing improvement (data structures, system design, etc.)>"
    ],
    "strengths_detected": [
        "<List positive aspects detected in the feedback or profile>"
    ],
    "confidence_level": "<low|medium|high - how confident are you in this analysis>",
    "recommended_actions": [
        "<List 3-7 specific, actionable recommendations>"
    ],
    "learning_plan": [
        {{
            "area": "<skill or topic area>",
            "action": "<specific learning action>",
            "timeline": "<realistic timeline like '2 weeks', '1 month'>"
        }}
    ],
    "project_suggestions": [
        "<2-4 project ideas that would address the identified gaps>"
    ],
    "resume_improvements": [
        "<Specific resume improvement suggestions>"
    ],
    "next_steps": [
        "<3-5 immediate actions the user should take>"
    ],
    "readiness_score": <0-100 integer estimating current readiness for similar roles>,
    "summary_message": "<A supportive, mentor-style 2-3 sentence summary explaining what went wrong and how to improve. Be encouraging but honest.>"
}}

IMPORTANT:
- Be specific and actionable in all recommendations
- Base your analysis on the actual feedback provided
- If information is missing, make reasonable inferences but note them
- The readiness_score should reflect realistic assessment
- Keep the summary_message encouraging and constructive"""

        result = llm.call_json(prompt, self.SYSTEM_PROMPT, temperature=0.3)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        if not result:
            return self._fallback_comprehensive_analysis(feedback_data, processing_time)
        
        # Ensure all required fields exist with defaults
        analysis = {
            "source": result.get("source", source),
            "company": result.get("company", feedback_data.get('company', '')),
            "role": result.get("role", feedback_data.get('role', '')),
            "identified_reasons": result.get("identified_reasons", []),
            "skill_gaps": result.get("skill_gaps", []),
            "behavioral_gaps": result.get("behavioral_gaps", []),
            "resume_issues": result.get("resume_issues", []),
            "technical_gaps": result.get("technical_gaps", []),
            "strengths_detected": result.get("strengths_detected", []),
            "confidence_level": result.get("confidence_level", "medium"),
            "recommended_actions": result.get("recommended_actions", []),
            "learning_plan": result.get("learning_plan", []),
            "project_suggestions": result.get("project_suggestions", []),
            "resume_improvements": result.get("resume_improvements", []),
            "next_steps": result.get("next_steps", []),
            "readiness_score": result.get("readiness_score", 50),
            "summary_message": result.get("summary_message", "Analysis complete. Focus on the identified areas for improvement.")
        }
        
        return {
            "agent": self.name,
            "status": "success",
            "analysis": analysis,
            "processing_time_ms": processing_time
        }
    
    def _fallback_comprehensive_analysis(self, feedback_data: Dict, processing_time: int) -> Dict[str, Any]:
        """Fallback for comprehensive analysis when LLM fails"""
        source = feedback_data.get('source', 'unknown')
        
        return {
            "agent": self.name,
            "status": "fallback",
            "analysis": {
                "source": source,
                "company": feedback_data.get('company', ''),
                "role": feedback_data.get('role', ''),
                "identified_reasons": [
                    "Unable to perform detailed analysis",
                    "Consider reviewing the feedback manually"
                ],
                "skill_gaps": ["Technical skills assessment needed"],
                "behavioral_gaps": ["Communication assessment needed"],
                "resume_issues": ["Resume review recommended"],
                "technical_gaps": ["Technical assessment needed"],
                "strengths_detected": ["Persistence in job search", "Openness to feedback"],
                "confidence_level": "low",
                "recommended_actions": [
                    "Review the feedback carefully",
                    "Identify specific areas mentioned",
                    "Create a targeted improvement plan",
                    "Practice mock interviews",
                    "Update resume based on feedback"
                ],
                "learning_plan": [
                    {"area": "Technical Skills", "action": "Review fundamentals", "timeline": "2 weeks"},
                    {"area": "Interview Skills", "action": "Practice with peers", "timeline": "1 week"}
                ],
                "project_suggestions": [
                    "Build a portfolio project related to target role",
                    "Contribute to open source"
                ],
                "resume_improvements": [
                    "Add quantified achievements",
                    "Tailor to target role"
                ],
                "next_steps": [
                    "Re-read feedback for specific insights",
                    "Update skills inventory",
                    "Practice identified weak areas"
                ],
                "readiness_score": 50,
                "summary_message": "We couldn't perform a detailed AI analysis at this time. Please review the feedback manually and focus on any specific areas mentioned. Every setback is a learning opportunity!"
            },
            "processing_time_ms": processing_time
        }
    
    def analyze_for_save(
        self,
        feedback_data: Dict,
        user_profile: Optional[Dict] = None,
        user_skills: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Analyze feedback and return data ready for database storage.
        This is a convenience wrapper around comprehensive_feedback_analysis.
        
        Returns data formatted for the feedback_analysis table.
        """
        result = self.comprehensive_feedback_analysis(
            feedback_data=feedback_data,
            user_profile=user_profile,
            user_skills=user_skills
        )
        
        if result.get('status') != 'success':
            return result
        
        analysis = result.get('analysis', {})
        
        # Format for database storage
        return {
            "status": "success",
            "data_for_save": {
                "source": analysis.get('source', 'unknown'),
                "company": analysis.get('company'),
                "role": analysis.get('role'),
                "original_message": feedback_data.get('message', ''),
                "identified_reasons": analysis.get('identified_reasons', []),
                "skill_gaps": analysis.get('skill_gaps', []),
                "behavioral_gaps": analysis.get('behavioral_gaps', []),
                "resume_issues": analysis.get('resume_issues', []),
                "technical_gaps": analysis.get('technical_gaps', []),
                "strengths_detected": analysis.get('strengths_detected', []),
                "confidence_level": analysis.get('confidence_level', 'medium'),
                "readiness_score": analysis.get('readiness_score', 50),
                "recommended_actions": analysis.get('recommended_actions', []),
                "learning_plan": analysis.get('learning_plan', []),
                "project_suggestions": analysis.get('project_suggestions', []),
                "resume_improvements": analysis.get('resume_improvements', []),
                "next_steps": analysis.get('next_steps', []),
                "summary_message": analysis.get('summary_message', '')
            },
            "analysis": analysis,
            "processing_time_ms": result.get('processing_time_ms', 0)
        }

    def _fallback_rejection_analysis(self, rejection_data: Dict) -> Dict[str, Any]:
        """Fallback rejection analysis"""
        return {
            "agent": self.name,
            "status": "fallback",
            "analysis": {
                "rejection_analysis": {
                    "likely_reasons": ["Competition was strong", "Skill mismatch possible"],
                    "skill_gaps_identified": ["Further assessment needed"]
                },
                "action_items": [
                    {"action": "Review job requirements", "priority": "high", "timeline": "This week"},
                    {"action": "Practice technical skills", "priority": "high", "timeline": "Ongoing"}
                ],
                "skills_to_focus": ["Technical fundamentals", "Communication"],
                "encouragement": "Every rejection is a step closer to the right opportunity. Keep learning and improving!",
                "next_steps": ["Continue learning", "Apply to similar roles", "Seek feedback"]
            }
        }
    
    def _fallback_patterns(self, history: List) -> Dict:
        """Fallback pattern analysis"""
        return {
            "recurring_themes": [{"theme": "Competitive market", "frequency": "Common", "severity": "significant"}],
            "skill_gaps_pattern": ["Technical depth"],
            "strength_patterns": ["Persistence", "Learning attitude"],
            "priority_improvements": ["Focus on core skills", "Practice interviewing"],
            "summary": "Based on limited data. Continue tracking for better insights."
        }
    
    def _fallback_progress(self, progress: Dict) -> Dict:
        """Fallback progress analysis"""
        rate = progress.get('completion_rate', 50)
        status = "on_track" if rate >= 70 else "needs_attention" if rate >= 40 else "behind"
        
        return {
            "progress_assessment": {
                "overall_status": status,
                "completion_rate_analysis": f"{rate}% completion rate",
                "pace_analysis": "Steady progress"
            },
            "achievements": ["Making progress on learning goals"],
            "momentum_tips": ["Stay consistent", "Celebrate small wins"],
            "next_week_focus": ["Continue current tasks", "Review completed work"]
        }
    
    def _fallback_report(self, user_data: Dict) -> Dict:
        """Fallback weekly report"""
        return {
            "report_title": f"Week {user_data.get('current_week', 1)} Progress Report",
            "week_summary": "Keep up the good work on your career journey!",
            "key_accomplishments": user_data.get('tasks_completed', ["Continued learning"]),
            "readiness_change": {"trend": "improving"},
            "insights": ["Consistent effort leads to results"],
            "next_week_preview": {
                "focus_areas": ["Continue current path"],
                "goals": ["Complete weekly tasks"],
                "recommendations": ["Stay focused and motivated"]
            },
            "motivation_message": "You're making progress every day. Keep going!",
            "agent_thoughts": "Steady progress is the key to success."
        }


# Global instance
feedback_agent = FeedbackAgent()
