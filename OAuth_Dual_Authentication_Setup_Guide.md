# Twitter API OAuth Dual Authentication Setup Guide

## Overview

To resolve Twitter API 401 Unauthorized errors and provide more stable service, we now support OAuth 1.0a and OAuth 2.0 dual authentication:

- **OAuth 1.0a**: For write operations (posting tweets, retweeting, replying, etc.)
- **OAuth 2.0**: For read operations (getting tweets, searching, etc.), typically more stable

## Setup Steps

### 1. Get OAuth 1.0a Credentials (Required)

In the [Twitter Developer Portal](https://developer.x.com/):

1. Create or select your project
2. Generate the following credentials:
   - `API Key` (Consumer Key)
   - `API Secret` (Consumer Secret)
   - `Access Token`
   - `Access Token Secret`

### 2. Get OAuth 2.0 Bearer Token (Recommended)

In the same project:

1. Go to project settings
2. Find the "Bearer Token" section
3. Generate Bearer Token

### 3. Configure Environment Variables

#### Method 1: Set in Claude Desktop Configuration

Edit your `claude_desktop_config.json`:

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

#### Method 2: Use .env File

Create a `.env` file in the project root:

```bash
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token
```

## Permission Settings

### Twitter Developer Portal Settings

1. **Project Type**: Choose appropriate project type
2. **User Authentication Settings**:
   - App permissions: `Read and write`
   - App type: `Web App`
   - Callback URL: `http://localhost/`
   - Website URL: `http://example.com/`

### API Access Levels

- **Free Users**: Basic functionality with limitations
- **Paid Users**: Full functionality with higher limits

## Test Configuration

### Using Test Script

```bash
cd /path/to/x-mcp
python test_tweet_functions.py
```

### Test in Claude

```
test api connection
```

## Troubleshooting

### Common Errors and Solutions

#### 401 Unauthorized
- **Cause**: Invalid or expired API credentials
- **Solution**: Regenerate API keys and tokens

#### 403 Forbidden
- **Cause**: Insufficient permissions or feature requires paid plan
- **Solution**: Check permission settings or upgrade API plan

#### 429 Rate Limit Exceeded
- **Cause**: API call frequency exceeded
- **Solution**: Wait for limit reset or upgrade plan

### Configuration Validation Checklist

- [ ] OAuth 1.0a credentials set and valid
- [ ] OAuth 2.0 Bearer Token set (recommended)
- [ ] Twitter project permissions set to "Read and write"
- [ ] API keys not expired
- [ ] Network connection normal

## Comparison of Advantages

### OAuth 1.0a Only Configuration
- ✅ Supports all write operations
- ✅ Supports read operations
- ⚠️ Read operations may be less stable
- ⚠️ More prone to permission issues

### OAuth 1.0a + OAuth 2.0 Configuration (Recommended)
- ✅ Supports all write operations
- ✅ More stable read operations
- ✅ Automatic selection of best authentication method
- ✅ Better error handling
- ✅ Higher success rate

## System Behavior

### Automatic Client Selection

The system automatically selects the best client:

1. **Read Operations**: Prefer OAuth 2.0, fallback to OAuth 1.0a
2. **Write Operations**: Always use OAuth 1.0a

### Error Handling

- Provides detailed error information and suggestions
- Automatic retry mechanism
- Intelligent degradation handling

## Monitoring and Maintenance

### Regular Checks

1. **API Usage**: Check in Twitter Developer Portal
2. **Error Logs**: Review application logs
3. **Permission Status**: Ensure permissions haven't been revoked

### Update Credentials

When credentials need updating:

1. Generate new credentials in Twitter Developer Portal
2. Update configuration files
3. Restart MCP server
4. Run tests to verify

## Support

If you encounter issues:

1. Run test script to diagnose problems
2. Check Twitter Developer Portal settings
3. Review detailed error logs
4. Refer to troubleshooting guide

Remember: Twitter API policies and limitations change frequently, so it's recommended to regularly check official documentation and update configurations.

## Configuration Examples

### Basic Configuration (OAuth 1.0a Only)
```json
{
  "env": {
    "TWITTER_API_KEY": "your_api_key",
    "TWITTER_API_SECRET": "your_api_secret",
    "TWITTER_ACCESS_TOKEN": "your_access_token",
    "TWITTER_ACCESS_TOKEN_SECRET": "your_access_token_secret"
  }
}
```

### Recommended Configuration (Dual Authentication)
```json
{
  "env": {
    "TWITTER_API_KEY": "your_api_key",
    "TWITTER_API_SECRET": "your_api_secret",
    "TWITTER_ACCESS_TOKEN": "your_access_token",
    "TWITTER_ACCESS_TOKEN_SECRET": "your_access_token_secret",
    "TWITTER_BEARER_TOKEN": "your_bearer_token"
  }
}
```

## Testing Commands

### In Claude Desktop
```
test api connection
search for tweets containing "AI"
get tweet 1234567890 content
get tweets 123456789, 987654321 information
```

### Using Test Script
```bash
# Run comprehensive test
python test_tweet_functions.py

# Check specific functionality
python -c "
import os
from test_tweet_functions import *
load_dotenv()
if test_credentials():
    oauth1 = test_oauth1_connection()
    oauth2 = test_oauth2_connection()
    print(f'OAuth 1.0a: {\"✅\" if oauth1 else \"❌\"}')
    print(f'OAuth 2.0: {\"✅\" if oauth2 else \"❌\"}')
"
```

## Migration from Single Authentication

If you're upgrading from OAuth 1.0a only:

1. **Backup existing configuration**
2. **Add Bearer Token to configuration**
3. **Restart Claude Desktop**
4. **Test functionality**
5. **Verify improved stability**

The system is backward compatible - existing OAuth 1.0a configurations will continue to work while benefiting from improved error handling and diagnostics.