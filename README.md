# X(Twitter) MCP Server

[![smithery badge](https://smithery.ai/badge/x-mcp)](https://smithery.ai/server/x-mcp)

**English** | [中文](README_CN.md)

An MCP server to create, manage and publish X/Twitter posts directly through Claude code and Gemini CLI chat.

> **Note:** This project is modified from [vidhupv/x-mcp](https://github.com/vidhupv/x-mcp), with added reply functionality for tweets.

## Features

### 🔐 Dual Authentication Support
- ✅ **OAuth 1.0a**: For write operations (posting tweets, retweeting, etc.)
- ✅ **OAuth 2.0**: For read operations (getting tweets, searching, etc.)
- ✅ **Automatic Client Selection**: System automatically chooses the best authentication method
- ✅ **Smart Fallback**: Automatically falls back to OAuth 1.0a when OAuth 2.0 is unavailable

### 📝 Tweet Management
- ✅ Create draft tweets
- ✅ Create draft tweet threads
- ✅ Create draft replies to existing tweets
- ✅ List all drafts
- ✅ Publish drafts (tweets, threads, and replies)
- ✅ Reply to tweets directly (without creating drafts)
- ✅ Retweet existing tweets
- ✅ Quote tweet with comments
- ✅ Create draft quote tweets
- ✅ Delete drafts
- ✅ Auto-delete failed drafts (configurable)
- ✅ Draft preservation on publish failure (configurable)

### ⏰ Scheduled Tweets (NEW!)
- ✅ **Schedule single tweets** - Publish tweets at specific times
- ✅ **Schedule tweet threads** - Publish complete threads at specific times
- ✅ **Recurring tweets** - Publish tweets at regular intervals
- ✅ **Flexible time formats** - Support absolute time (2024-01-15T14:30:00) and relative time (+10m, +2h, +1d)
- ✅ **Background scheduler** - Automatic execution without manual intervention
- ✅ **Schedule management** - View, cancel, and manage all scheduled tweets
- ✅ **Smart intervals** - Perfect for regular content publishing and campaigns

### 📷 Media Support
- ✅ Upload media files (images, videos, GIFs)
- ✅ Create tweets with media attachments
- ✅ Add alt text for accessibility
- ✅ Get media file information

### 📖 Tweet Retrieval (Enhanced)
- ✅ Get tweet content and information (with dual authentication support)
- ✅ Search recent tweets (improved error handling)
- ✅ Batch retrieve multiple tweets (more stable connections)
- ✅ Detailed error diagnostics and suggestions
- ✅ API connection testing tools

<a href="https://glama.ai/mcp/servers/jsxr09dktf">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/jsxr09dktf/badge" alt="X(Twitter) Server MCP server" />
</a>

## System Requirements

Before starting the installation, please ensure your system meets the following requirements:

### Required Software
- **Python 3.8+** - Project runtime environment
- **Node.js 16+** - For installing Gemini CLI (if using Gemini)
- **UV** - Python package manager (recommended) or pip
- **Git** - For cloning the project

### Installing Prerequisites

**macOS Users:**
```bash
# Install Homebrew (if you don't have it)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required software
brew install python node git uv
```

**Windows Users:**
```bash
# Using Chocolatey (recommended)
choco install python nodejs git

# Then install UV
pip install uv
```

**Linux Users:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip nodejs npm git
pip3 install uv

# CentOS/RHEL
sudo yum install python3 python3-pip nodejs npm git
pip3 install uv
```

## Quick Setup

### Installing via Smithery

To install X(Twitter) MCP Server for Claude code automatically via [Smithery](https://smithery.ai/server/x-mcp):

```bash
npx -y @smithery/cli install x-mcp --client claude
```

### Manual Installation for Claude code

#### 1. Project Setup

**Clone project and set up environment:**
```bash
# Clone the repository
git clone https://github.com/yourusername/x-mcp.git
cd x-mcp

# Install UV (Python package manager)
# macOS users (recommended):
brew install uv

# Or use pip:
pip install uv
```

**Install dependencies (choose one method):**

**Method 1: Automatic environment creation and installation (Recommended)**
```bash
# One step: create virtual environment and install dependencies
uv sync

# Activate virtual environment (if manual operation needed)
# macOS/Linux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate
```

**Method 2: Manual environment creation and installation**
```bash
# Manually create virtual environment
uv venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

# Install dependencies from pyproject.toml
uv pip sync pyproject.toml
```

#### 2. Configure Claude Desktop

**Create claude_desktop_config.json:**
   - **For MacOS:** Open directory `~/Library/Application Support/Claude/` and create the file inside it
   - **For Windows:** Open directory `%APPDATA%/Claude/` and create the file inside it

**Add this configuration to claude_desktop_config.json:**

#### Basic Configuration (OAuth 1.0a Only)
```json
{
  "mcpServers": {
    "x_mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/x-mcp",
        "run",
        "x-mcp"
      ],
      "env": {
        "TWITTER_API_KEY": "your_api_key",
        "TWITTER_API_SECRET": "your_api_secret",
        "TWITTER_ACCESS_TOKEN": "your_access_token",
        "TWITTER_ACCESS_TOKEN_SECRET": "your_access_token_secret"
      }
    }
  }
}
```

#### Recommended Configuration (OAuth 1.0a + OAuth 2.0 Dual Authentication)
```json
{
  "mcpServers": {
    "x_mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/x-mcp",
        "run",
        "x-mcp"
      ],
      "env": {
        "TWITTER_API_KEY": "your_api_key",
        "TWITTER_API_SECRET": "your_api_secret",
        "TWITTER_ACCESS_TOKEN": "your_access_token",
        "TWITTER_ACCESS_TOKEN_SECRET": "your_access_token_secret",
        "TWITTER_BEARER_TOKEN": "your_bearer_token"
      }
    }
  }
}
```

> **💡 Recommended to use dual authentication configuration**: Adding `TWITTER_BEARER_TOKEN` can significantly improve the stability and success rate of tweet retrieval functions.

#### 3. Get X/Twitter API Credentials

1. **Visit X API Developer Portal:**
   - Go to [X API Developer Portal](https://developer.x.com/en/products/x-api)
   - Create a developer account (if you don't have one)

2. **Create Project and App:**
   - Create a new project
   - Create an app within the project

3. **Configure App Permissions:**
   - In User Authentication Settings: Set to **Read and Write permissions**
   - App type: Select **Web App**
   - Callback URL: Set to `http://localhost/`
   - Website URL: Set to `http://example.com/`

