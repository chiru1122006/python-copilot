"""
Agent Modules Package
"""
from .reasoning_agent import reasoning_agent, ReasoningAgent
from .skill_gap_agent import skill_gap_agent, SkillGapAgent
from .planner_agent import planner_agent, PlannerAgent
from .feedback_agent import feedback_agent, FeedbackAgent
from .resume_agent import resume_agent, ResumeAgent
from .projects_agent import projects_agent, ProjectsAgent

# Lazy load embedding agent due to heavy dependencies
embedding_generator = None
EmbeddingGenerator = None

def get_embedding_generator():
    """Lazy load embedding generator on first use"""
    global embedding_generator, EmbeddingGenerator
    if embedding_generator is None:
        from .embedding_agent import embedding_generator as _eg, EmbeddingGenerator as _EG
        embedding_generator = _eg
        EmbeddingGenerator = _EG
    return embedding_generator

__all__ = [
    'reasoning_agent', 'ReasoningAgent',
    'skill_gap_agent', 'SkillGapAgent',
    'planner_agent', 'PlannerAgent',
    'feedback_agent', 'FeedbackAgent',
    'get_embedding_generator',
    'resume_agent', 'ResumeAgent',
    'projects_agent', 'ProjectsAgent'
]
