#!/usr/bin/env python3
"""
Prompt Collection v2.0 Mass Enhancement Script
Upgrades all prompts to Schema v2.0 with complete metadata
"""

import json
import os
from pathlib import Path
from datetime import datetime

# Enhanced metadata for all 114 prompts - keyed by filename
PROMPT_ENHANCEMENTS = {
    # AI Assistant Category
    "general-purpose-assistant.json": {
        "difficulty_level": "beginner",
        "time_estimate": "quick",
        "output_format": "text",
        "expected_outcomes": [
            "Clear, factual answer with supporting evidence",
            "Acknowledgment of limitations or uncertainties",
            "Relevant follow-up questions or deeper resources"
        ],
        "prerequisites": ["Basic knowledge in topic area"],
        "use_case_examples": [
            "Explaining technical concepts to non-technical audience",
            "Getting balanced perspective on controversial topics",
            "Finding resources for further learning"
        ],
        "success_criteria": [
            "Answer directly addresses the question",
            "Evidence provided for key claims",
            "Limitations acknowledged when uncertain"
        ],
        "tone": "neutral",
        "best_for": "Anyone seeking accurate, balanced information",
        "avoid_if": "You need highly specialized expertise or niche knowledge"
    },
    "academic-research-assistant.json": {
        "difficulty_level": "intermediate",
        "time_estimate": "thorough",
        "output_format": "markdown",
        "expected_outcomes": [
            "List of peer-reviewed sources with annotations",
            "Synthesis of findings across 3+ sources",
            "Proper academic citations (APA/MLA/Chicago format)",
            "Gaps identified for future research"
        ],
        "prerequisites": ["Familiarity with academic databases", "Topic area knowledge"],
        "use_case_examples": [
            "Literature review for thesis or dissertation",
            "Background research for academic paper",
            "Identifying research trends in field"
        ],
        "success_criteria": [
            "All sources are peer-reviewed and credible",
            "Synthesis connects findings across sources",
            "Citations formatted consistently"
        ],
        "tone": "formal",
        "best_for": "Researchers, students, academics conducting literature reviews",
        "avoid_if": "You need real-time news or non-academic sources"
    },
    "market-research-specialist.json": {
        "difficulty_level": "intermediate",
        "time_estimate": "thorough",
        "output_format": "json",
        "expected_outcomes": [
            "Target market segments identified and characterized",
            "Competitor analysis with positioning and pricing",
            "Market size and growth rate estimates",
            "Customer needs and pain points identified",
            "Strategic opportunities and market threats"
        ],
        "prerequisites": ["Understanding of business fundamentals", "Access to industry data"],
        "use_case_examples": [
            "Going-to-market strategy for startup",
            "Expansion into new geographic market",
            "Product positioning and differentiation analysis"
        ],
        "success_criteria": [
            "Quantitative market size with sources",
            "Competitive differentiation clearly articulated",
            "Opportunities ranked by viability"
        ],
        "tone": "technical",
        "best_for": "Product managers, entrepreneurs, business strategists",
        "avoid_if": "You need tactical execution details vs strategic insights"
    },
    "competitive-research-analyst.json": {
        "difficulty_level": "intermediate",
        "time_estimate": "thorough",
        "output_format": "markdown",
        "expected_outcomes": [
            "Detailed competitive matrix (3-5 key competitors)",
            "Feature parity analysis and differentiation gaps",
            "Pricing and positioning strategies",
            "Go-to-market and marketing approach",
            "Competitive vulnerabilities and opportunities"
        ],
        "prerequisites": ["Product knowledge", "Market understanding"],
        "use_case_examples": [
            "Competitive differentiation strategy",
            "Pricing optimization analysis",
            "Feature prioritization based on competitive gaps"
        ],
        "success_criteria": [
            "Competitors objectively compared",
            "Clear differentiation opportunities identified",
            "Analysis based on recent data"
        ],
        "tone": "technical",
        "best_for": "Product leads, strategists, executive teams",
        "avoid_if": "You only need high-level overview vs deep competitive analysis"
    },
    
    # Coding & Development
    "api-developer.json": {
        "difficulty_level": "intermediate",
        "time_estimate": "thorough",
        "output_format": "code",
        "expected_outcomes": [
            "OpenAPI/Swagger specification",
            "Example API endpoints with request/response",
            "Authentication and authorization implementation",
            "Error handling with status codes",
            "API documentation strings"
        ],
        "prerequisites": ["RESTful API knowledge", "HTTP protocol understanding"],
        "use_case_examples": [
            "Building RESTful microservice",
            "Designing webhook API for third-party integrations",
            "Creating GraphQL API layer"
        ],
        "success_criteria": [
            "API follows REST principles",
            "Proper HTTP methods and status codes",
            "Security best practices implemented"
        ],
        "constraints": {"max_scope": "API design and specification; not production scaling"},
        "tone": "technical",
        "best_for": "Backend engineers, API architects",
        "avoid_if": "You need client SDK generation or API testing tools"
    },
    "python-code-generator.json": {
        "difficulty_level": "intermediate",
        "time_estimate": "moderate",
        "output_format": "code",
        "expected_outcomes": [
            "Production-ready Python code",
            "PEP 8 compliant formatting",
            "Comprehensive docstrings with type hints",
            "Error handling with try-except blocks",
            "Code examples demonstrating usage"
        ],
        "prerequisites": ["Python 3.8+ knowledge", "Familiarity with topic domain"],
        "use_case_examples": [
            "Data processing pipeline development",
            "Machine learning model implementation",
            "Web service utility functions"
        ],
        "success_criteria": [
            "Code passes linting (Black, Flake8)",
            "Type hints present and correct",
            "Error cases explicitly handled"
        ],
        "constraints": {
            "language_support": ["Python 3.8+"],
            "max_scope": "Up to 500 lines of code per prompt"
        },
        "tone": "technical",
        "best_for": "Python developers of all levels",
        "avoid_if": "You need system-level code or multi-file project structure"
    },
    "react-component-generator.json": {
        "difficulty_level": "intermediate",
        "time_estimate": "moderate",
        "output_format": "code",
        "expected_outcomes": [
            "Functional React component with hooks",
            "Proper TypeScript types",
            "Props validation and documentation",
            "Accessibility (a11y) compliance",
            "Example usage demonstration"
        ],
        "prerequisites": ["React (16.8+) and Hooks knowledge", "JavaScript/TypeScript"],
        "use_case_examples": [
            "Reusable UI component for design system",
            "Dashboard widget with state management",
            "Form input component with validation"
        ],
        "success_criteria": [
            "Component is fully typed",
            "Passes accessibility audit",
            "Example shows typical usage patterns"
        ],
        "constraints": {"max_scope": "Single component; not full page architecture"},
        "tone": "technical",
        "best_for": "Frontend developers using React",
        "avoid_if": "You need styling implementation or state management setup"
    },
    "security-code-reviewer.json": {
        "difficulty_level": "expert",
        "time_estimate": "thorough",
        "output_format": "markdown",
        "expected_outcomes": [
            "List of vulnerabilities with OWASP mappings",
            "Severity levels (critical/high/medium/low)",
            "Secure code examples for remediation",
            "Reference to security principles violated",
            "Testing recommendations for verification"
        ],
        "prerequisites": ["OWASP Top 10 knowledge", "Secure coding practices"],
        "use_case_examples": [
            "Pre-production security audit",
            "Third-party code review",
            "Training junior developers on security"
        ],
        "success_criteria": [
            "All major vulnerability classes detected",
            "Remediation code is secure",
            "False positives minimized"
        ],
        "constraints": {
            "max_scope": "3-5 files per session",
            "language_support": ["Python", "JavaScript", "Java", "C#", "Go"]
        },
        "tone": "technical",
        "best_for": "Security engineers, code reviewers, team leads",
        "avoid_if": "You need penetration testing or deployed application security"
    },
    "java-backend-developer.json": {
        "difficulty_level": "expert",
        "time_estimate": "thorough",
        "output_format": "code",
        "expected_outcomes": [
            "Spring Boot application structure",
            "REST API with proper annotations",
            "Database schema and repository layer",
            "Error handling and logging",
            "Security configuration (JWT, OAuth2)"
        ],
        "prerequisites": ["Java 11+, Spring Framework", "Microservices architecture"],
        "use_case_examples": [
            "Building microservice API",
            "Enterprise application backend",
            "Integration with existing Java systems"
        ],
        "success_criteria": [
            "Follows Spring Boot best practices",
            "API endpoints RESTful",
            "Secure authentication mechanism"
        ],
        "constraints": {"max_scope": "Single service, not distributed system"},
        "tone": "technical",
        "best_for": "Enterprise Java developers, backend architects",
        "avoid_if": "You need deployment infrastructure or system design"
    },
    "typescript-nodejs-developer.json": {
        "difficulty_level": "intermediate",
        "time_estimate": "moderate",
        "output_format": "code",
        "expected_outcomes": [
            "Express.js REST API with full types",
            "Async/await patterns correctly implemented",
            "Input validation and sanitization",
            "Error handling middleware",
            "Environment configuration"
        ],
        "prerequisites": ["TypeScript (3.8+), Node.js 14+", "Async JavaScript"],
        "use_case_examples": [
            "Full-stack Node API service",
            "Real-time WebSocket server",
            "Service-to-service integration"
        ],
        "success_criteria": [
            "Strict TypeScript compilation",
            "Proper async error handling",
            "Security validation applied"
        ],
        "constraints": {"max_scope": "Single service, <1000 LOC"},
        "tone": "technical",
        "best_for": "Full-stack JavaScript/TypeScript developers",
        "avoid_if": "You need performance optimization or clustering"
    },
    "ci-cd-pipeline-designer.json": {
        "difficulty_level": "expert",
        "time_estimate": "thorough",
        "output_format": "code",
        "expected_outcomes": [
            "Pipeline configuration (GitHub Actions/GitLab CI)",
            "Automated testing stages (unit, integration)",
            "Build optimization and caching",
            "Deployment strategy (blue-green/canary)",
            "Monitoring and rollback procedures"
        ],
        "prerequisites": ["Git workflows", "DevOps fundamentals", "Container basics"],
        "use_case_examples": [
            "Zero-downtime production deployment",
            "Multi-environment promotion workflow",
            "Containerized application delivery"
        ],
        "success_criteria": [
            "Pipeline reliable and repeatable",
            "All test stages automated",
            "Rollback capability validated"
        ],
        "constraints": {"max_scope": "CI/CD platform logic; not cloud provider setup"},
        "tone": "technical",
        "best_for": "DevOps engineers, senior developers, platform teams",
        "avoid_if": "You need infrastructure provisioning or Kubernetes orchestration"
    },
    
    # Writing & Content
    "blog-post-writer.json": {
        "difficulty_level": "beginner",
        "time_estimate": "moderate",
        "output_format": "markdown",
        "expected_outcomes": [
            "1000-1500 word blog post",
            "Compelling headline and intro",
            "3-5 main sections with subheadings",
            "Conclusion with call-to-action",
            "2-3 supporting graphics described"
        ],
        "prerequisites": ["Topic knowledge", "Understanding of target audience"],
        "use_case_examples": [
            "Weekly product feature announcement",
            "Thought leadership column",
            "How-to guide for audience"
        ],
        "success_criteria": [
            "Post engages reader within first 2 paragraphs",
            "Claims supported with evidence",
            "Call-to-action aligns with business goal"
        ],
        "tone": "friendly",
        "best_for": "Content marketers, product managers, thought leaders",
        "avoid_if": "You need SEO optimization or multi-channel promotion"
    },
    "content-editor.json": {
        "difficulty_level": "intermediate",
        "time_estimate": "moderate",
        "output_format": "markdown",
        "expected_outcomes": [
            "Grammar and spelling corrections applied",
            "Clarity improvements with explanations",
            "Consistency feedback (terminology, tone)",
            "Rewrite suggestions for ambiguous passages",
            "Readability metrics (Flesch-Kincaid score)"
        ],
        "prerequisites": ["Writing proficiency", "Domain familiarity"],
        "use_case_examples": [
            "Polishing blog post before publication",
            "Standardizing documentation",
            "Improving technical writing clarity"
        ],
        "success_criteria": [
            "No grammatical errors remain",
            "Tone consistent throughout",
            "Readability improved without losing content"
        ],
        "tone": "neutral",
        "best_for": "Writers, marketing teams, documentation owners",
        "avoid_if": "You need substantive content rewrite vs editing"
    },
    "fact-checker.json": {
        "difficulty_level": "intermediate",
        "time_estimate": "thorough",
        "output_format": "markdown",
        "expected_outcomes": [
            "Factual claims identified and flagged",
            "Source credibility assessed",
            "Claims cross-referenced with multiple sources",
            "Evidence rating (verified/unverified/disputed)",
            "Suggested corrections with citations"
        ],
        "prerequisites": ["Critical thinking", "Research skills"],
        "use_case_examples": [
            "Fact-checking article before publication",
            "Verifying claims in marketing copy",
            "Researching alternative perspectives"
        ],
        "success_criteria": [
            "All quantitative claims verified",
            "Sources are credible and recent",
            "Disputed claims clearly flagged"
        ],
        "tone": "neutral",
        "best_for": "Journalists, researchers, content quality teams",
        "avoid_if": "You need real-time fact-checking or breaking news"
    },

    # Copy all remaining 100+ prompts with similar structure...
    # (For brevity, showing the pattern - full version would have all 114)
}

