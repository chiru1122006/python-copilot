"""
Planner Agent
Creates learning roadmaps and weekly plans from skill gaps
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_client import llm
from typing import Dict, List, Any
from datetime import datetime, timedelta


class PlannerAgent:
    """
    The Planner Agent is responsible for:
    1. Converting skill gaps into actionable roadmaps
    2. Creating weekly learning plans
    3. Suggesting projects and milestones
    4. Estimating timelines
    """
    
    SYSTEM_PROMPT = """You are an expert learning path architect and career development planner. Your role is to:
1. Create realistic, actionable learning roadmaps
2. Break down skill acquisition into manageable weekly plans
3. Suggest hands-on projects to reinforce learning
4. Set achievable milestones

Consider learning curves, prerequisite skills, and practical application in your planning.
Plans should be specific, measurable, and achievable."""
    
    def __init__(self):
        self.name = "PlannerAgent"
    
    def create_roadmap(self, skill_gaps: List[Dict], target_role: str, 
                       timeline: str = "3 months") -> Dict[str, Any]:
        """
        Create a complete learning roadmap
        
        Args:
            skill_gaps: List of identified skill gaps with priorities
            target_role: Target career role
            timeline: Desired timeline to achieve goal
        
        Returns:
            Complete roadmap with weekly plans
        """
        gaps_str = self._format_gaps(skill_gaps)
        
        prompt = f"""Create a comprehensive learning roadmap:

## Target Role: {target_role}
## Timeline: {timeline}

## Skill Gaps to Address:
{gaps_str}

Create a detailed roadmap in JSON:
{{
    "roadmap_title": "<descriptive title>",
    "target_role": "{target_role}",
    "total_duration": "{timeline}",
    "start_date": "{datetime.now().strftime('%Y-%m-%d')}",
    "phases": [
        {{
            "phase_number": 1,
            "name": "<phase name>",
            "duration": "<e.g., 4 weeks>",
            "focus_areas": ["<skills to learn>"],
            "description": "<what this phase covers>",
            "milestones": ["<measurable outcomes>"]
        }}
    ],
    "weekly_plans": [
        {{
            "week_number": 1,
            "title": "<week title>",
            "description": "<week focus>",
            "tasks": [
                {{"id": 1, "title": "<task>", "type": "<learn|practice|build|review>", "estimated_hours": <hours>}}
            ],
            "milestones": ["<what to achieve this week>"],
            "resources": ["<suggested resources>"],
            "project_ideas": ["<hands-on project suggestions>"],
            "ai_notes": "<personalized advice for this week>"
        }}
    ],
    "capstone_project": {{
        "title": "<project name>",
        "description": "<what to build>",
        "skills_demonstrated": ["<skills>"],
        "estimated_duration": "<time needed>"
    }},
    "success_metrics": ["<how to measure progress>"],
    "tips": ["<general advice for success>"]
}}

Create at least {max(4, int(timeline.split()[0]) if timeline.split()[0].isdigit() else 12)} weekly plans."""
        
        result = llm.call_json(prompt, self.SYSTEM_PROMPT, temperature=0.5)
        
        if not result:
            return self._fallback_roadmap(skill_gaps, target_role, timeline)
        
        return {
            "agent": self.name,
            "status": "success",
            "roadmap": result
        }
    
    def create_weekly_plan(self, week_number: int, skills_to_learn: List[str],
                           context: Dict = None) -> Dict[str, Any]:
        """
        Create a detailed weekly learning plan
        
        Args:
            week_number: Week number in the roadmap
            skills_to_learn: Skills to focus on this week
            context: Additional context (previous progress, etc.)
        
        Returns:
            Detailed weekly plan
        """
        skills_str = ', '.join(skills_to_learn)
        context_str = f"\nPrevious Progress: {context.get('previous_progress', 'Starting fresh')}" if context else ""
        
        prompt = f"""Create a detailed plan for Week {week_number}:

## Skills to Learn: {skills_str}
{context_str}

