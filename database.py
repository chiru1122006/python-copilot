"""
Database connection and helper functions
"""
import mysql.connector
from mysql.connector import Error
from config import Config
from decimal import Decimal
from datetime import datetime, date
import json


def convert_decimals(obj):
    """Recursively convert Decimal and datetime objects to JSON-serializable types"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    return obj


class Database:
    def __init__(self):
        self.connection = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME
            )
            return self.connection
        except Error as e:
            print(f"Database connection error: {e}")
            return None
    
    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
    
    def execute_query(self, query, params=None, fetch=True):
        """Execute a query and return results"""
        try:
            conn = self.connect()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch:
                result = cursor.fetchall()
                # Convert Decimal and datetime to JSON-serializable types
                result = convert_decimals(result)
            else:
                conn.commit()
                result = cursor.lastrowid
            
            cursor.close()
            self.disconnect()
            return result
        except Error as e:
            print(f"Query execution error: {e}")
            return None
    
    # ==========================================
    # USER METHODS
    # ==========================================
    
    def get_user(self, user_id: int):
        """Get user by ID"""
        query = "SELECT * FROM users WHERE id = %s"
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None
    
    def get_user_profile(self, user_id: int):
        """Get user profile with all details"""
        query = """
            SELECT u.*, up.education, up.experience, up.interests, 
                   up.resume_url, up.resume_text
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.user_id
            WHERE u.id = %s
        """
        result = self.execute_query(query, (user_id,))
        if result:
            user = result[0]
            # Parse JSON fields
            for field in ['education', 'experience', 'interests']:
                if user.get(field):
                    user[field] = json.loads(user[field]) if isinstance(user[field], str) else user[field]
            return user
        return None
    
    def update_readiness_score(self, user_id: int, score: int):
        """Update user's career readiness score"""
        query = "UPDATE users SET readiness_score = %s WHERE id = %s"
        self.execute_query(query, (score, user_id), fetch=False)
    
    # ==========================================
    # SKILLS METHODS
    # ==========================================
    
    def get_user_skills(self, user_id: int):
        """Get all skills for a user"""
        query = "SELECT * FROM skills WHERE user_id = %s ORDER BY level DESC"
        return self.execute_query(query, (user_id,)) or []
    
    def add_skill(self, user_id: int, skill_name: str, level: str, category: str = 'general'):
        """Add or update a skill"""
        query = """
            INSERT INTO skills (user_id, skill_name, level, category)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE level = %s, category = %s
        """
        return self.execute_query(query, (user_id, skill_name, level, category, level, category), fetch=False)
    
    # ==========================================
    # GOALS METHODS
    # ==========================================
    
    def get_user_goals(self, user_id: int):
        """Get all goals for a user"""
        query = "SELECT * FROM goals WHERE user_id = %s AND status = 'active'"
        return self.execute_query(query, (user_id,)) or []
    
    def get_primary_goal(self, user_id: int):
        """Get the primary (highest priority) active goal"""
        query = """
            SELECT * FROM goals 
            WHERE user_id = %s AND status = 'active'
            ORDER BY FIELD(priority, 'high', 'medium', 'low')
            LIMIT 1
        """
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None
    
    # ==========================================
    # SKILL GAPS METHODS
    # ==========================================
    
    def get_skill_gaps(self, user_id: int, goal_id: int = None):
        """Get skill gaps for a user with learning resources"""
        if goal_id:
            query = """SELECT id, skill_name, current_level, required_level, priority, status, 
                              learning_resources, estimated_learning_time, learning_approach 
                       FROM skill_gaps WHERE user_id = %s AND goal_id = %s 
                       ORDER BY FIELD(priority, 'high', 'medium', 'low')"""
            params = (user_id, goal_id)
        else:
            query = """SELECT id, skill_name, current_level, required_level, priority, status,
                              learning_resources, estimated_learning_time, learning_approach 
                       FROM skill_gaps WHERE user_id = %s 
                       ORDER BY FIELD(priority, 'high', 'medium', 'low')"""
            params = (user_id,)
        
        gaps = self.execute_query(query, params) or []
        
        # Parse learning_resources JSON
        for gap in gaps:
            if gap.get('learning_resources'):
                gap['learning_resources'] = json.loads(gap['learning_resources']) if isinstance(gap['learning_resources'], str) else gap['learning_resources']
        
        return gaps
    
    def save_skill_gaps(self, user_id: int, goal_id: int, gaps: list):
        """Save skill gaps for a user with learning resources"""
        # Clear existing gaps for this goal
        delete_query = "DELETE FROM skill_gaps WHERE user_id = %s AND goal_id = %s"
        self.execute_query(delete_query, (user_id, goal_id), fetch=False)
        
        # Insert new gaps with learning resources
        for gap in gaps:
            insert_query = """
                INSERT INTO skill_gaps (user_id, goal_id, skill_name, current_level, required_level, priority, 
                                        learning_resources, estimated_learning_time, learning_approach)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            learning_resources = gap.get('learning_resources', [])
            self.execute_query(insert_query, (
                user_id, goal_id, gap['skill_name'], 
                gap.get('current_level', 'none'),
                gap.get('required_level', 'intermediate'),
                gap.get('priority', 'medium'),
                json.dumps(learning_resources) if learning_resources else None,
                gap.get('estimated_learning_time', None),
                gap.get('learning_approach', None)
            ), fetch=False)
    
    # ==========================================
    # PLANS METHODS
    # ==========================================
    
    def get_user_plans(self, user_id: int, goal_id: int = None):
        """Get learning plans for a user"""
        if goal_id:
            query = "SELECT * FROM plans WHERE user_id = %s AND goal_id = %s ORDER BY week_number"
            params = (user_id, goal_id)
        else:
            query = "SELECT * FROM plans WHERE user_id = %s ORDER BY week_number"
            params = (user_id,)
        
        plans = self.execute_query(query, params) or []
        for plan in plans:
            if plan.get('tasks'):
                plan['tasks'] = json.loads(plan['tasks']) if isinstance(plan['tasks'], str) else plan['tasks']
            if plan.get('milestones'):
                plan['milestones'] = json.loads(plan['milestones']) if isinstance(plan['milestones'], str) else plan['milestones']
        return plans
    
    def save_plan(self, user_id: int, goal_id: int, plan: dict):
        """Save a learning plan"""
        query = """
            INSERT INTO plans (user_id, goal_id, week_number, title, description, tasks, milestones, ai_notes, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                title = VALUES(title), description = VALUES(description),
                tasks = VALUES(tasks), milestones = VALUES(milestones),
                ai_notes = VALUES(ai_notes), status = VALUES(status)
        """
        return self.execute_query(query, (
            user_id, goal_id, plan['week_number'], plan['title'],
            plan.get('description', ''),
            json.dumps(plan.get('tasks', [])),
            json.dumps(plan.get('milestones', [])),
            plan.get('ai_notes', ''),
            plan.get('status', 'pending')
        ), fetch=False)
    
    # ==========================================
    # FEEDBACK METHODS
    # ==========================================
    
    def get_user_feedback(self, user_id: int, limit: int = 10):
        """Get feedback entries for a user"""
        query = "SELECT * FROM feedback WHERE user_id = %s ORDER BY created_at DESC LIMIT %s"
        feedback_list = self.execute_query(query, (user_id, limit)) or []
        for fb in feedback_list:
            if fb.get('action_items'):
                fb['action_items'] = json.loads(fb['action_items']) if isinstance(fb['action_items'], str) else fb['action_items']
        return feedback_list
    
    def save_feedback(self, user_id: int, feedback: dict):
        """Save feedback entry"""
        # Ensure analysis is properly serialized to string
        analysis_text = feedback.get('analysis')
        if isinstance(analysis_text, dict):
            # Convert dict to readable string for analysis column
            if 'rejection_analysis' in analysis_text:
                ra = analysis_text['rejection_analysis']
                analysis_text = ra.get('summary', '') or ra.get('key_issues', ['Analysis completed'])[0] if isinstance(ra.get('key_issues'), list) else str(ra)
            elif 'summary' in analysis_text:
                analysis_text = analysis_text['summary']
            else:
                analysis_text = str(analysis_text)
        
        # Ensure action_items is a list for JSON encoding
        action_items = feedback.get('action_items', [])
        if isinstance(action_items, dict):
            action_items = [action_items]
        
        query = """
            INSERT INTO feedback (user_id, source, company, role, message, analysis, sentiment, action_items)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.execute_query(query, (
            user_id, feedback['source'], feedback.get('company'),
            feedback.get('role'), feedback['message'],
            analysis_text if isinstance(analysis_text, str) else json.dumps(analysis_text),
            feedback.get('sentiment', 'neutral'),
            json.dumps(action_items)
        ), fetch=False)
    
    def update_feedback_analysis(self, feedback_id: int, analysis: dict):
        """Update feedback with AI analysis - properly serialized"""
        # Serialize the analysis properly
        analysis_text = ''
        action_items = []
        sentiment = 'neutral'
        
        if isinstance(analysis, dict):
            # Extract analysis text
            if 'rejection_analysis' in analysis:
                ra = analysis['rejection_analysis']
                if isinstance(ra, dict):
                    parts = []
                    if ra.get('summary'):
                        parts.append(ra['summary'])
                    if ra.get('key_issues') and isinstance(ra.get('key_issues'), list):
                        parts.append("Key issues: " + ", ".join(ra['key_issues'][:3]))
                    analysis_text = " ".join(parts) if parts else "Analysis completed"
                else:
                    analysis_text = str(ra)
            elif 'summary' in analysis:
                analysis_text = analysis['summary']
            else:
                analysis_text = json.dumps(analysis)
            
            # Extract action items
            action_items = analysis.get('action_items', analysis.get('skills_to_focus', []))
            if isinstance(action_items, dict):
                action_items = [action_items.get('action', str(action_items))]
            elif not isinstance(action_items, list):
                action_items = [str(action_items)]
            
            # Extract sentiment
            sentiment = analysis.get('sentiment', 'neutral')
        else:
            analysis_text = str(analysis)
        
        query = """
            UPDATE feedback 
            SET analysis = %s, sentiment = %s, action_items = %s
            WHERE id = %s
        """
        return self.execute_query(query, (
            analysis_text,
            sentiment,
            json.dumps(action_items),
            feedback_id
        ), fetch=False)
    
    def save_ai_feedback_log(self, user_id: int, feedback_id: int, prompt: str, response: dict, token_usage: int = 0):
        """Save AI feedback analysis log for debugging and auditing"""
        # Serialize response properly
        response_text = json.dumps(response) if isinstance(response, dict) else str(response)
        parsed_insights = None
        
        if isinstance(response, dict):
            parsed_insights = json.dumps(response)
        
        query = """
            INSERT INTO ai_feedback_logs (user_id, feedback_id, prompt, response, parsed_insights, token_usage)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return self.execute_query(query, (
            user_id, feedback_id, prompt, response_text, parsed_insights, token_usage
        ), fetch=False)
    
    # ==========================================
    # MEMORY VECTORS METHODS
    # ==========================================
    
    def save_memory(self, user_id: int, content: str, embedding: list, memory_type: str, metadata: dict = None):
        """Save a memory vector"""
        query = """
            INSERT INTO memory_vectors (user_id, content, embedding, type, metadata)
            VALUES (%s, %s, %s, %s, %s)
        """
        return self.execute_query(query, (
            user_id, content, json.dumps(embedding), memory_type,
            json.dumps(metadata) if metadata else None
        ), fetch=False)
    
    def get_memories(self, user_id: int, memory_type: str = None, limit: int = 20):
        """Get memory vectors for a user"""
        if memory_type:
            query = "SELECT * FROM memory_vectors WHERE user_id = %s AND type = %s ORDER BY created_at DESC LIMIT %s"
            params = (user_id, memory_type, limit)
        else:
            query = "SELECT * FROM memory_vectors WHERE user_id = %s ORDER BY created_at DESC LIMIT %s"
            params = (user_id, limit)
        
        memories = self.execute_query(query, params) or []
        for mem in memories:
            if mem.get('embedding'):
                mem['embedding'] = json.loads(mem['embedding']) if isinstance(mem['embedding'], str) else mem['embedding']
            if mem.get('metadata'):
                mem['metadata'] = json.loads(mem['metadata']) if isinstance(mem['metadata'], str) else mem['metadata']
        return memories
    
    # ==========================================
    # APPLICATIONS METHODS
    # ==========================================
    
    def get_applications(self, user_id: int):
        """Get job applications for a user"""
        query = "SELECT * FROM applications WHERE user_id = %s ORDER BY created_at DESC"
        return self.execute_query(query, (user_id,)) or []
    
    def get_opportunities(self, limit: int = 20):
        """Get available opportunities"""
        query = "SELECT * FROM opportunities WHERE is_active = TRUE ORDER BY deadline ASC LIMIT %s"
        opportunities = self.execute_query(query, (limit,)) or []
        for opp in opportunities:
            if opp.get('requirements'):
                opp['requirements'] = json.loads(opp['requirements']) if isinstance(opp['requirements'], str) else opp['requirements']
        return opportunities
    
    # ==========================================
    # AGENT SESSIONS METHODS
    # ==========================================
    
    def create_agent_session(self, user_id: int, session_type: str, input_data: dict):
        """Create a new agent session"""
        query = """
            INSERT INTO agent_sessions (user_id, session_type, input_data, status)
            VALUES (%s, %s, %s, 'processing')
        """
        return self.execute_query(query, (user_id, session_type, json.dumps(input_data)), fetch=False)
    
    def update_agent_session(self, session_id: int, output_data: dict, thoughts: str, status: str = 'completed'):
        """Update agent session with results"""
        query = """
            UPDATE agent_sessions 
            SET output_data = %s, agent_thoughts = %s, status = %s, completed_at = NOW()
            WHERE id = %s
        """
        self.execute_query(query, (json.dumps(output_data), thoughts, status, session_id), fetch=False)
    
    def clear_plans(self, user_id: int, goal_id: int = None):
        """Clear existing plans for a user/goal"""
        if goal_id:
            query = "DELETE FROM plans WHERE user_id = %s AND goal_id = %s"
            self.execute_query(query, (user_id, goal_id), fetch=False)
        else:
            query = "DELETE FROM plans WHERE user_id = %s"
            self.execute_query(query, (user_id,), fetch=False)
    
    def search_memories(self, user_id: int, query_embedding: list, limit: int = 5):
        """Search memories by embedding similarity (simplified - uses recent memories)"""
        # For full vector search, you'd use a vector database
        # This is a simplified version that returns recent relevant memories
        query = """
            SELECT * FROM memory_vectors 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s
        """
        memories = self.execute_query(query, (user_id, limit)) or []
        for mem in memories:
            if mem.get('embedding'):
                mem['embedding'] = json.loads(mem['embedding']) if isinstance(mem['embedding'], str) else mem['embedding']
            if mem.get('metadata'):
                mem['metadata'] = json.loads(mem['metadata']) if isinstance(mem['metadata'], str) else mem['metadata']
        return memories
    
    def update_skill_priorities(self, user_id: int, skill_updates: list):
        """Update skill priorities based on feedback"""
        for update in skill_updates:
            query = """
                UPDATE skill_gaps 
                SET priority = %s 
                WHERE user_id = %s AND skill_name = %s
            """
            self.execute_query(query, (update['priority'], user_id, update['skill_name']), fetch=False)
    
    # ==========================================
    # CHAT MESSAGES METHODS
    # ==========================================
    
    def save_chat_message(self, user_id: int, role: str, content: str, context: dict = None):
        """Save a chat message to the database"""
        query = """
            INSERT INTO chat_messages (user_id, role, content, context)
            VALUES (%s, %s, %s, %s)
        """
        return self.execute_query(query, (
            user_id, role, content, 
            json.dumps(context) if context else None
        ), fetch=False)
    
    def get_chat_history(self, user_id: int, limit: int = 50):
        """Get chat history for a user"""
        query = """
            SELECT role, content, created_at 
            FROM chat_messages 
            WHERE user_id = %s 
            ORDER BY created_at ASC 
            LIMIT %s
        """
        messages = self.execute_query(query, (user_id, limit)) or []
        return [{'role': m['role'], 'content': m['content']} for m in messages]
    
    def clear_chat_history(self, user_id: int):
        """Clear all chat messages for a user"""
        query = "DELETE FROM chat_messages WHERE user_id = %s"
        return self.execute_query(query, (user_id,), fetch=False)
    
    # ==========================================
    # CAREER EVENTS METHODS
    # ==========================================
    
    def save_career_event(self, user_id: int, event_type: str, event_data: dict, description: str = None):
        """Save a career event"""
        query = """
            INSERT INTO career_events (user_id, event_type, event_data, description)
            VALUES (%s, %s, %s, %s)
        """
        return self.execute_query(query, (
            user_id, event_type, 
            json.dumps(event_data) if isinstance(event_data, dict) else event_data,
            description
        ), fetch=False)
    
    def get_career_events(self, user_id: int, event_type: str = None, limit: int = 20):
        """Get career events for a user"""
        if event_type:
            query = """
                SELECT * FROM career_events 
                WHERE user_id = %s AND event_type = %s 
                ORDER BY created_at DESC LIMIT %s
            """
            params = (user_id, event_type, limit)
        else:
            query = """
                SELECT * FROM career_events 
                WHERE user_id = %s 
                ORDER BY created_at DESC LIMIT %s
            """
            params = (user_id, limit)
        
        events = self.execute_query(query, params) or []
        for event in events:
            if event.get('event_data'):
                event['event_data'] = json.loads(event['event_data']) if isinstance(event['event_data'], str) else event['event_data']
        return events
    
    # ==========================================
    # LEARNING PROGRESS METHODS
    # ==========================================
    
    def save_learning_progress(self, user_id: int, plan_id: int = None, skill_name: str = None, 
                               progress_percentage: int = 0, hours_spent: float = 0, notes: str = None):
        """Save learning progress"""
        query = """
            INSERT INTO learning_progress (user_id, plan_id, skill_name, progress_percentage, hours_spent, notes, week_number)
            VALUES (%s, %s, %s, %s, %s, %s, WEEK(NOW()))
        """
        return self.execute_query(query, (
            user_id, plan_id, skill_name, progress_percentage, hours_spent, notes
        ), fetch=False)
    
    def get_learning_progress(self, user_id: int, limit: int = 20):
        """Get learning progress for a user"""
        query = """
            SELECT * FROM learning_progress 
            WHERE user_id = %s 
            ORDER BY created_at DESC LIMIT %s
        """
        return self.execute_query(query, (user_id, limit)) or []
    
    # ==========================================
    # CAREER READINESS METHODS
    # ==========================================
    
    def save_career_readiness(self, user_id: int, score: int, breakdown: dict):
        """Save career readiness score"""
        query = """
            INSERT INTO career_readiness (user_id, score, breakdown_json, 
                skills_score, education_score, goals_score, progress_score, applications_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.execute_query(query, (
            user_id, score, json.dumps(breakdown),
            breakdown.get('skills', 0),
            breakdown.get('education', 0),
            breakdown.get('goals', 0),
            breakdown.get('progress', 0),
            breakdown.get('applications', 0)
        ), fetch=False)
    
    def get_career_readiness_history(self, user_id: int, limit: int = 10):
        """Get career readiness history for a user"""
        query = """
            SELECT score, breakdown_json, created_at 
            FROM career_readiness 
            WHERE user_id = %s 
            ORDER BY created_at DESC LIMIT %s
        """
        history = self.execute_query(query, (user_id, limit)) or []
        for entry in history:
            if entry.get('breakdown_json'):
                entry['breakdown'] = json.loads(entry['breakdown_json']) if isinstance(entry['breakdown_json'], str) else entry['breakdown_json']
        return history
    
    # ==========================================
    # USER MEMORY METHODS
    # ==========================================
    
    def save_user_memory(self, user_id: int, memory_key: str, memory_value: str, memory_type: str = 'context'):
        """Save or update user memory"""
        query = """
            INSERT INTO user_memory (user_id, memory_key, memory_value, memory_type)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE memory_value = VALUES(memory_value), memory_type = VALUES(memory_type)
        """
        return self.execute_query(query, (user_id, memory_key, memory_value, memory_type), fetch=False)
    
    def get_user_memory(self, user_id: int, memory_key: str = None):
        """Get user memory"""
        if memory_key:
            query = "SELECT * FROM user_memory WHERE user_id = %s AND memory_key = %s"
            result = self.execute_query(query, (user_id, memory_key))
            return result[0] if result else None
        else:
            query = "SELECT * FROM user_memory WHERE user_id = %s ORDER BY updated_at DESC"
            return self.execute_query(query, (user_id,)) or []
    
    # ==========================================
    # RESUME METHODS
    # ==========================================
    
    def create_resume(
        self,
        user_id: int,
        role_type: str,
        resume_data: dict,
        file_path: str = None,
        target_company: str = None,
        based_on_jd: str = None,
        match_score: int = 0,
        emphasis_areas: list = None
    ):
        """Create a new versioned resume"""
        # Get next version number
        version_query = "SELECT COALESCE(MAX(version), 0) + 1 as next_version FROM resumes WHERE user_id = %s"
        version_result = self.execute_query(version_query, (user_id,))
        version = version_result[0]['next_version'] if version_result else 1
        
        # Deactivate old resumes for same role
        deactivate_query = "UPDATE resumes SET is_active = FALSE WHERE user_id = %s AND role_type = %s"
        self.execute_query(deactivate_query, (user_id, role_type), fetch=False)
        
        query = """
            INSERT INTO resumes (
                user_id, version, role_type, target_company, resume_data,
                file_path, pdf_generated, based_on_jd, match_score, emphasis_areas
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        resume_id = self.execute_query(
            query,
            (
                user_id, version, role_type, target_company,
                json.dumps(resume_data) if isinstance(resume_data, dict) else resume_data,
                file_path, bool(file_path), based_on_jd, match_score,
                json.dumps(emphasis_areas) if emphasis_areas else None
            ),
            fetch=False
        )
        return resume_id
    
    def get_user_resumes(self, user_id: int, active_only: bool = False):
        """Get all resumes for a user"""
        if active_only:
            query = "SELECT * FROM resumes WHERE user_id = %s AND is_active = TRUE ORDER BY created_at DESC"
        else:
            query = "SELECT * FROM resumes WHERE user_id = %s ORDER BY version DESC"
        
        result = self.execute_query(query, (user_id,)) or []
        
        # Parse JSON fields
        for resume in result:
            if resume.get('resume_data'):
                resume['resume_data'] = json.loads(resume['resume_data']) if isinstance(resume['resume_data'], str) else resume['resume_data']
            if resume.get('emphasis_areas'):
                resume['emphasis_areas'] = json.loads(resume['emphasis_areas']) if isinstance(resume['emphasis_areas'], str) else resume['emphasis_areas']
        
        return result
    
    def get_resume(self, resume_id: int):
        """Get a specific resume by ID"""
        query = "SELECT * FROM resumes WHERE id = %s"
        result = self.execute_query(query, (resume_id,))
        
        if result:
            resume = result[0]
            if resume.get('resume_data'):
                resume['resume_data'] = json.loads(resume['resume_data']) if isinstance(resume['resume_data'], str) else resume['resume_data']
            if resume.get('emphasis_areas'):
                resume['emphasis_areas'] = json.loads(resume['emphasis_areas']) if isinstance(resume['emphasis_areas'], str) else resume['emphasis_areas']
            return resume
        return None
    
    def get_latest_resume(self, user_id: int, role_type: str = None):
        """Get the latest resume for a user (optionally filtered by role)"""
        if role_type:
            query = "SELECT * FROM resumes WHERE user_id = %s AND role_type = %s ORDER BY version DESC LIMIT 1"
            params = (user_id, role_type)
        else:
            query = "SELECT * FROM resumes WHERE user_id = %s ORDER BY version DESC LIMIT 1"
            params = (user_id,)
        
        result = self.execute_query(query, params)
        
        if result:
            resume = result[0]
            if resume.get('resume_data'):
                resume['resume_data'] = json.loads(resume['resume_data']) if isinstance(resume['resume_data'], str) else resume['resume_data']
            if resume.get('emphasis_areas'):
                resume['emphasis_areas'] = json.loads(resume['emphasis_areas']) if isinstance(resume['emphasis_areas'], str) else resume['emphasis_areas']
            return resume
        return None
    
    def update_resume_pdf_path(self, resume_id: int, file_path: str):
        """Update resume PDF file path"""
        query = "UPDATE resumes SET file_path = %s, pdf_generated = TRUE WHERE id = %s"
        self.execute_query(query, (file_path, resume_id), fetch=False)
    
    def deactivate_resume(self, resume_id: int):
        """Deactivate a resume"""
        query = "UPDATE resumes SET is_active = FALSE WHERE id = %s"
        self.execute_query(query, (resume_id,), fetch=False)


# Global database instance
db = Database()
