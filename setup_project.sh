#!/bin/bash

# Create main project directories
mkdir -p src/secondbrain/{core,utils,gui,voice,config,tests}
mkdir -p data/{logs,cache,user_data}
mkdir -p docs/{api,user_guide}

# Move existing files to appropriate locations
mv main.py src/secondbrain/
mv voice_processor.py src/secondbrain/voice/
mv assistant.py src/secondbrain/core/
mv voice_config.json src/secondbrain/config/

# Create gitignore
cat > .gitignore << EOL
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.env
.venv
venv/
ENV/
.DS_Store
data/logs/*
data/cache/*
!data/logs/.gitkeep
!data/cache/.gitkeep
EOL

# Create empty __init__.py files
touch src/secondbrain/__init__.py
touch src/secondbrain/core/__init__.py
touch src/secondbrain/utils/__init__.py
touch src/secondbrain/gui/__init__.py
touch src/secondbrain/voice/__init__.py
touch src/secondbrain/tests/__init__.py

# Make script executable
chmod +x setup_project.sh

echo "Project structure setup complete!" 