"""
HTML to PDF Resume Generator
Uses xhtml2pdf for pure Python HTML to PDF conversion
Generates professional two-column resumes matching the design specification
Uses the custom template from resume-format.html
"""
import os
from typing import Dict, Any
from datetime import datetime
from io import BytesIO
from jinja2 import Environment, BaseLoader
from xhtml2pdf import pisa


class HTMLPDFGenerator:
    """
    Generates professional PDF resumes using HTML templates and xhtml2pdf
    Layout: Dark sidebar left (1/3) + White content right (2/3)
    Matches resume-format.html design exactly
    """
    
    # HTML Template matching resume-format.html design exactly
    RESUME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ header.name }} - {{ header.title }}</title>
    <style>
        @page {
            size: A4;
            margin: 0;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: Helvetica, Arial, sans-serif;
            font-size: 10pt;
            line-height: 1.4;
            color: #1f2937;
            background: white;
        }
        
        /* Main Layout - Two Columns */
        .page {
            width: 100%;
            min-height: 1100px;
        }
        
        .columns {
            width: 100%;
        }
        
        /* Left Sidebar (33%) - Dark Theme */
        .sidebar {
            width: 33%;
            background-color: #0f172a;
            color: white;
            padding: 30px 20px;
            vertical-align: top;
        }
        
        /* Right Main Content (67%) - White Theme */
        .main-content {
            width: 67%;
            padding: 30px 35px;
            background: white;
            vertical-align: top;
        }
        
        /* Profile Initials Circle */
        .profile-circle {
            width: 100px;
            height: 100px;
            background-color: #334155;
            border-radius: 50%;
            margin: 0 auto 25px auto;
            text-align: center;
            line-height: 100px;
        }
        
        .profile-initials {
            font-size: 28pt;
            font-weight: bold;
            color: #94a3b8;
        }
        
        /* Sidebar Section Headers */
        .sidebar-section-title {
            font-size: 11pt;
            font-weight: bold;
            color: white;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 12px;
            padding-bottom: 6px;
            border-bottom: 1px solid #334155;
        }
        
        .sidebar-section {
            margin-bottom: 25px;
        }
        
        /* Contact Info */
        .contact-item {
            margin-bottom: 10px;
            font-size: 9pt;
            color: #cbd5e1;
        }
        
        .contact-icon {
            color: #60a5fa;
            display: inline-block;
            width: 18px;
            margin-right: 8px;
        }
        
        /* Education in Sidebar */
        .education-item {
            margin-bottom: 12px;
        }
        
        .education-degree {
            font-size: 10pt;
            font-weight: bold;
            color: white;
        }
        
        .education-institution {
            font-size: 9pt;
            color: #94a3b8;
        }
        
        .education-year {
            font-size: 8pt;
            color: #64748b;
            font-style: italic;
        }
        
        /* Skills Tags */
        .skills-container {
            display: block;
        }
        
        .skill-tag {
            display: inline-block;
            background-color: #1e293b;
            color: #e2e8f0;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 8pt;
            margin: 0 4px 6px 0;
        }
        
        /* Certifications */
        .cert-item {
            font-size: 9pt;
            color: #cbd5e1;
            margin-bottom: 8px;
        }
        
        /* Main Content - Header */
        .main-header {
            margin-bottom: 25px;
        }
        
        .main-header h1 {
            font-size: 26pt;
            font-weight: bold;
            color: #111827;
            margin-bottom: 5px;
        }
        
        .main-header h2 {
            font-size: 13pt;
            font-weight: 500;
            color: #2563eb;
        }
        
        /* Main Section Headers */
        .main-section-title {
            font-size: 11pt;
            font-weight: bold;
            color: #9ca3af;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 12px;
        }
        
        .main-section {
            margin-bottom: 25px;
        }
        
        /* Professional Summary */
        .summary-text {
            font-size: 10pt;
            color: #4b5563;
            line-height: 1.6;
        }
        
        /* Experience Timeline */
        .experience-item {
            margin-bottom: 20px;
            padding-left: 15px;
            border-left: 2px solid #dbeafe;
            position: relative;
        }
        
        .experience-dot {
            position: absolute;
            left: -6px;
            top: 0;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: #3b82f6;
        }
        
        .experience-dot-gray {
            background-color: #9ca3af;
        }
        
        .experience-header {
            margin-bottom: 6px;
        }
        
        .experience-role {
            font-size: 12pt;
            font-weight: bold;
            color: #1f2937;
        }
        
        .experience-duration {
            font-size: 9pt;
            font-weight: 600;
            color: #2563eb;
            background-color: #eff6ff;
            padding: 2px 8px;
            border-radius: 3px;
            display: inline-block;
        }
        
        .experience-duration-simple {
            font-size: 9pt;
            color: #6b7280;
        }
        
        .experience-company {
            font-size: 9pt;
            color: #6b7280;
            font-weight: 500;
            margin-bottom: 8px;
        }
        
        .experience-points {
            margin-left: 15px;
            font-size: 9pt;
            color: #4b5563;
        }
        
        .experience-points li {
            margin-bottom: 5px;
            line-height: 1.5;
        }
        
        /* Projects Section */
        .project-item {
            margin-bottom: 15px;
        }
        
        .project-title {
            font-size: 10pt;
            font-weight: bold;
            color: #1f2937;
            margin-bottom: 3px;
        }
        
        .project-tech {
            font-size: 8pt;
            color: #2563eb;
            font-style: italic;
            margin-bottom: 5px;
        }
        
        .project-points {
            margin-left: 15px;
            font-size: 9pt;
            color: #4b5563;
        }
        
        .project-points li {
            margin-bottom: 4px;
            line-height: 1.4;
        }
        
        /* Strong text highlighting */
        strong {
            color: #1f2937;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="page">
        <table class="columns" cellpadding="0" cellspacing="0">
            <tr>
                <!-- Left Sidebar -->
                <td class="sidebar">
                    <!-- Profile Initials -->
                    <div class="profile-circle">
                        <span class="profile-initials">{{ header.name[:2] | upper }}</span>
                    </div>
                    
                    <!-- Contact -->
                    <div class="sidebar-section">
                        <div class="sidebar-section-title">Contact</div>
                        {% if contact.email %}
                        <div class="contact-item">
                            <span class="contact-icon">✉</span>{{ contact.email }}
                        </div>
                        {% endif %}
                        {% if contact.phone %}
                        <div class="contact-item">
                            <span class="contact-icon">☎</span>{{ contact.phone }}
                        </div>
                        {% endif %}
                        {% if contact.address %}
                        <div class="contact-item">
                            <span class="contact-icon">◉</span>{{ contact.address }}
                        </div>
                        {% endif %}
                        {% if contact.linkedin %}
                        <div class="contact-item">
                            <span class="contact-icon">in</span>{{ contact.linkedin }}
                        </div>
                        {% endif %}
                        {% if contact.website %}
                        <div class="contact-item">
                            <span class="contact-icon">⌂</span>{{ contact.website }}
                        </div>
                        {% endif %}
                    </div>
                    
                    <!-- Education -->
                    {% if education %}
                    <div class="sidebar-section">
                        <div class="sidebar-section-title">Education</div>
                        {% for edu in education %}
                        <div class="education-item">
                            <div class="education-degree">{{ edu.degree }}</div>
                            <div class="education-institution">{{ edu.institution }}</div>
                            <div class="education-year">{{ edu.year }}</div>
                        </div>
                        {% endfor %}
                    </div>
                    {% endif %}
                    
                    <!-- Core Skills -->
                    {% if skills %}
                    <div class="sidebar-section">
                        <div class="sidebar-section-title">Core Skills</div>
                        <div class="skills-container">
                            {% for skill in skills %}
                            <span class="skill-tag">{{ skill.name }}</span>
                            {% endfor %}
                        </div>
                    </div>
                    {% endif %}
                    
                    <!-- Certifications -->
                    {% if certifications %}
                    <div class="sidebar-section">
                        <div class="sidebar-section-title">Certifications</div>
                        {% for cert in certifications %}
                        <div class="cert-item">• {{ cert }}</div>
                        {% endfor %}
                    </div>
                    {% endif %}
                </td>
                
                <!-- Right Main Content -->
                <td class="main-content">
                    <!-- Header -->
                    <div class="main-header">
                        <h1>{{ header.name }}</h1>
                        <h2>{{ header.title }}</h2>
                    </div>
                    
                    <!-- Professional Profile / Summary -->
                    {% if summary %}
                    <div class="main-section">
                        <div class="main-section-title">Professional Profile</div>
                        <p class="summary-text">{{ summary }}</p>
                    </div>
                    {% endif %}
                    
                    <!-- Work Experience -->
                    {% if experience %}
                    <div class="main-section">
                        <div class="main-section-title">Work Experience</div>
                        {% for exp in experience %}
                        <div class="experience-item">
                            <div class="experience-dot {% if not loop.first %}experience-dot-gray{% endif %}"></div>
                            <div class="experience-header">
                                <span class="experience-role">{{ exp.role }}</span>
                                {% if loop.first %}
                                <span class="experience-duration">{{ exp.duration }}</span>
                                {% else %}
                                <span class="experience-duration-simple">{{ exp.duration }}</span>
                                {% endif %}
                            </div>
                            <div class="experience-company">{{ exp.company }}{% if exp.location %} • {{ exp.location }}{% endif %}</div>
                            {% if exp.points %}
                            <ul class="experience-points">
                                {% for point in exp.points %}
                                <li>{{ point }}</li>
                                {% endfor %}
                            </ul>
                            {% endif %}
                        </div>
                        {% endfor %}
                    </div>
                    {% endif %}
                    
                    <!-- Projects -->
                    {% if projects %}
                    <div class="main-section">
                        <div class="main-section-title">Projects</div>
                        {% for project in projects %}
                        <div class="project-item">
                            <div class="project-title">{{ project.title }}</div>
                            {% if project.tech_stack %}
                            <div class="project-tech">{{ project.tech_stack | join(', ') }}</div>
                            {% endif %}
                            {% if project.points %}
                            <ul class="project-points">
                                {% for point in project.points %}
                                <li>{{ point }}</li>
                                {% endfor %}
                            </ul>
                            {% endif %}
                        </div>
                        {% endfor %}
                    </div>
                    {% endif %}
                </td>
            </tr>
        </table>
    </div>
</body>
</html>
"""
    
    def __init__(self, output_dir: str = None):
        # Use absolute path to the resumes folder in the project root
        if output_dir is None:
            # Get the absolute path to the ai-main directory
            # This file is in: ai-main/python-agents/services/html_pdf_generator.py
            # We need to go up 3 levels to get to ai-main, then down to resumes
            current_file = os.path.abspath(__file__)
            services_dir = os.path.dirname(current_file)  # python-agents/services
            python_agents_dir = os.path.dirname(services_dir)  # python-agents
            ai_main_dir = os.path.dirname(python_agents_dir)  # ai-main
            output_dir = os.path.join(ai_main_dir, "resumes")
        
        self.output_dir = output_dir
        print(f"[HTMLPDFGenerator] Output directory set to: {self.output_dir}")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"[HTMLPDFGenerator] Created output directory: {self.output_dir}")
        
        # Initialize Jinja2 environment
        self.jinja_env = Environment(loader=BaseLoader())
        self.template = self.jinja_env.from_string(self.RESUME_TEMPLATE)
    
    def generate_pdf(
        self,
        resume_data: Dict[str, Any],
        filename: str = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """
        Generate PDF from structured resume JSON using xhtml2pdf
        
        Args:
            resume_data: Structured resume JSON following the strict schema
            filename: Optional custom filename
            user_id: Optional user ID for file naming
        
        Returns:
            Dictionary with file path and status
        """
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name_slug = resume_data.get('header', {}).get('name', 'resume').lower()
                name_slug = ''.join(c if c.isalnum() else '_' for c in name_slug)
                filename = f"{name_slug}_{timestamp}.pdf"
            
            # Ensure .pdf extension
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            filepath = os.path.join(self.output_dir, filename)
            print(f"[HTMLPDFGenerator] Generating PDF at: {filepath}")
            
            # Render HTML from template
            html_content = self.template.render(**resume_data)
            
            # Convert HTML to PDF using xhtml2pdf
            with open(filepath, "wb") as pdf_file:
                pisa_status = pisa.CreatePDF(
                    html_content,
                    dest=pdf_file,
                    encoding='utf-8'
                )
            
            if pisa_status.err:
                return {
                    "status": "error",
                    "message": f"PDF generation had errors: {pisa_status.err}",
                    "file_path": None
                }
            
            return {
                "status": "success",
                "file_path": filepath,
                "filename": filename,
                "message": "Resume PDF generated successfully"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate PDF: {str(e)}",
                "file_path": None
            }
    
    def generate_pdf_bytes(self, resume_data: Dict[str, Any]) -> bytes:
        """
        Generate PDF and return as bytes (for streaming download)
        
        Args:
            resume_data: Structured resume JSON
        
        Returns:
            PDF file as bytes
        """
        html_content = self.template.render(**resume_data)
        pdf_buffer = BytesIO()
        
        pisa.CreatePDF(html_content, dest=pdf_buffer, encoding='utf-8')
        
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    
    def validate_resume_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate resume data against the strict schema
        
        Args:
            data: Resume data to validate
        
        Returns:
            Validation result with any missing fields
        """
        required_structure = {
            "header": {"name": str, "title": str},
            "contact": {"phone": str, "email": str, "address": str, "website": str, "linkedin": str},
            "summary": str,
            "skills": list,
            "experience": list,
            "education": list
        }
        
        missing_fields = []
        
        # Check top-level fields
        for field, field_type in required_structure.items():
            if field not in data:
                missing_fields.append(field)
        
        return {
            "valid": len(missing_fields) == 0,
            "missing_fields": missing_fields,
            "message": "Valid resume data" if len(missing_fields) == 0 else f"Missing fields: {missing_fields}"
        }
    
    def generate_html_preview(self, resume_data: Dict[str, Any]) -> str:
        """
        Generate HTML preview of the resume
        
        Args:
            resume_data: Structured resume JSON
        
        Returns:
            HTML string for preview
        """
        return self.template.render(**resume_data)


# Create singleton instance
html_pdf_generator = HTMLPDFGenerator()
