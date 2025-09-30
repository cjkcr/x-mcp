# Auto-Delete Failed Drafts Feature

## Overview

When tweet publishing fails, the system can automatically delete the related draft files to avoid accumulating invalid drafts. This feature is configurable, allowing users to enable or disable it as needed.

## Features

### ✅ Supported Operation Types
- Single tweet publishing failure
- Tweet thread publishing failure (including partial success scenarios)
- Reply tweet publishing failure
- Quote tweet publishing failure
- Tweet with media publishing failure

### ✅ Error Handling Scenarios
- Twitter API errors (network issues, API limits, etc.)
- Missing or corrupted media files
- Tweet content format errors
- Authentication failures
- Other system errors

## Configuration Options

### Default Behavior
- **Default State**: Enabled (`AUTO_DELETE_FAILED_DRAFTS=true`)
- **When Enabled**: Automatically delete drafts after publishing failure
- **When Disabled**: Preserve drafts after publishing failure, allowing manual retry

### Configuration Methods

#### Method 1: Environment Variable Configuration
Add the environment variable in your configuration file:

```json
{
  "env": {
    "AUTO_DELETE_FAILED_DRAFTS": "true"  // Enable auto-delete
    // or
    "AUTO_DELETE_FAILED_DRAFTS": "false" // Disable auto-delete
  }
}
```

#### Method 2: Runtime Configuration
Use the following commands to configure dynamically:

```
Enable auto-delete failed drafts
```

```
Disable auto-delete failed drafts
```

#### Method 3: Check Current Configuration
```
Check current auto-delete configuration
```

## Use Cases

### Recommended to Enable
- Frequent tweet creation and publishing
- Want to keep draft folder clean
- Don't need to manually retry failed tweets
- Automated tweet publishing workflows

### Recommended to Disable
- Need to analyze publishing failure reasons
- Want to manually modify and retry failed tweets
- Debugging tweet publishing issues
- Important tweets that must be published successfully

## Behavior Details

### When Auto-Delete is Enabled
1. Attempt to publish draft
2. If publishing fails, automatically delete draft file
3. Return error message indicating "draft has been deleted"
4. Log deletion operation

### When Auto-Delete is Disabled
1. Attempt to publish draft
2. If publishing fails, preserve draft file
3. Return error message indicating "draft preserved for retry"
4. User can retry publishing later

### Special Case: Partial Thread Publishing
When thread publishing partially succeeds:
- **Auto-delete enabled**: Delete draft, log published tweet IDs
- **Auto-delete disabled**: Preserve draft, log published tweet IDs
- In both cases, display successfully published tweet IDs in error message

## Logging

The system logs the following operations:
- Draft deletion operations (success/failure)
- Configuration change operations
- Detailed error information for publishing failures

## Troubleshooting

### Common Issues

**Q: Configuration changes don't take effect?**
A: Ensure you restart the MCP server, or use runtime configuration commands.

**Q: What if draft deletion fails?**
A: Check file permissions, ensure the program has permission to delete draft files.

**Q: How to recover automatically deleted drafts?**
A: Automatically deleted drafts cannot be recovered. If you need to preserve failed drafts, disable the auto-delete feature.

**Q: Thread partially published and draft deleted, how to continue?**
A: Check the published tweet IDs in the error message, you can manually create new tweets to continue the thread.

## Best Practices

1. **Test Environment**: Recommend disabling auto-delete during testing for easier debugging
2. **Production Environment**: Can enable auto-delete in stable production environments
3. **Important Tweets**: For important tweets, recommend disabling auto-delete first, then enable after successful publishing
4. **Regular Cleanup**: Regularly check draft folder and clean up unnecessary drafts

## Technical Implementation

### Configuration Persistence
- Runtime configuration automatically updates `.env` file (if it exists)
- Configuration changes take effect immediately without restart

### Error Handling Priority
1. Attempt to publish draft
2. Catch publishing errors
3. Decide whether to delete draft based on configuration
4. Log operations
5. Return detailed error information

### Security Considerations
- Deletion operations have exception handling to avoid program crashes
- Deletion failures are logged
- Will not delete non-draft files