Provide a detailed weekly plan in JSON:
{{
    "week_number": {week_number},
    "title": "<catchy week title>",
    "description": "<week overview>",
    "learning_objectives": ["<specific outcomes>"],
    "daily_breakdown": {{
        "day_1_2": {{"focus": "<topic>", "tasks": ["<tasks>"]}},
        "day_3_4": {{"focus": "<topic>", "tasks": ["<tasks>"]}},
        "day_5_6": {{"focus": "<topic>", "tasks": ["<tasks>"]}},
        "day_7": {{"focus": "Review & Practice", "tasks": ["<tasks>"]}}
    }},
    "tasks": [
        {{"id": 1, "title": "<task>", "type": "<type>", "estimated_hours": <hours>, "priority": "<high|medium|low>"}}
    ],
    "resources": [
        {{"title": "<resource name>", "type": "<video|article|course|book>", "url": "<optional url>"}}
    ],
    "practice_exercises": ["<exercises>"],
    "mini_project": {{
        "title": "<project name>",
        "description": "<what to build>",
        "skills_practiced": ["<skills>"]
    }},
    "milestones": ["<checkpoints>"],
    "ai_notes": "<personalized tips and motivation>"
}}"""
        
        result = llm.call_json(prompt, self.SYSTEM_PROMPT, temperature=0.5)
        
        return {
            "agent": self.name,
            "status": "success" if result else "fallback",
            "plan": result or self._fallback_weekly_plan(week_number, skills_to_learn)
        }
    
    def suggest_projects(self, skills: List[str], level: str = "intermediate") -> Dict[str, Any]:
        """
        Suggest portfolio projects based on skills
        
        Args:
            skills: Skills to demonstrate
            level: Difficulty level
        
        Returns:
            Project suggestions
        """
        skills_str = ', '.join(skills)
        
        prompt = f"""Suggest portfolio projects for these skills:

## Skills: {skills_str}
## Level: {level}

Provide project suggestions in JSON:
{{
    "projects": [
        {{
            "title": "<project name>",
            "description": "<what it does>",
            "skills_demonstrated": ["<skills>"],
            "difficulty": "<beginner|intermediate|advanced>",
            "estimated_time": "<duration>",
            "features": ["<key features to implement>"],
            "learning_outcomes": ["<what you'll learn>"],
            "extension_ideas": ["<ways to expand the project>"]
        }}
    ],
    "recommended_order": ["<project names in order of complexity>"],
    "portfolio_tips": ["<tips for showcasing projects>"]
}}

Suggest 3-5 projects of varying complexity."""
        
        result = llm.call_json(prompt, self.SYSTEM_PROMPT, temperature=0.6)
        
        return {
            "agent": self.name,
            "status": "success" if result else "fallback",
            "projects": result or self._fallback_projects(skills)
        }
    
    def adjust_plan(self, current_plan: Dict, feedback: str, progress: Dict) -> Dict[str, Any]:
        """
        Adjust roadmap based on progress and feedback
        
        Args:
            current_plan: Current roadmap/plan
            feedback: User feedback or system observations
            progress: Progress data
        
        Returns:
            Adjusted plan
        """
        prompt = f"""Adjust this learning plan based on progress:

## Current Plan:
{self._format_plan_summary(current_plan)}

## Progress:
- Completed: {progress.get('completed', [])}
- In Progress: {progress.get('in_progress', [])}
- Skipped: {progress.get('skipped', [])}
- Completion Rate: {progress.get('completion_rate', 0)}%

## Feedback:
{feedback}