4. **Generate API Keys and Tokens:**
   - From the "Keys and Tokens" section, generate:
     - API Key (Consumer Key)
     - API Secret (Consumer Secret)
     - Access Token
     - Access Token Secret
     - Bearer Token (recommended for dual authentication)

#### 4. Update Configuration and Start

**Update the config file:**
   - Replace `/path/to/x-mcp` with your actual project path (e.g., `/Users/yourname/x-mcp`)
   - Replace all `your_*` placeholders with your actual API credentials

**Quit Claude completely and reopen it**

#### 5. Verify Installation

Test the connection in Claude:
```
test api connection
```

If everything is configured correctly, you should see successful connection test results.

### Configuration for Gemini CLI

If you want to use this MCP server with Gemini CLI instead of Claude code:

#### 1. Project Setup

**Clone project and set up environment:**
```bash
# Clone the repository
git clone https://github.com/yourusername/x-mcp.git
cd x-mcp

# Install UV (Python package manager)
# macOS users:
brew install uv

# Or use pip:
pip install uv
```

**Install dependencies (choose one method):**

**Method 1: Automatic environment creation and installation (Recommended)**
```bash
# One step: create virtual environment and install dependencies
uv sync

# Activate virtual environment (if manual operation needed)
# macOS/Linux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate
```

