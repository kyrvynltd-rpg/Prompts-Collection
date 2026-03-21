# Enhanced JSON Schema v2.0 Specification

## Overview
The Prompt Collection uses an enhanced JSON schema (v2.0) that adds metadata and structure to enable intelligent recommendations and advanced discovery features.

## Schema Definition

```json
{
  "schema_version": "2.0",
  "id": "unique-prompt-id",
  "title": "Prompt Title",
  "category": "Category Name",
  "subcategory": "Optional subcategory",
  
  "prompt": "Full prompt text with context, role, task, constraints...",
  "description": "12-15 word summary of what this prompt does",
  
  "difficulty_level": "beginner|intermediate|expert",
  "time_estimate": "quick|moderate|thorough",
  "output_format": "text|markdown|json|code|structured",
  
  "expected_outcomes": [
    "Outcome 1: Specific deliverable",
    "Outcome 2: Specific deliverable",
    "Outcome 3: Specific deliverable"
  ],
  
  "prerequisites": [
    "Any domain knowledge needed",
    "Tools or context user should have"
  ],
  
  "use_case_examples": [
    "Real-world use case 1",
    "Real-world use case 2",
    "Real-world use case 3"
  ],
  
  "success_criteria": [
    "How users know this worked well",
    "What good output looks like"
  ],
  
  "constraints": {
    "max_scope": "Boundary on what prompt covers",
    "language_support": ["English", "..."],
    "file_size_limit": "When applicable"
  },
  
  "tone": "formal|friendly|technical|neutral",
  "best_for": "Who benefits most from this prompt",
  "avoid_if": "When this prompt is NOT a good fit",
  
  "tags": {
    "primary": "main-category",
    "secondary": ["tag1", "tag2", "tag3"],
    "skills": ["skill1", "skill2"]
  },
  
  "related_prompts": [
    "prompt-id-1-for-chaining",
    "prompt-id-2-for-workflow"
  ],
  
  "disclaimer": "Legal/safety disclaimers if needed",
  "version": "2.0",
  "last_updated": "2026-03-21"
}
```

## Field Descriptions

### Core Identity
- **schema_version**: "2.0" (enables versioning and migration)
- **id**: Unique identifier (use kebab-case filename)
- **title**: Clear, action-oriented title
- **category**: One of 12 main categories
- **prompt**: Complete prompt text with all guidance

### Metadata (New in v2.0)
- **difficulty_level**: 
  - "beginner": Minimal prerequisite knowledge
  - "intermediate": Some domain experience expected
  - "expert": Deep expertise required
  
- **time_estimate**: 
  - "quick": Executes in <5 minutes
  - "moderate": 5-30 minutes
  - "thorough": 30+ minutes
  
- **output_format**: 
  - "text": Prose/paragraphs
  - "markdown": Formatted with headers/lists
  - "json": Structured data
  - "code": Programming code
  - "structured": Specific template

### User Guidance (New in v2.0)
- **expected_outcomes**: Concrete deliverables user will receive
- **prerequisites**: Required knowledge/tools/context
- **use_case_examples**: 3-5 real-world scenarios
- **success_criteria**: How to evaluate output quality
- **constraints**: Scope boundaries and limitations

### Discovery Optimization (New in v2.0)
- **tone**: Communication style expected
- **best_for**: Target user profile
- **avoid_if**: When NOT to use this prompt
- **tags.primary**: Main category for search
- **tags.secondary**: Additional search keywords
- **tags.skills**: Skills this prompt teaches/develops
- **related_prompts**: Workflow combinations

### Governance (New in v2.0)
- **disclaimer**: Safety/legal notices
- **version**: Prompt version (1.0, 1.1, 2.0, etc.)
- **last_updated**: Last modification date

## Backward Compatibility
- All v1.0 fields (title, prompt, description, tags) retained
- New fields are optional (legacy prompts degrade gracefully)
- Tools support both schema versions

## Migration Path
1. ✅ Phase 1: Add critical v2.0 fields to all prompts
2. ✅ Phase 2: Complete metadata population
3. ✅ Phase 3: Version track and deprecate v1.0
4. ✅ Phase 4: Build recommendation engine on v2.0 foundation
