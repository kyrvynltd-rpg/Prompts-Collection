# 💡 Prompt Improvement Tool

A powerful Python application built with Streamlit that helps you improve your AI prompts using a curated collection of best practices and logical analysis. Enter your prompt and get intelligent recommendations based on our extensively refined collection of 114 carefully crafted prompts.

## ✨ Features

- **🔍 Prompt Analysis**: Analyse your prompts against best practices from our curated collection
- **💡 Smart Recommendations**: Get prioritised, actionable recommendations to improve your prompts
- **📊 Best Practices Scoring**: See how your prompt measures against key best practices
- **✨ Auto-Improvement**: Get suggested improved versions of your prompts
- **Reference Collection**: Access 114 high-quality example prompts across 12 categories
- **🎯 Category-Specific Suggestions**: Get recommendations tailored to your prompt's category
- **🔎 Similar Prompt Discovery**: Find similar prompts from our collection for inspiration
- **🧠 Intelligent Recommendations**: Match prompts by intent, difficulty, time, and output format
- **🛤️ Learning Paths**: Follow category progression from beginner to expert prompts
- **📋 Easy Copy**: Copy improved prompts with one click

## 📦 Prompt Collection

Our curated collection includes 114 high-quality prompts across 12 categories:

1. **AI Assistant** (10 prompts) - General purpose and specialized research assistants
2. **Coding & Development** (15 prompts) - Programming, debugging, DevOps, and technical prompts
3. **Writing & Content** (13 prompts) - Blog posts, emails, editing, fact-checking, documentation
4. **Business & Strategy** (11 prompts) - Business planning, market research, proposals, change management
5. **Education & Learning** (8 prompts) - Tutoring, study guides, quizzes, training, language learning
6. **Creative & Design** (9 prompts) - Storytelling, poetry, world building, UI/UX design, research
7. **Data Analysis** (7 prompts) - Data analysis, statistics, visualization, qualitative analysis, ML
8. **Productivity & Organization** (9 prompts) - Task management, goal setting, time management, habit building
9. **Health & Wellness** (8 prompts) - Fitness, nutrition, mental health, sleep, meditation, recovery *(with health disclaimers)*
10. **Marketing & Sales** (8 prompts) - Marketing strategy, email campaigns, A/B testing, SEO, branding
11. **Legal & Compliance** (8 prompts) - Legal document review, privacy policies, compliance, IP protection
12. **Customer Service** (8 prompts) - Customer support, FAQ generation, feedback analysis, loyalty programs

## 🚀 Getting Started

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. **Clone or download this repository**

   ```bash
   git clone <repository-url>
   cd Prompts-Collection
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:

   ```bash
   python main.py
   ```

   Or directly with Streamlit:

   ```bash
   streamlit run src/app.py
   ```

4. **Open your browser**:
   The app will automatically open in your default browser at `http://localhost:8501`

## 🌐 Deployment (For Student Use)

This app is ready to deploy as a standard Streamlit web service.

Detailed operational guide:

- See [DEPLOYMENT_RUNBOOK.md](DEPLOYMENT_RUNBOOK.md) for click-by-click Render deployment, Azure Container Apps steps, and launch-day rollback/contingency planning.

### Option A: Render (Fastest hosted setup)

This repository now includes `render.yaml` for one-click setup.

1. Push this repo to GitHub
2. In Render, choose **New +** -> **Blueprint**
3. Select this repository
4. Render reads `render.yaml` and deploys automatically

Start command used:

```bash
streamlit run src/app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```

### Option B: Docker (Portable to any cloud)

This repository includes `Dockerfile` and `.dockerignore`.

Build and run locally:

```bash
docker build -t prompts-collection .
docker run --rm -p 8501:8501 -e PORT=8501 prompts-collection
```

Then deploy the same image to Azure Container Apps, AWS ECS, GCP Cloud Run, or any container host.

### Option C: Streamlit Community Cloud

1. Push to GitHub
2. Create a new app in Streamlit Community Cloud
3. Main file path: `src/app.py`
4. Python dependencies: `requirements.txt`

## ✅ Pre-Launch Checklist (Before Next Week)

1. Smoke-test deployment URL from a student network and mobile network
2. Verify all prompt categories load correctly
3. Confirm app start-up time is acceptable under cold start
4. Set a simple uptime monitor (for example, UptimeRobot)
5. Keep one backup deployment target ready (Render + Docker fallback)

## 📖 Usage

### Improving Your Prompts

1. **Enter Your Prompt**: Type or paste your prompt in the main text area
2. **Analyse**: Click "🔍 Analyse & Improve Prompt" or press Enter
3. **Review Recommendations**:

   - See your best practices score
   - Review prioritized recommendations (High/Medium/Low priority)
   - Check detailed breakdown of what's missing
4. **Get Improved Version**: View the suggested improved prompt
5. **Copy & Use**: Copy the improved prompt and use it with your AI

### Understanding Recommendations

Recommendations are prioritized:

- **🔴 High Priority**: Critical improvements (e.g., missing role definition, no action verbs)
- **🟡 Medium Priority**: Important enhancements (e.g., output format, quality markers)
- **🟢 Low Priority**: Nice-to-have improvements (e.g., examples, sentence structure)

### Sidebar Features

- **Search & Filter**: Browse the prompt collection by category and tags
- **Favourites**: Save prompts you like (session-based)
- **About**: Quick information about the tool

## 📁 Project Structure

```text
Prompts-Collection/
│
├── main.py                 # Entry point - runs the Streamlit app
├── src/
│   ├── app.py             # Main Streamlit application
│   └── prompt_loader.py   # Utility module to load prompts from file system
├── prompts/               # Prompt data directory
│   ├── AI Assistant/
│   │   ├── general-purpose-assistant.json
│   │   └── ...
│   ├── Coding & Development/
│   │   ├── python-code-generator.json
│   │   └── ...
│   └── ... (other categories)
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── .gitignore           # Git ignore rules
```