**Method 2: Manual environment creation and installation**
```bash
# Manually create virtual environment
uv venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

# Install dependencies from pyproject.toml
uv pip sync pyproject.toml
```

#### 2. Install and Configure Gemini CLI

**Install Gemini CLI:**
```bash
npm install -g @google/gemini-cli
```

**Create or update your MCP configuration file:**
```bash
# Create configuration directory (if it doesn't exist)
mkdir -p ~/.gemini

# Create configuration file
touch ~/.gemini/settings.json
```

**Edit configuration file `~/.gemini/settings.json`:**

#### Basic Configuration (OAuth 1.0a Only)
```json
{
  "mcpServers": {
    "x_mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/x-mcp",
        "run",
        "x-mcp"
      ],
      "env": {
        "TWITTER_API_KEY": "your_api_key",
        "TWITTER_API_SECRET": "your_api_secret",
        "TWITTER_ACCESS_TOKEN": "your_access_token",
        "TWITTER_ACCESS_TOKEN_SECRET": "your_access_token_secret"
      }
    }
  }
}
```

#### Recommended Configuration (OAuth 1.0a + OAuth 2.0 Dual Authentication)
```json
{
  "mcpServers": {
    "x_mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/x-mcp",
        "run",
        "x-mcp"
      ],
      "env": {
        "TWITTER_API_KEY": "your_api_key",
        "TWITTER_API_SECRET": "your_api_secret",
        "TWITTER_ACCESS_TOKEN": "your_access_token",
        "TWITTER_ACCESS_TOKEN_SECRET": "your_access_token_secret",
        "TWITTER_BEARER_TOKEN": "your_bearer_token"
      }
    }
  }
}
```

#### 3. Get X/Twitter API Credentials

