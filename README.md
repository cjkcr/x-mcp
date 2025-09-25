# X(Twitter) MCP Server

[![smithery badge](https://smithery.ai/badge/x-mcp)](https://smithery.ai/server/x-mcp)

**English** | [中文](README_CN.md)

An MCP server to create, manage and publish X/Twitter posts directly through Claude code and Gemini CLI chat.

> **Note:** This project is modified from [vidhupv/x-mcp](https://github.com/vidhupv/x-mcp), with added reply functionality for tweets.

## Features

- ✅ Create draft tweets
- ✅ Create draft tweet threads
- ✅ Create draft replies to existing tweets
- ✅ List all drafts
- ✅ Publish drafts (tweets, threads, and replies)
- ✅ Reply to tweets directly (without creating drafts)
- ✅ Retweet existing tweets
- ✅ Quote tweet with comments
- ✅ Create draft quote tweets
- ✅ Upload media files (images, videos, GIFs)
- ✅ Create tweets with media attachments
- ✅ Add alt text for accessibility
- ✅ Get media file information
- ✅ Get tweet content and information
- ✅ Search recent tweets (last 7 days)
- ✅ Batch retrieve multiple tweets
- ✅ Delete drafts
- ✅ Draft preservation on publish failure

<a href="https://glama.ai/mcp/servers/jsxr09dktf">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/jsxr09dktf/badge" alt="X(Twitter) Server MCP server" />
</a>

## Quick Setup

### Installing via Smithery

To install X(Twitter) MCP Server for Claude code automatically via [Smithery](https://smithery.ai/server/x-mcp):

```bash
npx -y @smithery/cli install x-mcp --client claude
```

### Manual Installation for Claude code

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/x-mcp.git
```

2. **Install UV globally using Homebrew in Terminal:**
```bash
brew install uv
```

3. **Create claude_desktop_config.json:**
   - **For MacOS:** Open directory `~/Library/Application Support/Claude/` and create the file inside it
   - **For Windows:** Open directory `%APPDATA%/Claude/` and create the file inside it

4. **Add this configuration to claude_desktop_config.json:**
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

5. **Get your X/Twitter API credentials:**
   - Go to [X API Developer Portal](https://developer.x.com/en/products/x-api)
   - Create a project
   - In User Authentication Settings: Set up with Read and Write permissions, Web App type
   - Set Callback URL to `http://localhost/` and Website URL to `http://example.com/`
   - Generate and copy all keys and tokens from Keys and Tokens section

6. **Update the config file:**
   - Replace `/path/to/x-mcp` with your actual repository path
   - Add your X/Twitter API credentials

7. **Quit Claude completely and reopen it**

### Configuration for Gemini CLI

If you want to use this MCP server with Gemini CLI instead of Claude code:

1. **Install Gemini CLI:**
```bash
npm install -g @google/gemini-cli
```

2. **Create or update your MCP configuration file:**
   - Create a file named `~/.gemini/settings.json`
   - Add the following configuration:

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

3. **Start Gemini CLI with MCP support:**
```bash
Restart gemini cli
```

4. **Update the config file:**
   - Replace `/path/to/x-mcp` with your actual repository path
   - Add your X/Twitter API credentials

## Usage Examples

Works with both Claude code and Gemini CLI:

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
* "Upload image /path/to/image.jpg with alt text 'Beautiful sunset over the mountains'"
* "Create tweet with media 'Check out this amazing photo!' using media IDs 123456789"
* "Create draft tweet with media 'My latest project' and attach /path/to/video.mp4"
* "Get tweet 1234567890 content and information"
* "Search for tweets containing 'AI OR artificial intelligence' from the last 7 days"
* "Get information for tweets 123456789, 987654321, 555666777"

## Troubleshooting

If not working:
- Make sure UV is installed globally (if not, uninstall with `pip uninstall uv` and reinstall with `brew install uv`)
- Or find UV path with `which uv` and replace `"command": "uv"` with the full path
- Verify all X/Twitter credentials are correct
- Check if the x-mcp path in config matches your actual repository location

## Credits

This project is based on the excellent work by [Vidhu Panhavoor Vasudevan](https://github.com/vidhupv) in the original [x-mcp](https://github.com/vidhupv/x-mcp) repository. 

### What's New in This Fork
- ✅ **Reply to tweets functionality** - Create draft replies and reply directly to existing tweets
- ✅ **Retweet functionality** - Simple retweets and quote tweets with comments
- ✅ **Media functionality** - Upload images, videos, GIFs with alt text support
- ✅ **Tweet retrieval functionality** - Get tweet content, search tweets, batch retrieve multiple tweets
- ✅ **Enhanced draft management** - Improved draft preservation on publish failure, support for all draft types
- ✅ **Better error handling** - More detailed error messages and recovery options

Special thanks to the original author for creating the foundation of this MCP server!