def enhance_prompt(file_path, enhancements):
    """Load, enhance, and save a single prompt file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            prompt = json.load(f)
        
        filename = os.path.basename(file_path)
        if filename in enhancements:
            # Add v2.0 metadata
            prompt['schema_version'] = '2.0'
            prompt['difficulty_level'] = enhancements[filename].get('difficulty_level')
            prompt['time_estimate'] = enhancements[filename].get('time_estimate')
            prompt['output_format'] = enhancements[filename].get('output_format')
            prompt['expected_outcomes'] = enhancements[filename].get('expected_outcomes', [])
            prompt['prerequisites'] = enhancements[filename].get('prerequisites', [])
            prompt['use_case_examples'] = enhancements[filename].get('use_case_examples', [])
            prompt['success_criteria'] = enhancements[filename].get('success_criteria', [])
            prompt['tone'] = enhancements[filename].get('tone', 'neutral')
            prompt['best_for'] = enhancements[filename].get('best_for', '')
            prompt['avoid_if'] = enhancements[filename].get('avoid_if', '')
            prompt['constraints'] = enhancements[filename].get('constraints', {})
            prompt['version'] = '2.0'
            prompt['last_updated'] = datetime.now().isoformat()
            
            # Save enhanced prompt
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(prompt, f, indent=2, ensure_ascii=False)
            
            return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Mass-enhance all prompts in the collection."""
    prompts_dir = Path("prompts")
    enhanced_count = 0
    
    for category_dir in prompts_dir.iterdir():
        if category_dir.is_dir():
            for prompt_file in category_dir.glob("*.json"):
                if enhance_prompt(str(prompt_file), PROMPT_ENHANCEMENTS):
                    enhanced_count += 1
                    print(f"✅ Enhanced: {prompt_file.name}")
    
    print(f"\n✅ Successfully enhanced {enhanced_count} prompts to Schema v2.0!")

if __name__ == "__main__":
    main()
