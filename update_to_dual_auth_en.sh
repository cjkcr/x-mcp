#!/bin/bash

# Twitter API Dual Authentication Update Script
# Updates existing x-mcp installation to support OAuth 1.0a + OAuth 2.0

echo "🔄 Twitter API Dual Authentication Update Script"
echo "==============================================="

# Check if we're in the correct directory
if [ ! -f "pyproject.toml" ] || [ ! -d "src/x_mcp" ]; then
    echo "❌ Error: Please run this script from the x-mcp project root directory"
    exit 1
fi

echo "✅ x-mcp project detected"

# Backup current configuration
echo "📦 Backing up current drafts..."
if [ -d "drafts" ]; then
    cp -r drafts drafts_backup_$(date +%Y%m%d_%H%M%S)
    echo "✅ Drafts backed up"
fi

# Check git status
if command -v git &> /dev/null && [ -d ".git" ]; then
    echo "📋 Checking git status..."
    if [ -n "$(git status --porcelain)" ]; then
        echo "⚠️  Warning: There are uncommitted changes, recommend committing or backing up first"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ Update cancelled"
            exit 1
        fi
    fi
fi

# Pull latest changes (if git repository)
if command -v git &> /dev/null && [ -d ".git" ]; then
    echo "🔄 Pulling latest changes..."
    git pull origin main || git pull origin master
fi

# Install/update dependencies
echo "📦 Updating dependencies..."
if command -v uv &> /dev/null; then
    uv sync
else
    echo "⚠️  Warning: uv not found, please ensure it's installed"
fi

# Run tests
echo "🧪 Running connection tests..."
python test_tweet_functions.py

echo ""
echo "🎉 Update complete!"
echo ""
echo "📋 Next steps:"
echo "1. Get Bearer Token from Twitter Developer Portal"
echo "2. Update Claude Desktop config, add TWITTER_BEARER_TOKEN"
echo "3. Restart Claude Desktop"
echo "4. Run 'test api connection' in Claude to verify configuration"
echo ""
echo "📚 Detailed configuration guides:"
echo "- OAuth_Dual_Authentication_Setup_Guide.md"
echo "- README.md"
echo ""
echo "🔧 If you encounter issues:"
echo "- Run 'python test_tweet_functions.py' for diagnostics"
echo "- Check '推文获取功能故障排除指南.md' (Chinese troubleshooting guide)"
echo "- Run 'test api connection' in Claude"