## 📄 Prompt File Format

Each prompt in the collection is stored as a JSON file using Schema v2.0:

```json
{
   "schema_version": "2.0",
  "title": "Prompt Title",
  "prompt": "You are an expert... [the actual prompt text]",
  "tags": ["tag1", "tag2", "tag3"],
   "description": "Brief description of what this prompt does",
   "difficulty_level": "beginner|intermediate|expert",
   "time_estimate": "quick|moderate|thorough",
   "output_format": "text|markdown|code|json|structured",
   "expected_outcomes": ["Outcome 1", "Outcome 2"],
   "prerequisites": ["Prerequisite 1", "Prerequisite 2"],
   "use_case_examples": ["Use case 1", "Use case 2", "Use case 3"],
   "success_criteria": ["Criterion 1", "Criterion 2", "Criterion 3"],
   "tone": "formal|friendly|technical|neutral",
   "best_for": "Target user profile",
   "avoid_if": "When this prompt is not appropriate",
   "constraints": {},
   "related_prompts": {
      "after_this": ["prompt-a", "prompt-b"],
      "before_this": ["prompt-c", "prompt-d"],
      "workflow_chains": [
         {
            "name": "Category execution flow",
            "prompts": ["current-prompt", "next-prompt", "follow-up-prompt"]
         }
      ]
   }
}
```

## 🔧 How It Works

The tool uses logical Python analysis to:

1. **Extract Patterns**: Analyses all prompts in the collection to identify common patterns
2. **Find Similar Prompts**: Uses keyword matching and similarity scoring to find relevant examples
3. **Analyse Structure**: Checks for role definitions, action verbs, quality markers, constraints, etc.
4. **Generate Recommendations**: Provides specific, actionable suggestions based on best practices
5. **Improve Prompts**: Automatically generates improved versions with missing elements added

### Best Practices Analysed

- ✅ **Role Definition**: Does the prompt define the AI's role?
- ✅ **Specific Instructions**: Are there clear action verbs?
- ✅ **Output Format**: Is the desired output format specified?
- ✅ **Quality Markers**: Are quality indicators included?
- ✅ **Constraints/Standards**: Are guidelines or best practices mentioned?

## 🔧 Customization

### Adding New Prompts to the Collection

#### Method 1: Add JSON File Directly

1. Navigate to the appropriate category folder in `prompts/`
2. Create a new JSON file (use lowercase, hyphens for spaces in filename)
3. Use the format shown above
4. Restart the app - new prompts will be automatically included in analysis

#### Method 2: Use Python Script

```python
from src.prompt_loader import save_prompt

save_prompt(
    category="AI Assistant",
    title="My New Prompt",
    prompt_text="You are an expert...",
    tags=["tag1", "tag2"],
    description="Description of the prompt"
)
```

### Adding New Categories

1. Create a new folder in the `prompts/` directory
2. Add JSON prompt files to that folder
3. The app will automatically detect and include the new category

## 🎯 Use Cases

This tool is perfect for:

- **AI Enthusiasts**: Improve your prompts for better AI interactions
- **Developers**: Get better code generation and technical prompts
- **Content Creators**: Enhance writing and content creation prompts
- **Business Professionals**: Refine business and strategy prompts
- **Educators**: Improve educational and learning prompts
- **Anyone**: Make your AI prompts more effective

## 🎨 Key Features Explained

### Smart Analysis

- Uses Jaccard similarity and keyword matching to find relevant examples
- Analyses prompt structure (sentence count, word count, formatting)
- Category-aware recommendations

### Pattern Recognition

- Extracts common patterns from 114 carefully curated example prompts
- Identifies best practices by category
- Learns from similar prompts in the collection

### Intelligent Suggestions

- Context-aware role inference
- Category-specific constraint suggestions
- Quality marker recommendations based on prompt type

## 📝 Notes

- Analysis is performed using logical Python algorithms (no external AI APIs)
- Recommendations are based on patterns found in our collection of 114 high-quality prompts
- Similar prompts are found using keyword matching and similarity scoring
- Favourites are stored in session state and reset when you refresh the page
- All prompts are stored as JSON files in the `prompts/` directory

## 🔄 Updating the Collection

To update the prompts collection:

1. **Add new prompts**: Create JSON files in the appropriate category folders
2. **Edit existing prompts**: Modify the JSON files directly
3. **Remove prompts**: Delete the JSON files
4. **Restart the app**: Changes will be reflected after restarting

## 🤝 Contributing

Feel free to:

- Add more prompts to existing categories
- Create new categories
- Improve the analysis logic
- Add new features
- Fix bugs or improve code quality

## 📊 Statistics

The platform currently includes:

- **114 high-quality prompts** across 12 categories
- **Quality-enhanced collection** with improved specificity, disclaimers, and best practices
- **Specialized coverage** (Java, TypeScript, CI/CD, Email Marketing, UX Research, Qualitative Analysis)
- **Comprehensive gap coverage** addressing missing domains from the original audit

## 📄 License

Proprietary. Copyright (c) 2026 Gabriele Iacopo Langellotto. All rights reserved. See [LICENSE](LICENSE).

## 🙏 Acknowledgments

Built with:

- [Streamlit](https://streamlit.io/) - The framework for building the web app
- Python - The programming language
- JSON - For structured prompt storage

---

**Make your prompts better using our curated collection and logical Python analysis!** 💡

**Tip**: Browse the `prompts/` folder directly in your file explorer to see all available prompts organized by category!