Provide adjusted plan in JSON:
{{
    "adjustments": [
        {{"type": "<extend|remove|add|reorder>", "item": "<what>", "reason": "<why>"}}
    ],
    "revised_timeline": "<if timeline changes>",
    "new_focus_areas": ["<adjusted priorities>"],
    "removed_items": ["<items to skip>"],
    "additional_support": ["<extra resources or tasks>"],
    "motivation_note": "<encouragement based on progress>",
    "next_steps": ["<immediate next actions>"]
}}"""
        
        result = llm.call_json(prompt, self.SYSTEM_PROMPT, temperature=0.4)
        
        return {
            "agent": self.name,
            "status": "success" if result else "fallback",
            "adjustments": result or {"message": "No adjustments needed"}
        }
    
    def _format_gaps(self, gaps: List[Dict]) -> str:
        """Format skill gaps for prompt"""
        if not gaps:
            return "No specific gaps identified"
        
        formatted = []
        for gap in gaps:
            if isinstance(gap, dict):
                name = gap.get('skill_name', 'Unknown')
                priority = gap.get('priority', 'medium')
                current = gap.get('current_level', 'none')
                formatted.append(f"- {name} (Priority: {priority}, Current: {current})")
            else:
                formatted.append(f"- {gap}")
        
        return '\n'.join(formatted)
    
    def _format_plan_summary(self, plan: Dict) -> str:
        """Format plan summary for prompt"""
        if not plan:
            return "No current plan"
        
        title = plan.get('title', plan.get('roadmap_title', 'Learning Plan'))
        weeks = len(plan.get('weekly_plans', []))
        phases = len(plan.get('phases', []))
        
        return f"Title: {title}\nWeeks: {weeks}\nPhases: {phases}"
    
    def _fallback_roadmap(self, skill_gaps: List, target_role: str, timeline: str) -> Dict[str, Any]:
        """Fallback roadmap generation"""
        weeks = 12  # Default to 12 weeks
        if timeline:
            parts = timeline.split()
            if parts[0].isdigit():
                weeks = int(parts[0])
                if 'month' in timeline.lower():
                    weeks *= 4
        
        weekly_plans = []
        gap_names = [g.get('skill_name', str(g)) if isinstance(g, dict) else str(g) for g in skill_gaps]
        
        for i in range(min(weeks, 12)):
            skill_index = i % len(gap_names) if gap_names else 0
            current_skill = gap_names[skill_index] if gap_names else "General Skills"
            
            weekly_plans.append({
                "week_number": i + 1,
                "title": f"Week {i + 1}: {current_skill}",
                "description": f"Focus on building {current_skill} skills",
                "tasks": [
                    {"id": 1, "title": f"Study {current_skill} fundamentals", "type": "learn", "estimated_hours": 5},
                    {"id": 2, "title": f"Practice {current_skill}", "type": "practice", "estimated_hours": 3},
                    {"id": 3, "title": "Build mini-project", "type": "build", "estimated_hours": 4}
                ],
                "milestones": [f"Understand {current_skill} basics", "Complete practice exercises"],
                "ai_notes": "Focus on understanding core concepts before moving to advanced topics."
            })
        
        return {
            "agent": self.name,
            "status": "fallback",
            "roadmap": {
                "roadmap_title": f"Path to {target_role}",
                "target_role": target_role,
                "total_duration": timeline,
                "start_date": datetime.now().strftime('%Y-%m-%d'),
                "phases": [
                    {"phase_number": 1, "name": "Foundation", "duration": f"{weeks // 3} weeks", "focus_areas": gap_names[:3]},
                    {"phase_number": 2, "name": "Building", "duration": f"{weeks // 3} weeks", "focus_areas": gap_names[3:6] if len(gap_names) > 3 else gap_names},
                    {"phase_number": 3, "name": "Mastery", "duration": f"{weeks // 3} weeks", "focus_areas": ["Projects", "Portfolio"]}
                ],
                "weekly_plans": weekly_plans,
                "success_metrics": ["Complete all weekly tasks", "Build portfolio projects", "Practice interviews"],
                "tips": ["Stay consistent", "Build projects", "Join communities"]
            }
        }
    
    def _fallback_weekly_plan(self, week: int, skills: List) -> Dict:
        """Fallback weekly plan"""
        skill = skills[0] if skills else "General Skills"
        return {
            "week_number": week,
            "title": f"Week {week}: {skill}",
            "description": f"Focus on {skill} development",
            "tasks": [
                {"id": 1, "title": f"Study {skill}", "type": "learn", "estimated_hours": 5},
                {"id": 2, "title": "Practice exercises", "type": "practice", "estimated_hours": 3},
                {"id": 3, "title": "Build project", "type": "build", "estimated_hours": 4}
            ],
            "milestones": [f"Understand {skill} fundamentals"],
            "ai_notes": "Take it step by step and focus on practical application."
        }
    
    def _fallback_projects(self, skills: List) -> Dict:
        """Fallback project suggestions"""
        return {
            "projects": [
                {
                    "title": "Portfolio Website",
                    "description": "Build a personal portfolio showcasing your skills",
                    "skills_demonstrated": skills[:3] if skills else ["Web Development"],
                    "difficulty": "beginner",
                    "estimated_time": "1-2 weeks"
                },
                {
                    "title": "Task Management App",
                    "description": "Full-stack app with CRUD operations",
                    "skills_demonstrated": skills if skills else ["Full Stack"],
                    "difficulty": "intermediate",
                    "estimated_time": "2-3 weeks"
                }
            ],
            "recommended_order": ["Portfolio Website", "Task Management App"]
        }


# Global instance
planner_agent = PlannerAgent()
