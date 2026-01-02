# Scheduled Tweets Functionality

## Overview

The new scheduled tweets functionality allows you to:
1. **Schedule single tweets** - Automatically publish a tweet at a specific time
2. **Schedule tweet threads** - Automatically publish a complete tweet thread at a specific time  
3. **Create recurring tweets** - Automatically publish multiple tweets at regular intervals

## 🚀 Auto-Publishing Features

- **True Auto-Publishing**: Not drafts - tweets are actually published to Twitter at the scheduled time
- **Background Auto-Execution**: Scheduler automatically starts when you create scheduled tweets
- **No Manual Intervention**: Once set up, the system handles all publishing automatically
- **Smart Error Handling**: Failed publications are automatically logged and moved to failed directory
- **Concurrent Creation Safe**: Supports AI rapid batch creation, each tweet has unique ID to prevent file overwrites

## Features

- Support for multiple time formats (absolute and relative)
- Automatic background execution
- View and cancel scheduled tweets anytime
- Support for recurring posts, perfect for regular content
- Automatic handling of thread reply chains

## Usage

### 1. Create Scheduled Tweet

```json
{
  "tool": "create_scheduled_tweet",
  "arguments": {
    "content": "This is a scheduled tweet!",
    "scheduled_time": "2024-01-15T14:30:00"
  }
}
```

**Time Format Support:**
- Absolute time: `2024-01-15T14:30:00` or `2024-01-15T14:30`
- Relative time:
  - `+10m` - 10 minutes from now
  - `+2h` - 2 hours from now
  - `+1d` - 1 day from now

### 2. Create Scheduled Thread

```json
{
  "tool": "create_scheduled_thread",
  "arguments": {
    "contents": [
      "This is the first tweet in the thread 1/3",
      "This is the second tweet in the thread 2/3",
      "This is the third tweet in the thread 3/3"
    ],
    "scheduled_time": "+1h"
  }
}
```

### 3. Create Recurring Tweets

```json
{
  "tool": "create_recurring_tweets",
  "arguments": {
    "contents": [
      "Daily reminder: Stay hydrated! 💧",
      "Daily reminder: Take breaks! 😴", 
      "Daily reminder: Exercise! 🏃‍♂️"
    ],
    "interval_minutes": 10,
    "start_time": "+5m",
    "total_count": 6
  }
}
```

**Parameters:**
- `contents`: Array of tweet content, will be used cyclically
- `interval_minutes`: Publishing interval in minutes
- `start_time`: Start time
- `total_count`: Total number of tweets to publish (optional, defaults to contents array length)

### 4. Manage Scheduled Tweets

#### List All Scheduled Tweets
```json
{
  "tool": "list_scheduled_tweets",
  "arguments": {}
}
```

#### Cancel Scheduled Tweet
```json
{
  "tool": "cancel_scheduled_tweet",
  "arguments": {
    "schedule_id": "scheduled_tweet_1704567890.json"
  }
}
```

### 5. Control Scheduler

#### Check Scheduler Status
```json
{
  "tool": "get_scheduler_status",
  "arguments": {}
}
```

#### Start Scheduler (Usually not needed - auto-starts)
```json
{
  "tool": "start_scheduler",
  "arguments": {}
}
```

#### Stop Scheduler
```json
{
  "tool": "stop_scheduler",
  "arguments": {}
}
```

**Note**: The scheduler automatically starts when you create scheduled tweets, so manual starting is usually not required.

## Usage Examples

### Example 1: Post every 10 minutes, 5 tweets total

```json
{
  "tool": "create_recurring_tweets",
  "arguments": {
    "contents": [
      "Product update #1: New features coming soon!",
      "Product update #2: Major UX improvements!",
      "Product update #3: Performance optimization complete!",
      "Product update #4: Enhanced security features!",
      "Product update #5: Thank you for your support!"
    ],
    "interval_minutes": 10,
    "start_time": "+5m",
    "total_count": 5
  }
}
```

### Example 2: Schedule thread for tomorrow 9 AM

```json
{
  "tool": "create_scheduled_thread",
  "arguments": {
    "contents": [
      "🌅 Good morning! Today's plan:",
      "📝 1. Complete project documentation",
      "💻 2. Code review",
      "🤝 3. Team meeting",
      "🎯 Let's make it happen!"
    ],
    "scheduled_time": "2024-01-16T09:00:00"
  }
}
```

### Example 3: Single tweet in 1 hour

```json
{
  "tool": "create_scheduled_tweet",
  "arguments": {
    "content": "Just completed an important feature! 🎉 #coding #achievement",
    "scheduled_time": "+1h"
  }
}
```

## Important Notes

1. **Auto-Publishing**: This is true auto-publishing functionality - not drafts! Tweets will be actually published to Twitter at the scheduled time
2. **Auto-Start Scheduler**: The scheduler automatically starts when you create scheduled tweets - no manual action needed
3. **Time Format**: Use correct time format, time must be in the future
4. **Network**: Ensure stable network connection during operation
5. **API Limits**: Be aware of Twitter API rate limits
6. **File Storage**: Scheduled tweet info is stored in `scheduled/` directory
7. **Error Handling**: Failed tweets are moved to `scheduled/failed/` directory

## File Structure

```
Project Root/
├── scheduled/           # Pending scheduled tweets
│   ├── scheduled_tweet_*.json
│   ├── scheduled_thread_*.json
│   ├── recurring_tweets_*.json
│   └── failed/         # Failed tweets
└── drafts/             # Draft tweets (existing functionality)
```

## Status Descriptions

- `ready_to_publish`: Ready to publish, waiting for execution
- `publishing_in_X_minutes`: Will publish in X minutes
- `scheduled_for_YYYY-MM-DD_HH:MM`: Scheduled for specific time

This functionality helps you better plan and manage your Twitter content publishing strategy!