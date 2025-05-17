#!/bin/zsh

# Baddy Agent Repository Initialization Script

# Set working directory
cd /Users/mac/Documents/Cursor_SecondBrain_Release_Package

echo "🚀 Initializing Baddy Agent Repository..."

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI not found. Installing..."
    brew install gh
fi

# Check if authenticated with GitHub
if ! gh auth status &> /dev/null; then
    echo "🔑 Authenticating with GitHub..."
    gh auth login
fi

# Initialize Git repository
echo "📦 Initializing Git repository..."
git init

# Add all files
echo "📝 Adding files to Git..."
git add .

# Create initial commit
echo "💾 Creating initial commit..."
git commit -m "Initial commit: Baddy Agent v1.0"

# Create GitHub repository
echo "🌐 Creating GitHub repository..."
gh repo create BaddyAgent \
    --public \
    --source=. \
    --remote=origin \
    --push

# Set up branch protection
echo "🛡️ Setting up branch protection..."
gh api repos/Njanja2025/BaddyAgent/branches/main/protection \
    -X PUT \
    -H "Accept: application/vnd.github.v3+json" \
    -f required_status_checks='{"strict":true,"contexts":["test","build"]}' \
    -f enforce_admins=true \
    -f required_pull_request_reviews='{"dismissal_restrictions":{},"dismiss_stale_reviews":true,"require_code_owner_reviews":true,"required_approving_review_count":1}' \
    -f restrictions=null

# Create development branch
echo "🌿 Creating development branch..."
git checkout -b develop
git push -u origin develop

# Return to main branch
git checkout main

echo "
✅ Repository initialization complete!

Your Baddy Agent repository is now available at:
https://github.com/Njanja2025/BaddyAgent

Next steps:
1. Review the repository settings
2. Add collaborators if needed
3. Set up branch protection rules
4. Configure GitHub Actions secrets

For more information, visit:
https://github.com/Njanja2025/BaddyAgent/wiki
"

# Open repository in browser
gh repo view --web 