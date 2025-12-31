"""
Agent Orchestrator
The central brain that coordinates all agents and manages the agentic loop

AGENTIC LOOP: observe → reason → plan → act → store → adapt
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from typing import Dict, Any, List, Optional
from datetime import datetime

# Import database with error handling
try:
    from database import db
except Exception as e:
    print(f"Orchestrator: Database import error: {e}")
    db = None

# Import agents with error handling
try:
    from agents import (
        reasoning_agent, 
        skill_gap_agent, 
        planner_agent, 
        feedback_agent,
        get_embedding_generator
    )
except Exception as e:
    print(f"Orchestrator: Agents import error: {e}")
    reasoning_agent = None
    skill_gap_agent = None
    planner_agent = None
    feedback_agent = None
    def get_embedding_generator():
        return None


class AgentOrchestrator:
    """
    The Agent Orchestrator is the brain of the system.
    It:
    1. Observes user state
    2. Reasons about next steps
    3. Calls appropriate agents
    4. Stores results
    5. Updates roadmaps
    6. Returns responses
    """
    
    def __init__(self):
        self.name = "AgentOrchestrator"
        self.current_user_id = None
        self.session_memory = {}
    
    def observe_user_state(self, user_id: int) -> Dict[str, Any]:
        """
        Gather complete user state for reasoning
        
        Args:
            user_id: The user's ID
        
        Returns:
            Complete user state dictionary
        """
        self.current_user_id = user_id
        
        # Gather all user data
        user = db.get_user_profile(user_id)
        skills = db.get_user_skills(user_id)
        goals = db.get_user_goals(user_id)
        primary_goal = db.get_primary_goal(user_id)
        skill_gaps = db.get_skill_gaps(user_id, primary_goal['id'] if primary_goal else None)
        plans = db.get_user_plans(user_id, primary_goal['id'] if primary_goal else None)
        feedback = db.get_user_feedback(user_id, limit=5)
        applications = db.get_applications(user_id)
        
        state = {
            "user_id": user_id,
            "profile": user,
            "skills": skills,
            "goals": goals,
            "primary_goal": primary_goal,
            "skill_gaps": skill_gaps,
            "plans": plans,
            "recent_feedback": feedback,
            "applications": applications,
            "stats": self._calculate_stats(plans, applications, feedback)
        }
        
        # Store in session memory
        self.session_memory[user_id] = state
        
        return state
    
    def _calculate_stats(self, plans: List, applications: List, feedback: List) -> Dict:
        """Calculate user statistics"""
        total_tasks = 0
        completed_tasks = 0
        
        for plan in plans:
            tasks = plan.get('tasks', [])
            total_tasks += len(tasks)
            completed_tasks += sum(1 for t in tasks if t.get('completed'))
        
        return {
            "total_plans": len(plans),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": round(completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "total_applications": len(applications),
            "active_applications": len([a for a in applications if a.get('status') in ['applied', 'interviewing']]),
            "feedback_count": len(feedback)
        }
    
    def reason_next_action(self, user_state: Dict) -> Dict[str, Any]:
        """
        Determine the next best action for the user
        
        Args:
            user_state: Current user state
        
        Returns:
            Recommended action with reasoning
        """
        # Analyze current state
        has_goal = bool(user_state.get('primary_goal'))
        has_skills = bool(user_state.get('skills'))
        has_gaps = bool(user_state.get('skill_gaps'))
        has_plan = bool(user_state.get('plans'))
        stats = user_state.get('stats', {})
        
        # Decision logic
        if not has_goal:
            return {
                "action": "set_goal",
                "priority": "critical",
                "message": "Set your career goal to get personalized guidance",
                "agent_to_call": None
            }
        
        if not has_skills or len(user_state.get('skills', [])) < 3:
            return {
                "action": "add_skills",
                "priority": "high",
                "message": "Add more skills to your profile for accurate analysis",
                "agent_to_call": None
            }
        
        if not has_gaps:
            return {
                "action": "analyze_gaps",
                "priority": "high",
                "message": "Let's analyze your skill gaps for your target role",
                "agent_to_call": "skill_gap_agent"
            }
        
        if not has_plan:
            return {
                "action": "create_plan",
                "priority": "high",
                "message": "Time to create your personalized learning roadmap",
                "agent_to_call": "planner_agent"
            }
        
        # Check progress
        if stats.get('completion_rate', 0) < 50 and stats.get('total_tasks', 0) > 5:
            return {
                "action": "review_progress",
                "priority": "medium",
                "message": "Let's review your progress and adjust the plan if needed",
                "agent_to_call": "feedback_agent"
            }
        
        # Default: continue with current plan
        return {
            "action": "continue_learning",
            "priority": "normal",
            "message": "Keep up the great work! Focus on your current tasks.",
            "agent_to_call": None
        }
    
    def run_full_analysis(self, user_id: int) -> Dict[str, Any]:
        """
        Run a complete analysis for a user
        
        Args:
            user_id: The user's ID
        
        Returns:
            Comprehensive analysis results
        """
        # Create session record
        session_id = db.create_agent_session(user_id, 'full_analysis', {'user_id': user_id})
        
        try:
            # 1. Observe state
            state = self.observe_user_state(user_id)
            
            # 2. Run reasoning agent
            profile_data = {
                **state.get('profile', {}),
                'skills': state.get('skills', []),
                'target_role': state.get('primary_goal', {}).get('target_role')
            }
            reasoning_result = reasoning_agent.analyze_profile(profile_data)
            
            # 3. Run skill gap analysis
            target_role = state.get('primary_goal', {}).get('target_role', 'Software Developer')
            gap_result = skill_gap_agent.analyze_gaps(state.get('skills', []), target_role)
            
            # 4. Get next action recommendation
            next_action = self.reason_next_action(state)
            
            # 5. Generate insights
            insights = self._generate_insights(state, reasoning_result, gap_result)
            
            # Compile results
            result = {
                "status": "success",
                "user_id": user_id,
                "readiness_score": reasoning_result.get('analysis', {}).get('readiness_score', 0),
                "reasoning": reasoning_result,
                "skill_gaps": gap_result,
                "next_action": next_action,
                "insights": insights,
                "stats": state.get('stats', {}),
                "agent_thoughts": self._generate_thoughts(state, reasoning_result)
            }
            
            # Update readiness score
            if reasoning_result.get('analysis', {}).get('readiness_score'):
                db.update_readiness_score(user_id, reasoning_result['analysis']['readiness_score'])
            
            # Store memory
            self._store_analysis_memory(user_id, result)
            
            # Update session
            db.update_agent_session(session_id, result, result.get('agent_thoughts', ''))
            
            return result
            
        except Exception as e:
            error_result = {"status": "error", "message": str(e)}
            db.update_agent_session(session_id, error_result, str(e), 'failed')
            return error_result
    
    def analyze_and_plan(self, user_id: int) -> Dict[str, Any]:
        """
        Analyze skill gaps and create a learning plan
        
        Args:
            user_id: The user's ID
        
        Returns:
            Skill gaps and generated plan
        """
        state = self.observe_user_state(user_id)
        
        # Get target role
        primary_goal = state.get('primary_goal', {})
        target_role = primary_goal.get('target_role', 'Software Developer')
        timeline = primary_goal.get('timeline', '3 months')
        
        # Analyze gaps
        gap_result = skill_gap_agent.analyze_gaps(state.get('skills', []), target_role)
        
        # Extract gaps for planning
        skill_gaps = gap_result.get('analysis', {}).get('skill_gaps', [])
        
        # Create roadmap
        roadmap_result = planner_agent.create_roadmap(skill_gaps, target_role, timeline)
        
        # Save gaps to database
        if primary_goal.get('id') and skill_gaps:
            db.save_skill_gaps(user_id, primary_goal['id'], skill_gaps)
        
        # Save plans to database
        weekly_plans = roadmap_result.get('roadmap', {}).get('weekly_plans', [])
        for plan in weekly_plans:
            db.save_plan(user_id, primary_goal.get('id'), plan)
        
        return {
            "status": "success",
            "skill_gaps": gap_result,
            "roadmap": roadmap_result,
            "saved_plans": len(weekly_plans)
        }
    
    def process_feedback(self, user_id: int, feedback_data: Dict) -> Dict[str, Any]:
        """
        Process new feedback and update recommendations
        
        Args:
            user_id: The user's ID
            feedback_data: Feedback details
        
        Returns:
            Feedback analysis and updated recommendations
        """
        # Analyze the feedback
        if feedback_data.get('source') == 'rejection':
            analysis = feedback_agent.analyze_rejection(feedback_data)
        else:
            analysis = feedback_agent.analyze_interview_feedback(feedback_data)
        
        # Save feedback
        feedback_data['analysis'] = analysis.get('analysis', {}).get('rejection_analysis', {})
        feedback_data['action_items'] = analysis.get('analysis', {}).get('action_items', [])
        db.save_feedback(user_id, feedback_data)
        
        # Store in memory
        content = f"Feedback from {feedback_data.get('company', 'Unknown')}: {feedback_data.get('message', '')}"
        embedding = get_embedding_generator().generate(content)
        db.save_memory(user_id, content, embedding, 'feedback', {'analysis': analysis})
        
        # Get patterns if enough history
        history = db.get_user_feedback(user_id, limit=10)
        patterns = None
        if len(history) >= 3:
            patterns = feedback_agent.detect_patterns(history)
        
        return {
            "status": "success",
            "analysis": analysis,
            "patterns": patterns,
            "roadmap_updates": analysis.get('analysis', {}).get('roadmap_updates', [])
        }
    
    def get_dashboard_data(self, user_id: int) -> Dict[str, Any]:
        """
        Get all data needed for the dashboard
        
        Args:
            user_id: The user's ID
        
        Returns:
            Dashboard data package
        """
        state = self.observe_user_state(user_id)
        
        # Get readiness analysis
        profile = state.get('profile', {})
        skills = state.get('skills', [])
        primary_goal = state.get('primary_goal', {})
        
        # Calculate readiness if we have enough data
        readiness = None
        if skills and primary_goal:
            readiness = reasoning_agent.calculate_readiness(
                skills, 
                primary_goal.get('target_role', 'Software Developer')
            )
        
        # Get current plan progress
        plans = state.get('plans', [])
        current_plan = None
        for plan in plans:
            if plan.get('status') in ['pending', 'in_progress']:
                current_plan = plan
                break
        
        # Get next action
        next_action = self.reason_next_action(state)
        
        # Get insights
        insights = self._generate_insights(state, readiness, None)
        
        return {
            "user": {
                "name": profile.get('name', 'User'),
                "career_goal": profile.get('career_goal'),
                "current_level": profile.get('current_level'),
                "readiness_score": profile.get('readiness_score', 0)
            },
            "target_role": primary_goal.get('target_role') if primary_goal else None,
            "readiness": readiness.get('readiness') if readiness else None,
            "stats": state.get('stats', {}),
            "skill_gaps_count": len(state.get('skill_gaps', [])),
            "current_plan": current_plan,
            "next_action": next_action,
            "insights": insights,
            "recent_feedback": state.get('recent_feedback', [])[:3],
            "applications_summary": {
                "total": len(state.get('applications', [])),
                "active": len([a for a in state.get('applications', []) if a.get('status') in ['applied', 'interviewing']])
            }
        }
    
    def get_opportunity_matches(self, user_id: int) -> Dict[str, Any]:
        """
        Get job opportunities matched to user profile
        
        Args:
            user_id: The user's ID
        
        Returns:
            Matched opportunities with scores
        """
        state = self.observe_user_state(user_id)
        user_skills = state.get('skills', [])
        
        # Get opportunities
        opportunities = db.get_opportunities()
        
        # Calculate match for each
        matched = []
        for opp in opportunities:
            requirements = opp.get('requirements', [])
            if requirements:
                comparison = skill_gap_agent.compare_with_job(user_skills, requirements)
                match_data = comparison.get('comparison', {})
                matched.append({
                    **opp,
                    'match_percentage': match_data.get('match_percentage', 0),
                    'matching_skills': match_data.get('matching_skills', []),
                    'missing_skills': match_data.get('missing_skills', [])
                })
            else:
                matched.append({**opp, 'match_percentage': 50})
        
        # Sort by match percentage
        matched.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        return {
            "status": "success",
            "opportunities": matched,
            "total": len(matched)
        }
    
    def _generate_insights(self, state: Dict, reasoning: Dict, gaps: Dict) -> List[str]:
        """Generate AI insights from analysis"""
        insights = []
        
        stats = state.get('stats', {})
        
        if stats.get('completion_rate', 0) >= 80:
            insights.append("🎉 Excellent progress! You're ahead of schedule.")
        elif stats.get('completion_rate', 0) >= 50:
            insights.append("👍 Good progress! Keep up the momentum.")
        elif stats.get('completion_rate', 0) > 0:
            insights.append("💪 You're making progress. Try to pick up the pace a bit.")
        
        skill_gaps = state.get('skill_gaps', [])
        high_priority = [g for g in skill_gaps if g.get('priority') == 'high']
        if high_priority:
            insights.append(f"🎯 Focus on {len(high_priority)} high-priority skills for your target role.")
        
        if reasoning and reasoning.get('analysis', {}).get('readiness_score', 0) >= 70:
            insights.append("🚀 You're getting close to job-ready! Consider applying soon.")
        
        applications = state.get('applications', [])
        active = [a for a in applications if a.get('status') in ['applied', 'interviewing']]
        if active:
            insights.append(f"📝 You have {len(active)} active application(s). Good luck!")
        
        return insights if insights else ["Keep learning and building your skills!"]
    
    def _generate_thoughts(self, state: Dict, reasoning: Dict) -> str:
        """Generate agent thought summary"""
        profile = state.get('profile', {})
        goal = state.get('primary_goal', {})
        stats = state.get('stats', {})
        
        thoughts = []
        thoughts.append(f"Analyzed profile for {profile.get('name', 'user')}.")
        
        if goal:
            thoughts.append(f"Target role: {goal.get('target_role')}.")
        
        if reasoning and reasoning.get('analysis'):
            score = reasoning['analysis'].get('readiness_score', 0)
            thoughts.append(f"Career readiness: {score}%.")
        
        if stats.get('completion_rate', 0) > 0:
            thoughts.append(f"Task completion: {stats['completion_rate']}%.")
        
        return " ".join(thoughts)
    
    def _store_analysis_memory(self, user_id: int, result: Dict):
        """Store analysis result in memory"""
        content = f"Full analysis completed. Readiness: {result.get('readiness_score', 0)}%."
        if result.get('next_action'):
            content += f" Next action: {result['next_action'].get('action')}."
        
        embedding = get_embedding_generator().generate(content)
        db.save_memory(user_id, content, embedding, 'reasoning', {'result_summary': True})
    
    # ==========================================
    # UNIFIED AGENTIC LOOP
    # ==========================================
    
    def run_agent(self, event_type: str, user_id: int, payload: Dict = None) -> Dict[str, Any]:
        """
        UNIFIED AGENT LOOP: observe → reason → plan → act → store → adapt
        
        This is the main entry point for ALL agent operations.
        
        Args:
            event_type: Type of event triggering the agent
                - 'skill_gap': Analyze skill gaps
                - 'roadmap': Generate/update roadmap
                - 'feedback': Process feedback
                - 'profile_update': Profile was updated
                - 'application': Application-related action
                - 'full_analysis': Complete analysis
            user_id: User ID
            payload: Additional data for the event
        
        Returns:
            Agent response with results and metadata
        """
        payload = payload or {}
        session_id = db.create_agent_session(user_id, event_type, payload)
        
        try:
            # ====== OBSERVE ======
            state = self.observe_user_state(user_id)
            memories = self._retrieve_relevant_memories(user_id, event_type)
            
            # ====== REASON ======
            reasoning_context = {
                'state': state,
                'memories': memories,
                'event': event_type,
                'payload': payload
            }
            
            # ====== PLAN & ACT ======
            if event_type == 'skill_gap':
                result = self._handle_skill_gap_event(state, payload)
            elif event_type == 'roadmap':
                result = self._handle_roadmap_event(state, payload)
            elif event_type == 'feedback':
                result = self._handle_feedback_event(user_id, state, payload)
            elif event_type == 'profile_update':
                result = self._handle_profile_update_event(user_id, state, payload)
            elif event_type == 'application' or event_type == 'apply_role':
                result = self._handle_application_event(user_id, state, payload)
            elif event_type == 'interview_prep':
                result = self._handle_interview_prep_event(user_id, state, payload)
            elif event_type == 'full_analysis':
                result = self.run_full_analysis(user_id)
            else:
                result = {"status": "unknown_event", "message": f"Unknown event type: {event_type}"}
            
            # ====== STORE ======
            self._store_agent_result(user_id, event_type, result)
            
            # ====== ADAPT ======
            # Check if we need to trigger cascading updates
            if event_type in ['profile_update', 'feedback'] and result.get('status') == 'success':
                # Auto-trigger roadmap regeneration
                if state.get('skill_gaps'):
                    self._trigger_roadmap_update(user_id, state)
            
            # Update session
            db.update_agent_session(session_id, result, result.get('agent_thoughts', ''))
            
            return {
                "status": "success",
                "event": event_type,
                "result": result,
                "agent_state": {
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id
                }
            }
            
        except Exception as e:
            import traceback
            error_result = {
                "status": "error", 
                "message": str(e),
                "traceback": traceback.format_exc()
            }
            db.update_agent_session(session_id, error_result, str(e), 'failed')
            return error_result
    
    def _handle_skill_gap_event(self, state: Dict, payload: Dict) -> Dict[str, Any]:
        """Handle skill gap analysis event"""
        skills = state.get('skills', [])
        primary_goal = state.get('primary_goal', {})
        target_role = payload.get('target_role') or primary_goal.get('target_role', 'Software Developer')
        
        # Run skill gap analysis
        gap_result = skill_gap_agent.analyze_gaps(skills, target_role)
        
        # Save gaps to database
        user_id = state.get('user_id')
        goal_id = primary_goal.get('id')
        
        if gap_result.get('status') == 'success' and goal_id:
            gaps = gap_result.get('analysis', {}).get('skill_gaps', [])
            db.save_skill_gaps(user_id, goal_id, gaps)
        
        return {
            "status": "success",
            "analysis": gap_result.get('analysis', {}),
            "skill_gaps": gap_result.get('analysis', {}).get('skill_gaps', []),
            "readiness_percentage": gap_result.get('analysis', {}).get('readiness_percentage', 0),
            "critical_path": gap_result.get('analysis', {}).get('critical_path', []),
            "agent_thoughts": f"Analyzed {len(skills)} skills against {target_role} requirements."
        }
    
    def _handle_roadmap_event(self, state: Dict, payload: Dict) -> Dict[str, Any]:
        """Handle roadmap generation event"""
        user_id = state.get('user_id')
        primary_goal = state.get('primary_goal', {})
        skill_gaps = state.get('skill_gaps', [])
        
        print(f"[ROADMAP] User ID: {user_id}")
        print(f"[ROADMAP] Primary Goal: {primary_goal}")
        print(f"[ROADMAP] Skill Gaps Count: {len(skill_gaps)}")
        
        target_role = payload.get('target_role') or primary_goal.get('target_role', 'Software Developer')
        timeline = payload.get('timeline') or primary_goal.get('timeline', '3 months')
        
        print(f"[ROADMAP] Target Role: {target_role}, Timeline: {timeline}")
        
        # If no skill gaps, run skill gap analysis first
        if not skill_gaps:
            print("[ROADMAP] No skill gaps found, running skill gap analysis...")
            skills = state.get('skills', [])
            print(f"[ROADMAP] Skills Count: {len(skills)}")
            gap_result = skill_gap_agent.analyze_gaps(skills, target_role)
            skill_gaps = gap_result.get('analysis', {}).get('skill_gaps', [])
            print(f"[ROADMAP] Generated {len(skill_gaps)} skill gaps")
            
            # Save gaps
            if primary_goal.get('id'):
                db.save_skill_gaps(user_id, primary_goal['id'], skill_gaps)
                print(f"[ROADMAP] Saved skill gaps to database")
        
        print(f"[ROADMAP] Generating roadmap with {len(skill_gaps)} gaps...")
        # Generate roadmap
        roadmap_result = planner_agent.create_roadmap(skill_gaps, target_role, timeline)
        
        print(f"[ROADMAP] Roadmap Result Status: {roadmap_result.get('status')}")
        
        # Save plans to database
        weekly_plans = roadmap_result.get('roadmap', {}).get('weekly_plans', [])
        
        print(f"[ROADMAP] Weekly Plans Count: {len(weekly_plans)}")
        
        # Clear existing plans for this goal
        if primary_goal.get('id'):
            db.clear_plans(user_id, primary_goal['id'])
            print(f"[ROADMAP] Cleared existing plans")
        
        # Save new plans
        for plan in weekly_plans:
            db.save_plan(user_id, primary_goal.get('id'), plan)
        
        print(f"[ROADMAP] Saved {len(weekly_plans)} plans to database")
        
        return {
            "status": "success",
            "roadmap": roadmap_result.get('roadmap', {}),
            "weekly_plans": weekly_plans,
            "total_weeks": len(weekly_plans),
            "agent_thoughts": f"Created {len(weekly_plans)}-week roadmap for {target_role}."
        }
    
    def _handle_feedback_event(self, user_id: int, state: Dict, payload: Dict) -> Dict[str, Any]:
        """Handle feedback processing event"""
        feedback_data = payload.get('feedback', payload)
        feedback_id = feedback_data.get('feedback_id')
        
        # Analyze feedback
        if feedback_data.get('source') == 'rejection':
            analysis = feedback_agent.analyze_rejection(feedback_data)
        else:
            analysis = feedback_agent.analyze_interview_feedback(feedback_data)
        
        # Extract the analysis dict
        analysis_result = analysis.get('analysis', {})
        
        # If we have a feedback_id, update that specific record
        if feedback_id:
            # Use the proper update method that serializes correctly
            db.update_feedback_analysis(feedback_id, analysis_result)
            
            # Log the AI feedback for debugging
            try:
                db.save_ai_feedback_log(
                    user_id, 
                    feedback_id, 
                    f"Analyze {feedback_data.get('source', 'feedback')}", 
                    analysis_result,
                    0  # token usage
                )
            except Exception as e:
                print(f"Failed to save AI feedback log: {e}")
        else:
            # Save new feedback entry with properly serialized analysis
            feedback_to_save = {
                'source': feedback_data.get('source', 'interview'),
                'company': feedback_data.get('company'),
                'role': feedback_data.get('role'),
                'message': feedback_data.get('message', ''),
                'analysis': analysis_result,
                'sentiment': analysis_result.get('sentiment', 'neutral'),
                'action_items': analysis_result.get('action_items', analysis_result.get('skills_to_focus', []))
            }
            db.save_feedback(user_id, feedback_to_save)
        
        # Store in memory for future context
        content = f"Feedback: {feedback_data.get('source', 'interview')} from {feedback_data.get('company', 'Unknown')}"
        embedding = get_embedding_generator().generate(content)
        db.save_memory(user_id, content, embedding, 'feedback', {'analysis_summary': 'Feedback analyzed'})
        
        # Log career event
        try:
            db.save_career_event(user_id, 'feedback_received', {
                'source': feedback_data.get('source'),
                'company': feedback_data.get('company'),
                'role': feedback_data.get('role')
            }, f"Received {feedback_data.get('source', 'feedback')} feedback")
        except Exception as e:
            print(f"Failed to save career event: {e}")
        
        # Check for patterns
        history = db.get_user_feedback(user_id, limit=10)
        patterns = None
        if len(history) >= 3:
            patterns = feedback_agent.detect_patterns(history)
        
        # Get roadmap update suggestions (ensure they are strings)
        roadmap_updates = analysis_result.get('roadmap_updates', [])
        if isinstance(roadmap_updates, dict):
            roadmap_updates = [str(roadmap_updates)]
        
        skills_to_focus = analysis_result.get('skills_to_focus', [])
        if isinstance(skills_to_focus, dict):
            skills_to_focus = [str(skills_to_focus)]
        
        return {
            "status": "success",
            "analysis": analysis_result,
            "patterns": patterns,
            "roadmap_updates": roadmap_updates,
            "skills_to_focus": skills_to_focus,
            "should_regenerate_roadmap": len(roadmap_updates) > 0,
            "agent_thoughts": f"Processed feedback and identified {len(skills_to_focus)} skills to focus on."
        }
    
    def _handle_profile_update_event(self, user_id: int, state: Dict, payload: Dict) -> Dict[str, Any]:
        """Handle profile update event - triggers re-analysis"""
        # Run full analysis with new profile data
        analysis_result = self.run_full_analysis(user_id)
        
        # Check if roadmap needs update
        should_update_roadmap = False
        if payload.get('skills_changed') or payload.get('goal_changed'):
            should_update_roadmap = True
        
        return {
            "status": "success",
            "analysis": analysis_result,
            "should_update_roadmap": should_update_roadmap,
            "agent_thoughts": "Profile updated. Re-analyzed career readiness."
        }
    
    def _handle_application_event(self, user_id: int, state: Dict, payload: Dict) -> Dict[str, Any]:
        """Handle application matching event"""
        action = payload.get('action', 'match')
        
        if action == 'match' or not action:
            # Get opportunity matches
            match_result = self.get_opportunity_matches(user_id)
            opportunities = match_result.get('opportunities', [])
            
            # Format for PHP controller
            return {
                "status": "success",
                "opportunities": opportunities,
                "total": len(opportunities),
                "agent_thoughts": f"Found {len(opportunities)} matching opportunities."
            }
        elif action == 'analyze':
            # Analyze specific application
            job_requirements = payload.get('requirements', [])
            user_skills = state.get('skills', [])
            
            comparison = skill_gap_agent.compare_with_job(user_skills, job_requirements)
            
            return {
                "status": "success",
                "match_analysis": comparison.get('comparison', {}),
                "agent_thoughts": f"Analyzed match against job requirements."
            }
        
        return {"status": "success", "message": "Application event processed", "opportunities": []}
    
    def _handle_interview_prep_event(self, user_id: int, state: Dict, payload: Dict) -> Dict[str, Any]:
        """Handle interview preparation suggestions"""
        from llm_client import llm
        
        company = payload.get('company', 'the company')
        role = payload.get('role', 'the position')
        skills = payload.get('skills', state.get('skills', []))
        education = payload.get('education', [])
        experience = payload.get('experience', [])
        
        print(f"[INTERVIEW_PREP] Company: {company}, Role: {role}")
        print(f"[INTERVIEW_PREP] Skills count: {len(skills)}")
        
        # Format user's skills
        skills_str = ', '.join([s.get('skill_name', str(s)) if isinstance(s, dict) else str(s) for s in skills[:15]])
        
        # Format experience
        exp_str = ""
        if experience:
            exp_list = []
            for exp in experience[:3]:
                if isinstance(exp, dict):
                    title = exp.get('title', '')
                    company_name = exp.get('company', '')
                    if title:
                        exp_list.append(f"{title} at {company_name}" if company_name else title)
            if exp_list:
                exp_str = f"\n\nRelevant Experience: {', '.join(exp_list)}"
        
        system_prompt = """You are an expert interview preparation coach. Your role is to:
