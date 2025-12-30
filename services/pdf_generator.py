"""
PDF Resume Generator
Generates professional PDF resumes from structured JSON data using ReportLab
"""
import os
from typing import Dict, Any
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, grey
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY


class PDFResumeGenerator:
    """
    Generates professional PDF resumes with:
    1. ATS-friendly formatting
    2. Professional styling
    3. Section-based layout
    4. Customizable themes
    """
    
    def __init__(self, output_dir: str = "resumes"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Color scheme
        self.primary_color = HexColor('#2563eb')  # Blue
        self.secondary_color = HexColor('#64748b')  # Slate
        self.text_color = HexColor('#1e293b')  # Dark slate
        
        # Initialize styles
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        # Name/Header style
        self.styles.add(ParagraphStyle(
            name='ResumeHeader',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=self.primary_color,
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Contact info style
        self.styles.add(ParagraphStyle(
            name='ContactInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.secondary_color,
            alignment=TA_CENTER,
            spaceAfter=12
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=self.primary_color,
            spaceAfter=6,
            spaceBefore=12,
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=self.primary_color,
            borderPadding=4,
            borderRadius=2
        ))
        
        # Job title style
        self.styles.add(ParagraphStyle(
            name='JobTitle',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=self.text_color,
            fontName='Helvetica-Bold',
            spaceAfter=2
        ))
        
        # Company/Date style
        self.styles.add(ParagraphStyle(
            name='CompanyDate',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.secondary_color,
            fontName='Helvetica-Oblique',
            spaceAfter=4
        ))
        
        # Achievement/Bullet style
        self.styles.add(ParagraphStyle(
            name='Achievement',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.text_color,
            leftIndent=20,
            spaceAfter=3,
            bulletIndent=10
        ))
        
        # Summary style
        self.styles.add(ParagraphStyle(
            name='Summary',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.text_color,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        ))
    
    def generate_pdf(
        self,
        resume_data: Dict[str, Any],
        filename: str,
        user_id: int,
        version: int
    ) -> str:
        """
        Generate PDF from structured resume data
        
        Args:
            resume_data: Structured resume JSON
            filename: Output filename
            user_id: User ID for directory structure
            version: Resume version number
        
        Returns:
            Full file path of generated PDF
        """
        # Create user-specific directory
        user_dir = os.path.join(self.output_dir, f"user_{user_id}")
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        
        filepath = os.path.join(user_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Build content
        story = []
        
        # Header Section
        story.extend(self._build_header(resume_data.get('contact', {})))
        
        # Professional Summary
        if resume_data.get('summary'):
            story.extend(self._build_summary(resume_data['summary']))
        
        # Skills Section
        if resume_data.get('skills'):
            story.extend(self._build_skills(resume_data['skills']))
        
        # Experience Section
        if resume_data.get('experience'):
            story.extend(self._build_experience(resume_data['experience']))
        
        # Education Section
        if resume_data.get('education'):
            story.extend(self._build_education(resume_data['education']))
        
        # Projects Section
        if resume_data.get('projects'):
            story.extend(self._build_projects(resume_data['projects']))
        
        # Certifications
        if resume_data.get('certifications'):
            story.extend(self._build_certifications(resume_data['certifications']))
        
        # Build PDF
        doc.build(story)
        
        return filepath
    
    def _build_header(self, contact: Dict) -> list:
        """Build header with contact information"""
        elements = []
        
        # Name
        name = contact.get('name', 'Unknown')
        elements.append(Paragraph(name, self.styles['ResumeHeader']))
        
        # Contact details
        contact_parts = []
        if contact.get('email'):
            contact_parts.append(contact['email'])
        if contact.get('phone'):
            contact_parts.append(contact['phone'])
        if contact.get('location'):
            contact_parts.append(contact['location'])
        
        contact_line = ' | '.join(contact_parts)
        elements.append(Paragraph(contact_line, self.styles['ContactInfo']))
        
        # Links
        links = []
        if contact.get('linkedin'):
            links.append(f"LinkedIn: {contact['linkedin']}")
        if contact.get('github'):
            links.append(f"GitHub: {contact['github']}")
        if contact.get('portfolio'):
            links.append(f"Portfolio: {contact['portfolio']}")
        
        if links:
            links_line = ' | '.join(links)
            elements.append(Paragraph(links_line, self.styles['ContactInfo']))
        
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_summary(self, summary: str) -> list:
        """Build professional summary section"""
        elements = []
        elements.append(Paragraph("PROFESSIONAL SUMMARY", self.styles['SectionHeader']))
        elements.append(Paragraph(summary, self.styles['Summary']))
        elements.append(Spacer(1, 0.1*inch))
        return elements
    
    def _build_skills(self, skills: Dict) -> list:
        """Build skills section"""
        elements = []
        elements.append(Paragraph("SKILLS", self.styles['SectionHeader']))
        
        for category, skill_list in skills.items():
            if skill_list:
                category_name = category.replace('_', ' ').title()
                skill_text = f"<b>{category_name}:</b> {', '.join(skill_list)}"
                elements.append(Paragraph(skill_text, self.styles['Normal']))
                elements.append(Spacer(1, 0.05*inch))
        
        elements.append(Spacer(1, 0.1*inch))
        return elements
    
    def _build_experience(self, experiences: list) -> list:
        """Build work experience section"""
        elements = []
        elements.append(Paragraph("PROFESSIONAL EXPERIENCE", self.styles['SectionHeader']))
        
        for exp in experiences:
            # Job title
            title = exp.get('title', 'Position')
            elements.append(Paragraph(title, self.styles['JobTitle']))
            
            # Company and duration
            company = exp.get('company', 'Company')
            duration = exp.get('duration', '')
            company_line = f"{company} | {duration}" if duration else company
            elements.append(Paragraph(company_line, self.styles['CompanyDate']))
            
            # Achievements
            achievements = exp.get('achievements', [])
            for achievement in achievements:
                bullet = f"• {achievement}"
                elements.append(Paragraph(bullet, self.styles['Achievement']))
            
            elements.append(Spacer(1, 0.15*inch))
        
        return elements
    
    def _build_education(self, education: list) -> list:
        """Build education section"""
        elements = []
        elements.append(Paragraph("EDUCATION", self.styles['SectionHeader']))
        
        for edu in education:
            degree = edu.get('degree', 'Degree')
            institution = edu.get('institution', 'Institution')
            year = edu.get('year', '')
            
            edu_title = f"{degree} | {institution}"
            if year:
                edu_title += f" | {year}"
            
            elements.append(Paragraph(edu_title, self.styles['JobTitle']))
            
            if edu.get('details'):
                elements.append(Paragraph(edu['details'], self.styles['Normal']))
            
            elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _build_projects(self, projects: list) -> list:
        """Build projects section"""
        elements = []
        elements.append(Paragraph("PROJECTS", self.styles['SectionHeader']))
        
        for project in projects:
            name = project.get('name', 'Project')
            elements.append(Paragraph(name, self.styles['JobTitle']))
            
            if project.get('description'):
                elements.append(Paragraph(project['description'], self.styles['Normal']))
            
            if project.get('technologies'):
                tech_text = f"<i>Technologies: {', '.join(project['technologies'])}</i>"
                elements.append(Paragraph(tech_text, self.styles['Normal']))
            
            if project.get('highlights'):
                for highlight in project['highlights']:
                    bullet = f"• {highlight}"
                    elements.append(Paragraph(bullet, self.styles['Achievement']))
            
            elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _build_certifications(self, certifications: list) -> list:
        """Build certifications section"""
        elements = []
        elements.append(Paragraph("CERTIFICATIONS", self.styles['SectionHeader']))
        
        cert_text = '<br/>'.join([f"• {cert}" for cert in certifications])
        elements.append(Paragraph(cert_text, self.styles['Normal']))
        
        return elements


# Singleton instance
pdf_generator = PDFResumeGenerator()
