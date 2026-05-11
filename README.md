# Flask Starter Kit

This is a Flask starter kit with basic structure and tooling for web application development.

## Quick Start (Local Development)

1. **Clone and setup virtual environment:**
   ```bash
   git clone <your-repo-url>
   cd starter-template-crud-f25
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   heroku config:get JAWSDB_URL  # Copy this value to your .env file
   ```

3. **Setup database (first time only):**

   Run `database/schema.sql` in your JAWS DB using MySQL Workbench or the Heroku console.

4. **Run the app:**
   ```bash
   flask run
   ```

5. **Visit:** http://localhost:5000

## Deploying to Heroku

1. **Create Heroku app and add JAWS DB:**
   ```bash
   heroku create your-app-name
   heroku addons:create jawsdb:kitefin
   ```

2. **Set your secret key:**
   ```bash
   heroku config:set FLASK_SECRET_KEY=your-secure-random-key
   ```

3. **Deploy:**
   ```bash
   git push heroku main
   ```

JAWS DB automatically configures the `JAWSDB_URL` environment variable - no manual database config needed.

## Project Structure
As your project grows, consider adding these organizational folders:

### Recommended Additions
- `docs/` - API documentation, setup guides, deployment notes
- `docs/features/` - Feature specifications and requirements  
- `docs/architecture/` - System design documents
- `tests/` - Unit and integration tests
- `migrations/` - Database schema changes (if using Flask-Migrate)
- `config/` - Environment-specific configurations
- `.github/workflows/` - CI/CD pipelines (if using GitHub)
- `.vscode/` - Cursor/VS Code workspace settings

### Documentation Files
- `CHANGELOG.md` - Track version changes and updates
- `.env.example` - Template for environment variables

**Note**: Only create these folders as your project actually needs them. Don't over-structure early.

## AI Workflow Integration
This folder includes prompts that should be copy/pasted into your docs/commands folder and then used by tagging them in the chat (e.g. @plan_feature.md) and providing additional context such as the description of your feature.

Feel free to customize them to your needs! These are really just a starting point and what works for me.

[![The Perfect Cursor AI Workflow (3 Simple Steps)](https://img.youtube.com/vi/Jem2yqhXFaU/0.jpg)](https://youtu.be/Jem2yqhXFaU)
> 🎥 The Perfect Cursor AI Workflow (3 Simple Steps)

# Example Use
## Create Brief
Used for establishing the bigger picture context of what this project is about which can be helpful to plan new features.
```
@create_brief.md 

We are building an application to help dungeon masters plan their D&D campaigns and it's going to be called Dragonroll. It will include a variety of different tools, such as a random map generator and bc generator, loot generator and so on. We will use ai and allow the dungeon master to input certain prompts or use the tools directly.
```

## Plan Feature
Used to create a technical plan for a new feature. Focuses on the technical requirements - NOT product manager context bloat or overly specific code details.
```
@plan_feature.md 

We want to add a new page that is going to be our NPC generator. To implement this, we are going to use the open ai api to generate the description of the npc as well as a name And we'll also generate an image for the npc using the open ai gpt-image-1 model.
```

## Code Review
Used to review the successful completion of a plan in a separate chat (and yes, it's this minimal)
```
@code_review.md
@0001_PLAN.md
```

## Documentation Writing
Used to create comprehensive documentation for the plan, review, and implementation.
```
@write_docs.md
@0001_PLAN.md
@0001_REVIEW.md
```