1. Identify key skills needed for the target role
2. Suggest relevant projects to showcase
3. Provide interview preparation tips specific to the company and role
4. Recommend areas to study and practice

Be specific, actionable, and encouraging."""
        
        prompt = f"""Provide comprehensive interview preparation guidance for:

## Target Position
- Company: {company}
- Role: {role}

## Candidate Profile
- Current Skills: {skills_str}{exp_str}

Provide detailed interview preparation advice in JSON format:
{{
    "key_skills_to_highlight": [
        {{"skill": "<skill name>", "why": "<relevance to role>", "how_to_demonstrate": "<specific example>"}}
    ],
    "suggested_projects": [
        {{
            "title": "<project idea>",
            "description": "<what to build>",
            "skills_demonstrated": ["<skills>"],
            "relevance": "<why this helps for the interview>",
            "complexity": "<beginner|intermediate|advanced>",
            "estimated_time": "<time to complete>"
        }}
    ],
    "technical_topics_to_study": [
        {{"topic": "<topic>", "priority": "<high|medium|low>", "resources": ["<resource suggestions>"]}}
    ],
    "interview_preparation_tips": [
        {{"category": "<behavioral|technical|company-specific>", "tip": "<specific advice>", "why": "<importance>"}}
    ],
    "common_questions": [
        {{"question": "<likely interview question>", "approach": "<how to answer>", "example_points": ["<key points to mention>"]}}
    ],
    "red_flags_to_address": [
        {{"concern": "<potential weakness>", "how_to_address": "<mitigation strategy>"}}
    ],
    "company_culture_prep": {{
        "company_values": "<research about company culture>",
        "questions_to_ask": ["<smart questions for interviewer>"],
        "alignment_points": ["<how your background aligns>"]
    }},
    "30_day_prep_plan": {{
        "week_1": ["<tasks for week 1>"],
        "week_2": ["<tasks for week 2>"],
        "week_3": ["<tasks for week 3>"],
        "week_4": ["<tasks for week 4>"]
    }},
    "confidence_boosters": ["<positive aspects of their profile>"],
    "final_checklist": ["<things to do right before interview>"]
}}