1. **Visit X API Developer Portal:**
   - Go to [X API Developer Portal](https://developer.x.com/en/products/x-api)
   - Create a developer account (if you don't have one)

2. **Create Project and App:**
   - Create a new project
   - Create an app within the project

3. **Configure App Permissions:**
   - In User Authentication Settings: Set to **Read and Write permissions**
   - App type: Select **Web App**
   - Callback URL: Set to `http://localhost/`
   - Website URL: Set to `http://example.com/`

4. **Generate API Keys and Tokens:**
   - From the "Keys and Tokens" section, generate:
     - API Key (Consumer Key)
     - API Secret (Consumer Secret)
     - Access Token
     - Access Token Secret
     - Bearer Token (recommended for dual authentication)

#### 4. Update Configuration and Start

**Update the config file:**
- Replace `/path/to/x-mcp` with your actual project path (e.g., `/Users/yourname/x-mcp`)
- Replace all `your_*` placeholders with your actual API credentials

**Start Gemini CLI:**
```bash
# Start Gemini CLI with MCP support
gemini-cli

# Or if you need to specify config file path:
gemini-cli --config ~/.gemini/settings.json
```

#### 5. Verify Installation

Test the connection in Gemini CLI:
```
test api connection
```

If everything is configured correctly, you should see successful connection test results.

## Advanced Configuration

### Auto-Delete Failed Drafts

When tweet publishing fails, you can choose whether to automatically delete drafts:

- **Enable auto-delete** (default): Automatically delete drafts when publishing fails to avoid accumulating invalid drafts
- **Disable auto-delete**: Preserve drafts when publishing fails, allowing manual retry or modification

#### Configuration Methods

1. **Via Environment Variable**: Add `"AUTO_DELETE_FAILED_DRAFTS": "true"` or `"false"` in your configuration file
2. **Via Commands**: Use "Enable auto-delete failed drafts" or "Disable auto-delete failed drafts"
3. **Check Status**: Use "Check current auto-delete configuration"

## Usage Examples

Works with both Claude code and Gemini CLI:

### Basic Tweet Operations
* "Tweet 'Just learned how to tweet through AI - mind blown! 🤖✨'"
* "Create a thread about the history of pizza"
* "Show me my draft tweets"
* "Publish this draft!"
* "Delete that draft"
* "Reply to tweet 1234567890 with 'Great point! Thanks for sharing.'"
* "Create a draft reply to tweet 1234567890 saying 'I completely agree with this perspective.'"
* "Retweet tweet 1234567890"
* "Quote tweet 1234567890 with comment 'This is exactly what I was thinking!'"
* "Create a draft quote tweet for 1234567890 with comment 'Amazing insight here'"

### Media Operations
* "Upload image /path/to/image.jpg with alt text 'Beautiful sunset over the mountains'"
* "Create tweet with media 'Check out this amazing photo!' using media IDs 123456789"
* "Create draft tweet with media 'My latest project' and attach /path/to/video.mp4"

### Scheduled Tweets (NEW!)
* "Schedule a tweet 'Good morning everyone! ☀️' for tomorrow at 9 AM"
* "Create a scheduled thread about productivity tips for next Monday at 2 PM"
* "Set up recurring tweets every 10 minutes starting in 5 minutes: ['Tip 1: Stay hydrated', 'Tip 2: Take breaks', 'Tip 3: Exercise regularly']"
* "Schedule tweet 'Weekend vibes! 🎉' for +2h"
* "Create recurring tweets every 30 minutes for the next 3 hours with motivational quotes"
* "List all my scheduled tweets"
* "Cancel scheduled tweet scheduled_tweet_1234567890.json"
* "Start the tweet scheduler"
* "Stop the tweet scheduler"

### Configuration & Management
* "Enable auto-delete failed drafts"
* "Disable auto-delete failed drafts"
* "Check current auto-delete configuration"

### Tweet Retrieval
* "Get tweet 1234567890 content and information"
* "Search for tweets containing 'AI OR artificial intelligence' from the last 7 days"
* "Get information for tweets 123456789, 987654321, 555666777"

## Troubleshooting

### Environment Setup Issues

**UV not found or installation failed:**
```bash
# Check if UV is properly installed
which uv
uv --version

# If not found, reinstall
pip uninstall uv
brew install uv  # macOS
# or
pip install uv   # other systems
```

**Virtual environment issues:**
```bash
# Delete existing virtual environment
rm -rf .venv

# Recreate (choose one method):

# Method 1: Automatic creation and installation (recommended)
uv sync

# Method 2: Manual creation and installation
uv venv
source .venv/bin/activate  # macOS/Linux or .venv\Scripts\activate (Windows)
uv pip sync pyproject.toml
```

**Python version incompatibility:**
```bash
# Check Python version (requires 3.8+)
python --version
python3 --version

# If version is too old, upgrade Python
brew install python@3.11  # macOS
# or use your system package manager to upgrade
```

### Basic Issues
If not working:
- Make sure UV is installed globally (if not, uninstall with `pip uninstall uv` and reinstall with `brew install uv`)
- Or find UV path with `which uv` and replace `"command": "uv"` with the full path
- Verify all X/Twitter credentials are correct
- Check if the x-mcp path in config matches your actual repository location

### 🔧 API Connection Testing

**Quick Diagnosis:**
```
test api connection
```
Running this command in Claude will:
- Test OAuth 1.0a and OAuth 2.0 connections
- Check API permissions and limitations
- Provide detailed diagnostic information and suggestions

**Run Test Script:**
```bash
cd /path/to/x-mcp
python test_tweet_functions.py
```

### 🚨 401 Unauthorized Error Fix

**Problem Symptoms:**
- Getting "401 Unauthorized" error when posting tweets
- Can post tweets but cannot retrieve tweets

**Solutions:**

1. **Add Bearer Token (Recommended):**
   ```json
   "env": {
     "TWITTER_API_KEY": "your_api_key",
     "TWITTER_API_SECRET": "your_api_secret",
     "TWITTER_ACCESS_TOKEN": "your_access_token",
     "TWITTER_ACCESS_TOKEN_SECRET": "your_access_token_secret",
     "TWITTER_BEARER_TOKEN": "your_bearer_token"
   }
   ```

2. **Regenerate API Credentials:**
   - Visit [Twitter Developer Portal](https://developer.x.com/)
   - Regenerate all API keys and tokens
   - Ensure permissions are set to "Read and write"

3. **Check Project Settings:**
   - User authentication settings: Read and write permissions
   - App type: Web App
   - Callback URL: `http://localhost/`
   - Website URL: `http://example.com/`

### 📖 Tweet Retrieval Issues

**Dual Authentication Benefits:**
- OAuth 2.0 for read operations (more stable)
- OAuth 1.0a for write operations (required)
- Automatic fallback handling

**Common Errors and Solutions:**

| Error Code | Cause | Solution |
|------------|-------|----------|
| 401 | Authentication failed | Check API credentials, regenerate tokens |
| 403 | Insufficient permissions | Upgrade API plan or check permission settings |
| 404 | Tweet not found | Verify tweet ID, check if tweet is public |
| 429 | Rate limit exceeded | Wait 15 minutes or upgrade API plan |

**API Plan Limitations:**
- **Free Users**: Basic functionality with limitations
- **Basic ($100/month)**: Full read functionality
- **Pro ($5000/month)**: Advanced features and higher limits

### 🔍 Detailed Diagnostic Steps

1. **Check Authentication Status:**
   ```
   test api connection
   ```

2. **Verify Configuration:**
   - Confirm all environment variables are set
   - Check paths are correct
   - Validate API key formats

3. **Test Specific Functions:**
   ```
   search for tweets containing "hello"
   get tweet 1234567890 content
   ```

4. **Review Detailed Logs:**
   - Check Claude Desktop console
   - Review MCP server logs
   - Note specific error messages

## Credits

This project is based on the excellent work by [Vidhu Panhavoor Vasudevan](https://github.com/vidhupv) in the original [x-mcp](https://github.com/vidhupv/x-mcp) repository. 

### What's New in This Fork
- 🆕 **Scheduled Tweets System** - Schedule single tweets, threads, and recurring tweets with flexible timing
- 🆕 **OAuth Dual Authentication System** - Support for OAuth 1.0a + OAuth 2.0, automatic selection of best authentication method
- 🆕 **401 Error Fix** - Resolved authentication issues when retrieving tweets
- 🆕 **Smart Client Selection** - Read operations prefer OAuth 2.0, write operations use OAuth 1.0a
- 🆕 **Enhanced Error Handling** - Detailed error diagnostics and English error messages
- 🆕 **API Connection Testing Tool** - Built-in connection testing and diagnostic functionality
- ✅ **Reply to tweets functionality** - Create draft replies and reply directly to existing tweets
- ✅ **Retweet functionality** - Simple retweets and quote tweets with comments
- ✅ **Media functionality** - Upload images, videos, GIFs with alt text support
- ✅ **Tweet retrieval functionality** - Get tweet content, search tweets, batch retrieve multiple tweets
- ✅ **Enhanced draft management** - Improved draft preservation on publish failure, support for all draft types

Special thanks to the original author for creating the foundation of this MCP server!

## Detailed Documentation

For more detailed functionality descriptions and usage guides, please refer to:
- **[Scheduled Tweets Functionality](SCHEDULED_TWEETS_FUNCTIONALITY.md)** - 🆕 Complete guide to scheduled tweets feature
- **[定时发推文功能说明](定时发推文功能说明.md)** - 🆕 Chinese version of scheduled tweets guide
- **[OAuth Dual Authentication Setup Guide](OAuth_Dual_Authentication_Setup_Guide.md)** - 🆕 Detailed dual authentication setup guide
- [OAuth双重认证配置指南](OAuth双重认证配置指南.md) - Chinese version of the setup guide
- [推文获取功能故障排除指南](推文获取功能故障排除指南.md) - Chinese troubleshooting guide
- [REPLY_FUNCTIONALITY.md](REPLY_FUNCTIONALITY.md) - Detailed reply functionality documentation