Provide 3-5 items in each category. Be specific to the {role} role at {company}."""
        
        result = llm.call_json(prompt, system_prompt, temperature=0.6, max_tokens=6000)
        
        if not result:
            print("[INTERVIEW_PREP] LLM returned no result, using fallback")
            # Fallback suggestions
            result = self._fallback_interview_prep(company, role, skills)
        else:
            print(f"[INTERVIEW_PREP] Generated suggestions successfully with {len(str(result))} characters")
        
        return {
            "status": "success",
            "suggestions": result,
            "company": company,
            "role": role,
            "agent_thoughts": f"Generated comprehensive interview preparation guide for {role} at {company}."
        }
    
    def _fallback_interview_prep(self, company: str, role: str, skills: List) -> Dict:
        """Fallback interview prep suggestions"""
        skill_names = [s.get('skill_name', str(s)) if isinstance(s, dict) else str(s) for s in skills[:5]]
        
        return {
            "key_skills_to_highlight": [
                {"skill": skill, "why": f"Essential for {role}", "how_to_demonstrate": "Discuss relevant projects"}
                for skill in skill_names[:3]
            ],
            "suggested_projects": [
                {
                    "title": f"{role} Portfolio Project",
                    "description": f"Build a project showcasing skills needed for {role}",
                    "skills_demonstrated": skill_names[:3],
                    "relevance": "Demonstrates practical application",
                    "complexity": "intermediate",
                    "estimated_time": "2-3 weeks"
                }
            ],
            "technical_topics_to_study": [
                {"topic": "Data Structures & Algorithms", "priority": "high", "resources": ["LeetCode", "HackerRank"]},
                {"topic": "System Design", "priority": "medium", "resources": ["System Design Primer"]}
            ],
            "interview_preparation_tips": [
                {"category": "technical", "tip": "Practice coding problems daily", "why": "Builds confidence"},
                {"category": "behavioral", "tip": "Prepare STAR method examples", "why": "Structures your responses"}
            ],
            "common_questions": [
                {"question": "Tell me about yourself", "approach": "Focus on relevant experience", "example_points": ["Background", "Skills", "Why this role"]},
                {"question": f"Why {company}?", "approach": "Show research and alignment", "example_points": ["Company values", "Product interest", "Growth opportunity"]}
            ],
            "red_flags_to_address": [],
            "company_culture_prep": {
                "company_values": f"Research {company}'s mission and values",
                "questions_to_ask": ["What does success look like in this role?", "What are the team dynamics?"],
                "alignment_points": ["Your skills match the role", "You're passionate about their mission"]
            },
            "30_day_prep_plan": {
                "week_1": ["Research company", "Practice common questions", "Review fundamentals"],
                "week_2": ["Work on portfolio project", "Practice technical problems"],
                "week_3": ["Mock interviews", "Refine project"],
                "week_4": ["Final review", "Prepare questions to ask"]
            },
            "confidence_boosters": [
                f"You have {len(skills)} skills in your profile",
                f"Your background aligns with {role} requirements"
            ],
            "final_checklist": [
                "Test your setup (if virtual)",
                "Prepare questions to ask",
                "Review your resume",
                "Get good sleep"
            ]
        }
    
    def _retrieve_relevant_memories(self, user_id: int, context: str) -> List[Dict]:
        """Retrieve relevant memories for context"""
        try:
            # Generate embedding for context
            query_embedding = get_embedding_generator().generate(context)
            
            # Search for similar memories
            memories = db.search_memories(user_id, query_embedding, limit=5)
            return memories
        except Exception as e:
            print(f"Memory retrieval error: {e}")
            return []
    
    def _store_agent_result(self, user_id: int, event_type: str, result: Dict):
        """Store agent result in memory for future context"""
        try:
            content = f"Agent {event_type}: {result.get('agent_thoughts', 'Completed')}"
            embedding = get_embedding_generator().generate(content)
            db.save_memory(user_id, content, embedding, 'agent_result', {
                'event_type': event_type,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Memory storage error: {e}")
    
    def _trigger_roadmap_update(self, user_id: int, state: Dict):
        """Trigger automatic roadmap update after changes"""
        try:
            primary_goal = state.get('primary_goal', {})
            if primary_goal:
                self._handle_roadmap_event(state, {
                    'target_role': primary_goal.get('target_role'),
                    'timeline': primary_goal.get('timeline', '3 months')
                })
        except Exception as e:
            print(f"Roadmap update trigger error: {e}")
    
    def get_agent_state(self, user_id: int) -> Dict[str, Any]:
        """Get current agent state for a user"""
        state = self.observe_user_state(user_id)
        
        return {
            "status": "success",
            "user_id": user_id,
            "has_goal": bool(state.get('primary_goal')),
            "skills_count": len(state.get('skills', [])),
            "gaps_count": len(state.get('skill_gaps', [])),
            "plans_count": len(state.get('plans', [])),
            "feedback_count": len(state.get('recent_feedback', [])),
            "applications_count": len(state.get('applications', [])),
            "readiness_score": state.get('profile', {}).get('readiness_score', 0),
            "stats": state.get('stats', {}),
            "next_action": self.reason_next_action(state)
        }


# Global orchestrator instance
orchestrator = AgentOrchestrator()
