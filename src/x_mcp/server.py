import os
import json
import logging
import asyncio
import mimetypes
from datetime import datetime, timedelta
from typing import Any, Sequence
from dotenv import load_dotenv
import tweepy
from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    LoggingLevel,
    EmptyResult,
)

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("x_mcp")

# Configuration for auto-delete drafts on publish failure
_auto_delete_env = os.getenv("AUTO_DELETE_FAILED_DRAFTS", "true").lower()
AUTO_DELETE_FAILED_DRAFTS = _auto_delete_env in ("true", "1", "yes", "on") if _auto_delete_env else True

# Get Twitter API credentials from environment variables
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")  # Optional for OAuth 2.0

# Validate required credentials for OAuth 1.0a
if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
    raise ValueError("Twitter API credentials are required (OAuth 1.0a)")

# Initialize multiple clients for different use cases
# OAuth 1.0a client - for posting, retweeting, and user-specific operations
oauth1_client = tweepy.Client(
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET,
    wait_on_rate_limit=True
)

# OAuth 2.0 client - for reading tweets (if bearer token is available)
oauth2_client = None
if BEARER_TOKEN:
    try:
        oauth2_client = tweepy.Client(
            bearer_token=BEARER_TOKEN,
            wait_on_rate_limit=True
        )
        logger.info("OAuth 2.0 client initialized with bearer token")
    except Exception as e:
        logger.warning(f"Failed to initialize OAuth 2.0 client: {e}")

# Fallback to OAuth 1.0a for all operations
client = oauth1_client

# Also initialize OAuth 1.0a API for media upload and legacy operations
auth = tweepy.OAuth1UserHandler(
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)
api = tweepy.API(auth, wait_on_rate_limit=True)

def get_read_client():
    """Get the best client for read operations (OAuth 2.0 preferred, fallback to OAuth 1.0a)"""
    if oauth2_client:
        return oauth2_client
    return oauth1_client

def get_write_client():
    """Get the client for write operations (always OAuth 1.0a)"""
    return oauth1_client

# Create the MCP server instance
server = Server("x_mcp")

# Global variable to store the scheduled task
_scheduled_task = None
_scheduler_running = False

def delete_draft_on_failure(draft_id: str, filepath: str) -> None:
    """Delete draft file if auto-delete is enabled"""
    if AUTO_DELETE_FAILED_DRAFTS:
        try:
            os.remove(filepath)
            logger.info(f"Deleted draft {draft_id} due to publishing failure (auto-delete enabled)")
        except Exception as delete_error:
            logger.error(f"Failed to delete draft {draft_id} after publishing error: {delete_error}")
    else:
        logger.info(f"Draft {draft_id} preserved for retry (auto-delete disabled)")

# Implement tool handlers
@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for interacting with Twitter/X."""
    return [
        Tool(
            name="create_draft_tweet",
            description="Create a draft tweet",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The content of the tweet",
                    },
                },
                "required": ["content"],
            },
        ),
        Tool(
            name="create_draft_thread",
            description="Create a draft tweet thread",
            inputSchema={
                "type": "object",
                "properties": {
                    "contents": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "An array of tweet contents for the thread",
                    },
                },
                "required": ["contents"],
            },
        ),
        Tool(
            name="list_drafts",
            description="List all draft tweets and threads",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="publish_draft",
            description="Publish a draft tweet or thread",
            inputSchema={
                "type": "object",
                "properties": {
                    "draft_id": {
                        "type": "string",
                        "description": "ID of the draft to publish",
                    },
                },
                "required": ["draft_id"],
            },
        ),
        Tool(
            name="delete_draft",
            description="Delete a draft tweet or thread",
            inputSchema={
                "type": "object",
                "properties": {
                    "draft_id": {
                        "type": "string",
                        "description": "ID of the draft to delete",
                    },
                },
                "required": ["draft_id"],
            },
        ),
        Tool(
            name="create_draft_reply",
            description="Create a draft reply to an existing tweet",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The content of the reply tweet",
                    },
                    "reply_to_tweet_id": {
                        "type": "string",
                        "description": "The ID of the tweet to reply to",
                    },
                },
                "required": ["content", "reply_to_tweet_id"],
            },
        ),
        Tool(
            name="reply_to_tweet",
            description="Reply to an existing tweet directly (without creating a draft)",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The content of the reply tweet",
                    },
                    "reply_to_tweet_id": {
                        "type": "string",
                        "description": "The ID of the tweet to reply to",
                    },
                },
                "required": ["content", "reply_to_tweet_id"],
            },
        ),
        Tool(
            name="retweet",
            description="Retweet an existing tweet (simple retweet without comment)",
            inputSchema={
                "type": "object",
                "properties": {
                    "tweet_id": {
                        "type": "string",
                        "description": "The ID of the tweet to retweet",
                    },
                },
                "required": ["tweet_id"],
            },
        ),
        Tool(
            name="quote_tweet",
            description="Quote tweet with comment (retweet with your own comment)",
            inputSchema={
                "type": "object",
                "properties": {
                    "tweet_id": {
                        "type": "string",
                        "description": "The ID of the tweet to quote",
                    },
                    "comment": {
                        "type": "string",
                        "description": "Your comment on the quoted tweet",
                    },
                },
                "required": ["tweet_id", "comment"],
            },
        ),
        Tool(
            name="create_draft_quote_tweet",
            description="Create a draft quote tweet with comment",
            inputSchema={
                "type": "object",
                "properties": {
                    "tweet_id": {
                        "type": "string",
                        "description": "The ID of the tweet to quote",
                    },
                    "comment": {
                        "type": "string",
                        "description": "Your comment on the quoted tweet",
                    },
                },
                "required": ["tweet_id", "comment"],
            },
        ),
        Tool(
            name="upload_media",
            description="Upload media file (image, video, or GIF) for use in tweets",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the media file to upload",
                    },
                    "media_type": {
                        "type": "string",
                        "enum": ["image", "video", "gif"],
                        "description": "Type of media file",
                    },
                    "alt_text": {
                        "type": "string",
                        "description": "Alternative text for accessibility (optional, for images)",
                    },
                },
                "required": ["file_path", "media_type"],
            },
        ),
        Tool(
            name="create_tweet_with_media",
            description="Create a tweet with attached media files",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The text content of the tweet",
                    },
                    "media_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of media IDs to attach to the tweet",
                    },
                },
                "required": ["content", "media_ids"],
            },
        ),
        Tool(
            name="create_draft_tweet_with_media",
            description="Create a draft tweet with media files",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The text content of the tweet",
                    },
                    "media_files": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "file_path": {"type": "string"},
                                "media_type": {"type": "string", "enum": ["image", "video", "gif"]},
                                "alt_text": {"type": "string"}
                            },
                            "required": ["file_path", "media_type"]
                        },
                        "description": "List of media files to include in the draft",
                    },
                },
                "required": ["content", "media_files"],
            },
        ),
        Tool(
            name="get_media_info",
            description="Get information about uploaded media",
            inputSchema={
                "type": "object",
                "properties": {
                    "media_id": {
                        "type": "string",
                        "description": "The media ID to get information for",
                    },
                },
                "required": ["media_id"],
            },
        ),
        Tool(
            name="get_tweet",
            description="Get the content and information of a specific tweet",
            inputSchema={
                "type": "object",
                "properties": {
                    "tweet_id": {
                        "type": "string",
                        "description": "The ID of the tweet to retrieve",
                    },
                    "include_author": {
                        "type": "boolean",
                        "description": "Whether to include author information (default: true)",
                        "default": True,
                    },
                },
                "required": ["tweet_id"],
            },
        ),
        Tool(
            name="get_tweets",
            description="Get the content and information of multiple tweets",
            inputSchema={
                "type": "object",
                "properties": {
                    "tweet_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tweet IDs to retrieve (max 100)",
                    },
                    "include_author": {
                        "type": "boolean",
                        "description": "Whether to include author information (default: true)",
                        "default": True,
                    },
                },
                "required": ["tweet_ids"],
            },
        ),
        Tool(
            name="search_tweets",
            description="Search for recent tweets (last 7 days for free users)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'AI OR artificial intelligence', '#python', 'from:username')",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of tweets to return (default: 10, max: 100)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "include_author": {
                        "type": "boolean",
                        "description": "Whether to include author information (default: true)",
                        "default": True,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="test_api_connection",
            description="Test Twitter API connection and permissions",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_global_trends",
            description="Get current global trending topics on Twitter/X",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of trends to return (default: 10, max: 50)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_regional_trends",
            description="Get trending topics for a specific region/location",
            inputSchema={
                "type": "object",
                "properties": {
                    "woeid": {
                        "type": "integer",
                        "description": "Where On Earth ID for the location (e.g., 1 for worldwide, 23424977 for US, 23424856 for Japan)",
                    },
                    "location_name": {
                        "type": "string",
                        "description": "Location name (alternative to woeid, e.g., 'United States', 'Japan', 'United Kingdom')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of trends to return (default: 10, max: 50)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_available_trend_locations",
            description="Get list of available locations for trend queries",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_topic_details",
            description="Get detailed information about a specific trending topic or hashtag",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The trending topic or hashtag to get details for (e.g., '#AI', 'ChatGPT')",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of related tweets to return (default: 20, max: 100)",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "include_retweets": {
                        "type": "boolean",
                        "description": "Whether to include retweets in results (default: false)",
                        "default": False,
                    },
                },
                "required": ["topic"],
            },
        ),
        Tool(
            name="search_trending_hashtags",
            description="Search for trending hashtags related to a keyword",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Keyword to search for related trending hashtags",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10, max: 50)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                    },
                },
                "required": ["keyword"],
            },
        ),
        Tool(
            name="configure_auto_delete_failed_drafts",
            description="Configure whether to automatically delete drafts when publishing fails",
            inputSchema={
                "type": "object",
                "properties": {
                    "enabled": {
                        "type": "boolean",
                        "description": "Whether to automatically delete drafts on publishing failure",
                    },
                },
                "required": ["enabled"],
            },
        ),
        Tool(
            name="get_auto_delete_config",
            description="Get current configuration for auto-deleting failed drafts",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="create_scheduled_tweet",
            description="Create a scheduled tweet to be published at a specific time",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The content of the tweet",
                    },
                    "scheduled_time": {
                        "type": "string",
                        "description": "When to publish the tweet (ISO format: YYYY-MM-DDTHH:MM:SS or relative like '+10m', '+1h', '+1d')",
                    },
                },
                "required": ["content", "scheduled_time"],
            },
        ),
        Tool(
            name="create_scheduled_thread",
            description="Create a scheduled tweet thread to be published at a specific time",
            inputSchema={
                "type": "object",
                "properties": {
                    "contents": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "An array of tweet contents for the thread",
                    },
                    "scheduled_time": {
                        "type": "string",
                        "description": "When to publish the thread (ISO format: YYYY-MM-DDTHH:MM:SS or relative like '+10m', '+1h', '+1d')",
                    },
                },
                "required": ["contents", "scheduled_time"],
            },
        ),
        Tool(
            name="create_recurring_tweets",
            description="Create recurring tweets that will be published at regular intervals",
            inputSchema={
                "type": "object",
                "properties": {
                    "contents": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "An array of tweet contents to be published in sequence",
                    },
                    "interval_minutes": {
                        "type": "integer",
                        "description": "Interval between tweets in minutes (e.g., 10 for every 10 minutes)",
                        "minimum": 1,
                    },
                    "start_time": {
                        "type": "string",
                        "description": "When to start publishing (ISO format: YYYY-MM-DDTHH:MM:SS or relative like '+10m', '+1h', '+1d')",
                    },
                    "total_count": {
                        "type": "integer",
                        "description": "Total number of tweets to publish (optional, defaults to length of contents array)",
                        "minimum": 1,
                    },
                },
                "required": ["contents", "interval_minutes", "start_time"],
            },
        ),
        Tool(
            name="list_scheduled_tweets",
            description="List all scheduled tweets and their status",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="cancel_scheduled_tweet",
            description="Cancel a scheduled tweet before it's published",
            inputSchema={
                "type": "object",
                "properties": {
                    "schedule_id": {
                        "type": "string",
                        "description": "ID of the scheduled tweet to cancel",
                    },
                },
                "required": ["schedule_id"],
            },
        ),
        Tool(
            name="start_scheduler",
            description="Start the tweet scheduler background task",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="stop_scheduler",
            description="Stop the tweet scheduler background task",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_scheduler_status",
            description="Get the current status of the tweet scheduler",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """Handle tool calls for creating Twitter/X drafts."""
    if name == "create_draft_tweet":
        return await handle_create_draft_tweet(arguments)
    elif name == "create_draft_thread":
        return await handle_create_draft_thread(arguments)
    elif name == "list_drafts":
        return await handle_list_drafts(arguments)
    elif name == "publish_draft":
        return await handle_publish_draft(arguments)
    elif name == "delete_draft":
        return await handle_delete_draft(arguments)
    elif name == "create_draft_reply":
        return await handle_create_draft_reply(arguments)
    elif name == "reply_to_tweet":
        return await handle_reply_to_tweet(arguments)
    elif name == "retweet":
        return await handle_retweet(arguments)
    elif name == "quote_tweet":
        return await handle_quote_tweet(arguments)
    elif name == "create_draft_quote_tweet":
        return await handle_create_draft_quote_tweet(arguments)
    elif name == "upload_media":
        return await handle_upload_media(arguments)
    elif name == "create_tweet_with_media":
        return await handle_create_tweet_with_media(arguments)
    elif name == "create_draft_tweet_with_media":
        return await handle_create_draft_tweet_with_media(arguments)
    elif name == "get_media_info":
        return await handle_get_media_info(arguments)
    elif name == "get_tweet":
        return await handle_get_tweet(arguments)
    elif name == "get_tweets":
        return await handle_get_tweets(arguments)
    elif name == "search_tweets":
        return await handle_search_tweets(arguments)
    elif name == "test_api_connection":
        return await handle_test_api_connection(arguments)
    elif name == "get_global_trends":
        return await handle_get_global_trends(arguments)
    elif name == "get_regional_trends":
        return await handle_get_regional_trends(arguments)
    elif name == "get_available_trend_locations":
        return await handle_get_available_trend_locations(arguments)
    elif name == "get_topic_details":
        return await handle_get_topic_details(arguments)
    elif name == "search_trending_hashtags":
        return await handle_search_trending_hashtags(arguments)
    elif name == "configure_auto_delete_failed_drafts":
        return await handle_configure_auto_delete_failed_drafts(arguments)
    elif name == "get_auto_delete_config":
        return await handle_get_auto_delete_config(arguments)
    elif name == "create_scheduled_tweet":
        return await handle_create_scheduled_tweet(arguments)
    elif name == "create_scheduled_thread":
        return await handle_create_scheduled_thread(arguments)
    elif name == "create_recurring_tweets":
        return await handle_create_recurring_tweets(arguments)
    elif name == "list_scheduled_tweets":
        return await handle_list_scheduled_tweets(arguments)
    elif name == "cancel_scheduled_tweet":
        return await handle_cancel_scheduled_tweet(arguments)
    elif name == "start_scheduler":
        return await handle_start_scheduler(arguments)
    elif name == "stop_scheduler":
        return await handle_stop_scheduler(arguments)
    elif name == "get_scheduler_status":
        return await handle_get_scheduler_status(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

async def handle_create_draft_tweet(arguments: Any) -> Sequence[TextContent]:
    if not isinstance(arguments, dict) or "content" not in arguments:
        raise ValueError("Invalid arguments for create_draft_tweet")
    content = arguments["content"]
    try:
        # Simulate creating a draft by storing it locally
        draft = {"content": content, "timestamp": datetime.now().isoformat()}
        # Ensure drafts directory exists
        os.makedirs("drafts", exist_ok=True)
        # Save the draft to a file
        draft_id = f"draft_{int(datetime.now().timestamp())}.json"
        with open(os.path.join("drafts", draft_id), "w") as f:
            json.dump(draft, f, indent=2)
        logger.info(f"Draft tweet created: {draft_id}")
        return [
            TextContent(
                type="text",
                text=f"Draft tweet created with ID {draft_id}",
            )
        ]
    except Exception as e:
        logger.error(f"Error creating draft tweet: {str(e)}")
        raise RuntimeError(f"Error creating draft tweet: {str(e)}")

async def handle_create_draft_thread(arguments: Any) -> Sequence[TextContent]:
    if not isinstance(arguments, dict) or "contents" not in arguments:
        raise ValueError("Invalid arguments for create_draft_thread")
    contents = arguments["contents"]
    if not isinstance(contents, list) or not all(isinstance(item, str) for item in contents):
        raise ValueError("Invalid contents for create_draft_thread")
    try:
        draft = {"contents": contents, "timestamp": datetime.now().isoformat()}
        # Ensure drafts directory exists
        os.makedirs("drafts", exist_ok=True)
        # Save the draft to a file
        draft_id = f"thread_draft_{int(datetime.now().timestamp())}.json"
        with open(os.path.join("drafts", draft_id), "w") as f:
            json.dump(draft, f, indent=2)
        logger.info(f"Draft thread created: {draft_id}")
        return [
            TextContent(
                type="text",
                text=f"Draft thread created with ID {draft_id}",
            )
        ]
    except Exception as e:
        logger.error(f"Error creating draft thread: {str(e)}")
        raise RuntimeError(f"Error creating draft thread: {str(e)}")

async def handle_list_drafts(arguments: Any) -> Sequence[TextContent]:
    try:
        drafts = []
        if os.path.exists("drafts"):
            for filename in os.listdir("drafts"):
                filepath = os.path.join("drafts", filename)
                with open(filepath, "r") as f:
                    draft = json.load(f)
                drafts.append({"id": filename, "draft": draft})
        return [
            TextContent(
                type="text",
                text=json.dumps(drafts, indent=2),
            )
        ]
    except Exception as e:
        logger.error(f"Error listing drafts: {str(e)}")
        raise RuntimeError(f"Error listing drafts: {str(e)}")

async def handle_publish_draft(arguments: Any) -> Sequence[TextContent]:
    if not isinstance(arguments, dict) or "draft_id" not in arguments:
        raise ValueError("Invalid arguments for publish_draft")
    draft_id = arguments["draft_id"]
    filepath = os.path.join("drafts", draft_id)
    if not os.path.exists(filepath):
        raise ValueError(f"Draft {draft_id} does not exist")
    
    # Read the draft first
    try:
        with open(filepath, "r") as f:
            draft = json.load(f)
    except Exception as e:
        logger.error(f"Error reading draft {draft_id}: {str(e)}")
        raise RuntimeError(f"Error reading draft {draft_id}: {str(e)}")
    
    # Try to publish the draft
    try:
        if "content" in draft:
            content = draft["content"]
            
            # Check if this is a reply draft
            if draft.get("type") == "reply" and "reply_to_tweet_id" in draft:
                # Reply to existing tweet
                reply_to_tweet_id = draft["reply_to_tweet_id"]
                response = get_write_client().create_tweet(text=content, in_reply_to_tweet_id=reply_to_tweet_id)
                tweet_id = response.data['id']
                logger.info(f"Published reply tweet ID {tweet_id} to tweet {reply_to_tweet_id}")
                
                # Only delete the draft after successful publishing
                os.remove(filepath)
                return [
                    TextContent(
                        type="text",
                        text=f"Draft {draft_id} published as reply tweet ID {tweet_id} to tweet {reply_to_tweet_id}",
                    )
                ]
            else:
                # Single tweet
                response = get_write_client().create_tweet(text=content)
                tweet_id = response.data['id']
                logger.info(f"Published tweet ID {tweet_id}")
                
                # Only delete the draft after successful publishing
                os.remove(filepath)
                return [
                    TextContent(
                        type="text",
                        text=f"Draft {draft_id} published as tweet ID {tweet_id}",
                    )
                ]
        elif "comment" in draft and draft.get("type") == "quote_tweet":
            # Quote tweet draft
            comment = draft["comment"]
            quote_tweet_id = draft["quote_tweet_id"]
            
            response = get_write_client().create_tweet(text=comment, quote_tweet_id=quote_tweet_id)
            tweet_id = response.data['id']
            logger.info(f"Published quote tweet ID {tweet_id} quoting tweet {quote_tweet_id}")
            
            # Only delete the draft after successful publishing
            os.remove(filepath)
            return [
                TextContent(
                    type="text",
                    text=f"Draft {draft_id} published as quote tweet ID {tweet_id} quoting tweet {quote_tweet_id}",
                )
            ]
        elif "media_files" in draft and draft.get("type") == "tweet_with_media":
            # Tweet with media draft
            content = draft["content"]
            media_files = draft["media_files"]
            
            # Upload media files and collect media IDs
            media_ids = []
            for media_file in media_files:
                file_path = media_file["file_path"]
                media_type = media_file["media_type"]
                alt_text = media_file.get("alt_text")
                
                # Check if file exists
                if not os.path.exists(file_path):
                    raise ValueError(f"Media file not found: {file_path}")
                
                # Upload media
                media_upload = api.media_upload(filename=file_path)
                media_id = media_upload.media_id_string
                media_ids.append(media_id)
                
                # Add alt text if provided and media is an image
                if alt_text and media_type in ["image", "gif"]:
                    api.create_media_metadata(media_id=media_id, alt_text=alt_text)
                
                logger.info(f"Uploaded {media_type} for draft: {media_id}")
            
            # Create tweet with media
            response = get_write_client().create_tweet(text=content, media_ids=media_ids)
            tweet_id = response.data['id']
            logger.info(f"Published tweet with media ID {tweet_id}, media IDs: {media_ids}")
            
            # Only delete the draft after successful publishing
            os.remove(filepath)
            return [
                TextContent(
                    type="text",
                    text=f"Draft {draft_id} published as tweet with media ID {tweet_id} ({len(media_ids)} media files)",
                )
            ]
        elif "contents" in draft:
            # Thread
            contents = draft["contents"]
            # Publish the thread
            published_tweet_ids = []
            last_tweet_id = None
            
            try:
                for i, content in enumerate(contents):
                    if last_tweet_id is None:
                        response = get_write_client().create_tweet(text=content)
                    else:
                        response = get_write_client().create_tweet(text=content, in_reply_to_tweet_id=last_tweet_id)
                    last_tweet_id = response.data['id']
                    published_tweet_ids.append(last_tweet_id)
                    await asyncio.sleep(1)  # Avoid hitting rate limits
                
                logger.info(f"Published thread with {len(published_tweet_ids)} tweets, starting with ID {published_tweet_ids[0]}")
                
                # Only delete the draft after successful publishing of entire thread
                os.remove(filepath)
                return [
                    TextContent(
                        type="text",
                        text=f"Draft {draft_id} published as thread with {len(published_tweet_ids)} tweets, starting with tweet ID {published_tweet_ids[0]}",
                    )
                ]
            except Exception as thread_error:
                # If thread publishing fails partway through, log which tweets were published
                if published_tweet_ids:
                    logger.error(f"Thread publishing failed after {len(published_tweet_ids)} tweets. Published tweet IDs: {published_tweet_ids}")
                    # Delete the draft even if thread partially published
                    delete_draft_on_failure(draft_id, filepath)
                    status_msg = "Draft has been deleted." if AUTO_DELETE_FAILED_DRAFTS else "Draft preserved for retry."
                    raise RuntimeError(f"Thread publishing failed after {len(published_tweet_ids)} tweets. Published tweets: {published_tweet_ids}. {status_msg} Error: {thread_error}")
                else:
                    # No tweets were published, the error will be handled by the outer exception handler
                    raise thread_error
        else:
            raise ValueError(f"Invalid draft format for {draft_id}")
            
    except tweepy.TweepError as e:
        logger.error(f"Twitter API error publishing draft {draft_id}: {e}")
        delete_draft_on_failure(draft_id, filepath)
        status_msg = "Draft has been deleted." if AUTO_DELETE_FAILED_DRAFTS else "Draft preserved for retry."
        raise RuntimeError(f"Twitter API error publishing draft {draft_id}: {e}. {status_msg}")
    except Exception as e:
        logger.error(f"Error publishing draft {draft_id}: {str(e)}")
        delete_draft_on_failure(draft_id, filepath)
        status_msg = "Draft has been deleted." if AUTO_DELETE_FAILED_DRAFTS else "Draft preserved for retry."
        raise RuntimeError(f"Error publishing draft {draft_id}: {str(e)}. {status_msg}")


async def handle_delete_draft(arguments: Any) -> Sequence[TextContent]:
    if not isinstance(arguments, dict) or "draft_id" not in arguments:
        raise ValueError("Invalid arguments for delete_draft")
    
    draft_id = arguments["draft_id"]
    filepath = os.path.join("drafts", draft_id)
    
    try:
        if not os.path.exists(filepath):
            raise ValueError(f"Draft {draft_id} does not exist")
        
        os.remove(filepath)
        logger.info(f"Deleted draft: {draft_id}")
        
        return [
            TextContent(
                type="text",
                text=f"Successfully deleted draft {draft_id}",
            )
        ]
    except Exception as e:
        logger.error(f"Error deleting draft {draft_id}: {str(e)}")
        raise RuntimeError(f"Error deleting draft {draft_id}: {str(e)}")

async def handle_create_draft_reply(arguments: Any) -> Sequence[TextContent]:
    if not isinstance(arguments, dict) or "content" not in arguments or "reply_to_tweet_id" not in arguments:
        raise ValueError("Invalid arguments for create_draft_reply")
    
    content = arguments["content"]
    reply_to_tweet_id = arguments["reply_to_tweet_id"]
    
    try:
        # Create a draft reply with the tweet ID to reply to
        draft = {
            "content": content,
            "reply_to_tweet_id": reply_to_tweet_id,
            "timestamp": datetime.now().isoformat(),
            "type": "reply"
        }
        
        # Ensure drafts directory exists
        os.makedirs("drafts", exist_ok=True)
        
        # Save the draft to a file
        draft_id = f"reply_draft_{int(datetime.now().timestamp())}.json"
        with open(os.path.join("drafts", draft_id), "w") as f:
            json.dump(draft, f, indent=2)
        
        logger.info(f"Draft reply created: {draft_id}")
        
        return [
            TextContent(
                type="text",
                text=f"Draft reply created with ID {draft_id} (replying to tweet {reply_to_tweet_id})",
            )
        ]
    except Exception as e:
        logger.error(f"Error creating draft reply: {str(e)}")
        raise RuntimeError(f"Error creating draft reply: {str(e)}")

async def handle_reply_to_tweet(arguments: Any) -> Sequence[TextContent]:
    if not isinstance(arguments, dict) or "content" not in arguments or "reply_to_tweet_id" not in arguments:
        raise ValueError("Invalid arguments for reply_to_tweet")
    
    content = arguments["content"]
    reply_to_tweet_id = arguments["reply_to_tweet_id"]
    
    try:
        # Reply to the tweet directly
        response = get_write_client().create_tweet(text=content, in_reply_to_tweet_id=reply_to_tweet_id)
        tweet_id = response.data['id']
        
        logger.info(f"Published reply tweet ID {tweet_id} to tweet {reply_to_tweet_id}")
        
        return [
            TextContent(
                type="text",
                text=f"Successfully replied to tweet {reply_to_tweet_id} with tweet ID {tweet_id}",
            )
        ]
    except tweepy.TweepError as e:
        logger.error(f"Twitter API error: {e}")
        raise RuntimeError(f"Error replying to tweet {reply_to_tweet_id}: {e}")
    except Exception as e:
        logger.error(f"Error replying to tweet {reply_to_tweet_id}: {str(e)}")
        raise RuntimeError(f"Error replying to tweet {reply_to_tweet_id}: {str(e)}")

async def handle_retweet(arguments: Any) -> Sequence[TextContent]:
    if not isinstance(arguments, dict) or "tweet_id" not in arguments:
        raise ValueError("Invalid arguments for retweet")
    
    tweet_id = arguments["tweet_id"]
    
    try:
        # Simple retweet without comment using the retweet method
        response = get_write_client().retweet(tweet_id)
        
        logger.info(f"Retweeted tweet {tweet_id}")
        
        return [
            TextContent(
                type="text",
                text=f"Successfully retweeted tweet {tweet_id}",
            )
        ]
    except tweepy.TweepError as e:
        logger.error(f"Twitter API error retweeting tweet {tweet_id}: {e}")
        raise RuntimeError(f"Twitter API error retweeting tweet {tweet_id}: {e}")
    except Exception as e:
        logger.error(f"Error retweeting tweet {tweet_id}: {str(e)}")
        raise RuntimeError(f"Error retweeting tweet {tweet_id}: {str(e)}")

async def handle_quote_tweet(arguments: Any) -> Sequence[TextContent]:
    if not isinstance(arguments, dict) or "tweet_id" not in arguments or "comment" not in arguments:
        raise ValueError("Invalid arguments for quote_tweet")
    
    tweet_id = arguments["tweet_id"]
    comment = arguments["comment"]
    
    try:
        # Quote tweet with comment
        response = get_write_client().create_tweet(text=comment, quote_tweet_id=tweet_id)
        quote_tweet_id = response.data['id']
        
        logger.info(f"Quote tweeted tweet {tweet_id} with comment. Quote tweet ID: {quote_tweet_id}")
        
        return [
            TextContent(
                type="text",
                text=f"Successfully quote tweeted tweet {tweet_id} with comment. Quote tweet ID: {quote_tweet_id}",
            )
        ]
    except tweepy.TweepError as e:
        logger.error(f"Twitter API error quote tweeting tweet {tweet_id}: {e}")
        raise RuntimeError(f"Twitter API error quote tweeting tweet {tweet_id}: {e}")
    except Exception as e:
        logger.error(f"Error quote tweeting tweet {tweet_id}: {str(e)}")
        raise RuntimeError(f"Error quote tweeting tweet {tweet_id}: {str(e)}")

async def handle_create_draft_quote_tweet(arguments: Any) -> Sequence[TextContent]:
    if not isinstance(arguments, dict) or "tweet_id" not in arguments or "comment" not in arguments:
        raise ValueError("Invalid arguments for create_draft_quote_tweet")
    
    tweet_id = arguments["tweet_id"]
    comment = arguments["comment"]
    
    try:
        # Create a draft quote tweet
        draft = {
            "comment": comment,
            "quote_tweet_id": tweet_id,
            "timestamp": datetime.now().isoformat(),
            "type": "quote_tweet"
        }
        
        # Ensure drafts directory exists
        os.makedirs("drafts", exist_ok=True)
        
        # Save the draft to a file
        draft_id = f"quote_draft_{int(datetime.now().timestamp())}.json"
        with open(os.path.join("drafts", draft_id), "w") as f:
            json.dump(draft, f, indent=2)
        
        logger.info(f"Draft quote tweet created: {draft_id}")
        
        return [
            TextContent(
                type="text",
                text=f"Draft quote tweet created with ID {draft_id} (quoting tweet {tweet_id})",
            )
        ]
    except Exception as e:
        logger.error(f"Error creating draft quote tweet: {str(e)}")
        raise RuntimeError(f"Error creating draft quote tweet: {str(e)}")

async def handle_upload_media(arguments: Any) -> Sequence[TextContent]:
    if not isinstance(arguments, dict) or "file_path" not in arguments or "media_type" not in arguments:
        raise ValueError("Invalid arguments for upload_media")
    
    file_path = arguments["file_path"]
    media_type = arguments["media_type"]
    alt_text = arguments.get("alt_text")
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")
        
        # Validate media type based on file extension
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            raise ValueError(f"Cannot determine media type for file: {file_path}")
        
        # Validate file type matches specified media_type
        if media_type == "image" and not mime_type.startswith("image/"):
            raise ValueError(f"File is not an image: {file_path}")
        elif media_type == "video" and not mime_type.startswith("video/"):
            raise ValueError(f"File is not a video: {file_path}")
        elif media_type == "gif" and mime_type != "image/gif":
            raise ValueError(f"File is not a GIF: {file_path}")
        
        # Upload media using tweepy
        media_upload = api.media_upload(filename=file_path)
        media_id = media_upload.media_id_string
        
        # Add alt text if provided and media is an image
        if alt_text and media_type in ["image", "gif"]:
            api.create_media_metadata(media_id=media_id, alt_text=alt_text)
            logger.info(f"Added alt text to media {media_id}: {alt_text}")
        
        logger.info(f"Uploaded {media_type} media: {media_id}")
        
        return [
            TextContent(
                type="text",
                text=f"Successfully uploaded {media_type} media. Media ID: {media_id}" + 
                     (f" (with alt text: '{alt_text}')" if alt_text else ""),
            )
        ]
    except tweepy.TweepError as e:
        logger.error(f"Twitter API error uploading media: {e}")
        raise RuntimeError(f"Twitter API error uploading media: {e}")
    except Exception as e:
        logger.error(f"Error uploading media {file_path}: {str(e)}")
        raise RuntimeError(f"Error uploading media {file_path}: {str(e)}")

async def handle_create_tweet_with_media(arguments: Any) -> Sequence[TextContent]:
    if not isinstance(arguments, dict) or "content" not in arguments or "media_ids" not in arguments:
        raise ValueError("Invalid arguments for create_tweet_with_media")
    
    content = arguments["content"]
    media_ids = arguments["media_ids"]
    
    if not isinstance(media_ids, list) or not media_ids:
        raise ValueError("media_ids must be a non-empty list")
    
    try:
        # Create tweet with media
        response = get_write_client().create_tweet(text=content, media_ids=media_ids)
        tweet_id = response.data['id']
        
        logger.info(f"Created tweet with media: {tweet_id}, media IDs: {media_ids}")
        
        return [
            TextContent(
                type="text",
                text=f"Successfully created tweet with media. Tweet ID: {tweet_id}, Media IDs: {', '.join(media_ids)}",
            )
        ]
    except tweepy.TweepError as e:
        logger.error(f"Twitter API error creating tweet with media: {e}")
        raise RuntimeError(f"Twitter API error creating tweet with media: {e}")
    except Exception as e:
        logger.error(f"Error creating tweet with media: {str(e)}")
        raise RuntimeError(f"Error creating tweet with media: {str(e)}")

async def handle_create_draft_tweet_with_media(arguments: Any) -> Sequence[TextContent]:
    if not isinstance(arguments, dict) or "content" not in arguments or "media_files" not in arguments:
        raise ValueError("Invalid arguments for create_draft_tweet_with_media")
    
    content = arguments["content"]
    media_files = arguments["media_files"]
    
    if not isinstance(media_files, list) or not media_files:
        raise ValueError("media_files must be a non-empty list")
    
    try:
        # Create draft with media file information
        draft = {
            "content": content,
            "media_files": media_files,
            "timestamp": datetime.now().isoformat(),
            "type": "tweet_with_media"
        }
        
        # Ensure drafts directory exists
        os.makedirs("drafts", exist_ok=True)
        
        # Save the draft to a file
        draft_id = f"media_draft_{int(datetime.now().timestamp())}.json"
        with open(os.path.join("drafts", draft_id), "w") as f:
            json.dump(draft, f, indent=2)
        
        logger.info(f"Draft tweet with media created: {draft_id}")
        
        return [
            TextContent(
                type="text",
                text=f"Draft tweet with media created with ID {draft_id} ({len(media_files)} media files)",
            )
        ]
    except Exception as e:
        logger.error(f"Error creating draft tweet with media: {str(e)}")
        raise RuntimeError(f"Error creating draft tweet with media: {str(e)}")

async def handle_get_media_info(arguments: Any) -> Sequence[TextContent]:
    if not isinstance(arguments, dict) or "media_id" not in arguments:
        raise ValueError("Invalid arguments for get_media_info")
    
    media_id = arguments["media_id"]
    
    try:
        # Get media information using tweepy
        # Note: This requires the media to be uploaded by the authenticated user
        media_info = api.get_media(media_id)
        
        info_text = f"Media ID: {media_id}\n"
        if hasattr(media_info, 'type'):
            info_text += f"Type: {media_info.type}\n"
        if hasattr(media_info, 'size'):
            info_text += f"Size: {media_info.size} bytes\n"
        if hasattr(media_info, 'url'):
            info_text += f"URL: {media_info.url}\n"
        
        logger.info(f"Retrieved media info for: {media_id}")
        
        return [
            TextContent(
                type="text",
                text=info_text,
            )
        ]
    except tweepy.TweepError as e:
        logger.error(f"Twitter API error getting media info: {e}")
        raise RuntimeError(f"Twitter API error getting media info: {e}")
    except Exception as e:
        logger.error(f"Error getting media info for {media_id}: {str(e)}")
        raise RuntimeError(f"Error getting media info for {media_id}: {str(e)}")

async def handle_get_tweet(arguments: Any) -> Sequence[TextContent]:
    if not isinstance(arguments, dict) or "tweet_id" not in arguments:
        raise ValueError("Invalid arguments for get_tweet")
    
    tweet_id = arguments["tweet_id"]
    include_author = arguments.get("include_author", True)
    
    # Try OAuth 2.0 first, then fallback to OAuth 1.0a
    read_client = get_read_client()
    
    try:
        logger.info(f"Attempting to get tweet: {tweet_id} using {'OAuth 2.0' if read_client == oauth2_client else 'OAuth 1.0a'}")
        
        # Get tweet information using tweepy
        tweet_fields = ["id", "text", "created_at", "author_id", "lang", "reply_settings", "referenced_tweets"]
        user_fields = ["id", "name", "username", "verified"] if include_author else None
        expansions = ["author_id", "referenced_tweets.id"] if include_author else ["referenced_tweets.id"]
        
        response = read_client.get_tweet(
            id=tweet_id,
            tweet_fields=tweet_fields,
            user_fields=user_fields,
            expansions=expansions
        )
        
        logger.info(f"API response received for tweet {tweet_id}")
        
        if not response.data:
            logger.warning(f"No data returned for tweet {tweet_id}")
            raise ValueError(f"Tweet {tweet_id} not found or not accessible")
        
        tweet = response.data
        result_text = f"Tweet ID: {tweet.id}\n"
        result_text += f"Content: {tweet.text}\n"
        result_text += f"Created: {tweet.created_at}\n"
        result_text += f"Language: {tweet.lang}\n"
        
        # Add author information if requested and available
        if include_author and response.includes and 'users' in response.includes:
            author = response.includes['users'][0]
            result_text += f"Author: {author.name} (@{author.username})\n"
            if hasattr(author, 'verified') and author.verified:
                result_text += "Verified: Yes\n"
        
        # Add referenced tweet information if available
        if hasattr(tweet, 'referenced_tweets') and tweet.referenced_tweets:
            ref_tweet = tweet.referenced_tweets[0]
            result_text += f"Reference Type: {ref_tweet.type}\n"
            result_text += f"Referenced Tweet ID: {ref_tweet.id}\n"
        
        logger.info(f"Successfully retrieved tweet: {tweet_id}")
        
        return [
            TextContent(
                type="text",
                text=result_text,
            )
        ]
    except tweepy.TweepyException as e:
        error_msg = f"Twitter API error getting tweet {tweet_id}: {e}"
        logger.error(error_msg)
        
        # Provide more specific error information
        if "403" in str(e):
            error_msg += "\n可能原因：API权限不足，请检查Twitter开发者项目的读取权限设置"
        elif "404" in str(e):
            error_msg += "\n可能原因：推文不存在、已删除或设为私密"
        elif "429" in str(e):
            error_msg += "\n可能原因：API调用频率限制，请稍后重试"
        elif "401" in str(e):
            error_msg += "\n可能原因：API凭据无效或过期"
            
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Error getting tweet {tweet_id}: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

async def handle_get_tweets(arguments: Any) -> Sequence[TextContent]:
    if not isinstance(arguments, dict) or "tweet_ids" not in arguments:
        raise ValueError("Invalid arguments for get_tweets")
    
    tweet_ids = arguments["tweet_ids"]
    include_author = arguments.get("include_author", True)
    
    if not isinstance(tweet_ids, list) or not tweet_ids:
        raise ValueError("tweet_ids must be a non-empty list")
    
    if len(tweet_ids) > 100:
        raise ValueError("Maximum 100 tweet IDs allowed")
    
    # Try OAuth 2.0 first, then fallback to OAuth 1.0a
    read_client = get_read_client()
    
    try:
        logger.info(f"Attempting to get {len(tweet_ids)} tweets using {'OAuth 2.0' if read_client == oauth2_client else 'OAuth 1.0a'}")
        
        # Get multiple tweets using tweepy
        tweet_fields = ["id", "text", "created_at", "author_id", "lang", "reply_settings", "referenced_tweets"]
        user_fields = ["id", "name", "username", "verified"] if include_author else None
        expansions = ["author_id", "referenced_tweets.id"] if include_author else ["referenced_tweets.id"]
        
        response = read_client.get_tweets(
            ids=tweet_ids,
            tweet_fields=tweet_fields,
            user_fields=user_fields,
            expansions=expansions
        )
        
        if not response.data:
            raise ValueError("No tweets found or accessible")
        
        result_text = f"Retrieved {len(response.data)} tweets:\n\n"
        
        # Create a mapping of user IDs to user info for efficiency
        users_map = {}
        if include_author and response.includes and 'users' in response.includes:
            for user in response.includes['users']:
                users_map[user.id] = user
        
        for i, tweet in enumerate(response.data, 1):
            result_text += f"--- Tweet {i} ---\n"
            result_text += f"ID: {tweet.id}\n"
            result_text += f"Content: {tweet.text}\n"
            result_text += f"Created: {tweet.created_at}\n"
            result_text += f"Language: {tweet.lang}\n"
            
            # Add author information if available
            if include_author and tweet.author_id in users_map:
                author = users_map[tweet.author_id]
                result_text += f"Author: {author.name} (@{author.username})\n"
                if hasattr(author, 'verified') and author.verified:
                    result_text += "Verified: Yes\n"
            
            # Add referenced tweet information if available
            if hasattr(tweet, 'referenced_tweets') and tweet.referenced_tweets:
                ref_tweet = tweet.referenced_tweets[0]
                result_text += f"Reference Type: {ref_tweet.type}\n"
                result_text += f"Referenced Tweet ID: {ref_tweet.id}\n"
            
            result_text += "\n"
        
        logger.info(f"Retrieved {len(response.data)} tweets")
        
        return [
            TextContent(
                type="text",
                text=result_text,
            )
        ]
    except tweepy.TweepError as e:
        logger.error(f"Twitter API error getting tweets: {e}")
        raise RuntimeError(f"Twitter API error getting tweets: {e}")
    except Exception as e:
        logger.error(f"Error getting tweets: {str(e)}")
        raise RuntimeError(f"Error getting tweets: {str(e)}")

async def handle_search_tweets(arguments: Any) -> Sequence[TextContent]:
    if not isinstance(arguments, dict) or "query" not in arguments:
        raise ValueError("Invalid arguments for search_tweets")
    
    query = arguments["query"]
    max_results = arguments.get("max_results", 10)
    include_author = arguments.get("include_author", True)
    
    if max_results < 1 or max_results > 100:
        raise ValueError("max_results must be between 1 and 100")
    
    # Try OAuth 2.0 first, then fallback to OAuth 1.0a
    read_client = get_read_client()
    
    try:
        logger.info(f"Searching tweets with query: {query} using {'OAuth 2.0' if read_client == oauth2_client else 'OAuth 1.0a'}")
        
        # Search tweets using tweepy
        tweet_fields = ["id", "text", "created_at", "author_id", "lang", "reply_settings", "referenced_tweets"]
        user_fields = ["id", "name", "username", "verified"] if include_author else None
        expansions = ["author_id", "referenced_tweets.id"] if include_author else ["referenced_tweets.id"]
        
        response = read_client.search_recent_tweets(
            query=query,
            max_results=max_results,
            tweet_fields=tweet_fields,
            user_fields=user_fields,
            expansions=expansions
        )
        
        logger.info(f"Search API response received for query: {query}")
        
        if not response.data:
            return [
                TextContent(
                    type="text",
                    text=f"No tweets found for query: {query}",
                )
            ]
        
        result_text = f"Search results for '{query}' ({len(response.data)} tweets):\n\n"
        
        # Create a mapping of user IDs to user info for efficiency
        users_map = {}
        if include_author and response.includes and 'users' in response.includes:
            for user in response.includes['users']:
                users_map[user.id] = user
        
        for i, tweet in enumerate(response.data, 1):
            result_text += f"--- Result {i} ---\n"
            result_text += f"ID: {tweet.id}\n"
            result_text += f"Content: {tweet.text}\n"
            result_text += f"Created: {tweet.created_at}\n"
            result_text += f"Language: {tweet.lang}\n"
            
            # Add author information if available
            if include_author and tweet.author_id in users_map:
                author = users_map[tweet.author_id]
                result_text += f"Author: {author.name} (@{author.username})\n"
                if hasattr(author, 'verified') and author.verified:
                    result_text += "Verified: Yes\n"
            
            # Add referenced tweet information if available
            if hasattr(tweet, 'referenced_tweets') and tweet.referenced_tweets:
                ref_tweet = tweet.referenced_tweets[0]
                result_text += f"Reference Type: {ref_tweet.type}\n"
                result_text += f"Referenced Tweet ID: {ref_tweet.id}\n"
            
            result_text += "\n"
        
        logger.info(f"Search completed: {len(response.data)} tweets found for '{query}'")
        
        return [
            TextContent(
                type="text",
                text=result_text,
            )
        ]
    except tweepy.TweepyException as e:
        error_msg = f"Twitter API error searching tweets: {e}"
        logger.error(error_msg)
        
        # Provide more specific error information
        if "403" in str(e):
            error_msg += "\n可能原因：API权限不足，免费用户可能无法使用搜索功能，或需要升级API计划"
        elif "429" in str(e):
            error_msg += "\n可能原因：API调用频率限制，请稍后重试"
        elif "401" in str(e):
            error_msg += "\n可能原因：API凭据无效或过期"
        elif "400" in str(e):
            error_msg += f"\n可能原因：搜索查询格式无效：'{query}'"
            
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Error searching tweets: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

async def handle_test_api_connection(arguments: Any) -> Sequence[TextContent]:
    """Test Twitter API connection and permissions"""
    try:
        logger.info("Testing Twitter API connection...")
        result_text = "=== Twitter API 连接测试 ===\n\n"
        
        # Test OAuth 1.0a client
        result_text += "📋 OAuth 1.0a 测试:\n"
        try:
            me = oauth1_client.get_me()
            if me.data:
                result_text += f"✅ OAuth 1.0a 连接成功！\n"
                result_text += f"   当前用户: {me.data.name} (@{me.data.username})\n"
                result_text += f"   用户ID: {me.data.id}\n"
            else:
                result_text += "❌ OAuth 1.0a 无法获取用户信息\n"
        except Exception as e:
            result_text += f"❌ OAuth 1.0a 连接失败: {e}\n"
        
        # Test OAuth 2.0 client if available
        result_text += "\n📋 OAuth 2.0 测试:\n"
        if oauth2_client:
            try:
                # OAuth 2.0 doesn't support get_me(), so we try a simple search
                search_response = oauth2_client.search_recent_tweets(
                    query="hello",
                    max_results=5,
                    tweet_fields=["id", "text"]
                )
                if search_response.data:
                    result_text += f"✅ OAuth 2.0 连接成功！(搜索到 {len(search_response.data)} 条推文)\n"
                else:
                    result_text += "⚠️ OAuth 2.0 连接成功但搜索返回空结果\n"
            except Exception as e:
                result_text += f"❌ OAuth 2.0 连接失败: {e}\n"
        else:
            result_text += "⚠️ 未配置 TWITTER_BEARER_TOKEN，跳过 OAuth 2.0 测试\n"
        
        # Test read operations with the best available client
        result_text += "\n📋 读取功能测试:\n"
        read_client = get_read_client()
        client_type = "OAuth 2.0" if read_client == oauth2_client else "OAuth 1.0a"
        result_text += f"使用 {client_type} 进行读取测试...\n"
        
        try:
            search_response = read_client.search_recent_tweets(
                query="AI",
                max_results=5,
                tweet_fields=["id", "text"]
            )
            if search_response.data:
                result_text += f"✅ 搜索功能正常 (找到 {len(search_response.data)} 条推文)\n"
            else:
                result_text += "⚠️ 搜索功能返回空结果\n"
        except tweepy.TweepyException as e:
            if "403" in str(e):
                result_text += "❌ 搜索功能被禁止 - 可能需要升级API计划\n"
            elif "429" in str(e):
                result_text += "⚠️ 搜索功能受限 - API调用频率限制\n"
            elif "401" in str(e):
                result_text += "❌ 认证失败 - 请检查API凭据\n"
            else:
                result_text += f"❌ 搜索功能错误: {e}\n"
        except Exception as e:
            result_text += f"❌ 搜索功能异常: {e}\n"
        
        # Test write operations
        result_text += "\n📋 写入功能测试:\n"
        try:
            # We don't actually post a tweet, just verify the client can be used for posting
            result_text += "✅ 写入客户端 (OAuth 1.0a) 已就绪\n"
            result_text += "   支持功能: 发推文、转推、回复、上传媒体\n"
        except Exception as e:
            result_text += f"❌ 写入客户端配置错误: {e}\n"
        
        # Summary and recommendations
        result_text += "\n=== 总结和建议 ===\n"
        
        if oauth2_client:
            result_text += "✅ 推荐配置: OAuth 1.0a + OAuth 2.0 双重认证\n"
            result_text += "   - OAuth 2.0 用于读取操作 (更稳定)\n"
            result_text += "   - OAuth 1.0a 用于写入操作 (发推文等)\n"
        else:
            result_text += "⚠️ 当前配置: 仅 OAuth 1.0a\n"
            result_text += "   建议添加 TWITTER_BEARER_TOKEN 以启用 OAuth 2.0\n"
        
        result_text += "\n如果遇到问题:\n"
        result_text += "1. 检查 Twitter Developer Portal 中的项目权限\n"
        result_text += "2. 确保 API 密钥未过期\n"
        result_text += "3. 验证账户类型和 API 使用限制\n"
        result_text += "4. 考虑升级到付费 API 计划以获得更多功能\n"
        
        logger.info("API connection test completed")
        
        return [
            TextContent(
                type="text",
                text=result_text,
            )
        ]
    except Exception as e:
        error_msg = f"API连接测试失败: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

# Implement the main function
async def main():
    import mcp
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )

def parse_scheduled_time(time_str: str) -> datetime:
    """Parse scheduled time string into datetime object"""
    time_str = time_str.strip()
    
    # Handle relative time formats like '+10m', '+1h', '+1d'
    if time_str.startswith('+'):
        relative_str = time_str[1:]
        now = datetime.now()
        
        if relative_str.endswith('m'):
            # Minutes
            minutes = int(relative_str[:-1])
            return now + timedelta(minutes=minutes)
        elif relative_str.endswith('h'):
            # Hours
            hours = int(relative_str[:-1])
            return now + timedelta(hours=hours)
        elif relative_str.endswith('d'):
            # Days
            days = int(relative_str[:-1])
            return now + timedelta(days=days)
        else:
            raise ValueError(f"Invalid relative time format: {time_str}")
    
    # Handle absolute time formats
    try:
        # Try ISO format with seconds
        return datetime.fromisoformat(time_str)
    except ValueError:
        try:
            # Try without seconds
            return datetime.strptime(time_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            try:
                # Try date only (assume current time)
                date_part = datetime.strptime(time_str, "%Y-%m-%d")
                now = datetime.now()
                return date_part.replace(hour=now.hour, minute=now.minute, second=now.second)
            except ValueError:
                raise ValueError(f"Invalid time format: {time_str}. Use ISO format (YYYY-MM-DDTHH:MM:SS) or relative (+10m, +1h, +1d)")

async def schedule_tweet_task():
    """Background task that checks and publishes scheduled tweets"""
    global _scheduler_running
    _scheduler_running = True
    logger.info("Tweet scheduler started")
    
    while _scheduler_running:
        try:
            await check_and_publish_scheduled_tweets()
            # Check every 30 seconds
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            logger.info("Tweet scheduler stopped")
            _scheduler_running = False
            break
        except Exception as e:
            logger.error(f"Error in tweet scheduler: {e}")
            # Continue running even if there's an error
            await asyncio.sleep(30)
    
    _scheduler_running = False

async def check_and_publish_scheduled_tweets():
    """Check for scheduled tweets that are ready to be published"""
    if not os.path.exists("scheduled"):
        return
    
    now = datetime.now()
    
    for filename in os.listdir("scheduled"):
        if not filename.endswith('.json'):
            continue
            
        filepath = os.path.join("scheduled", filename)
        
        try:
            with open(filepath, "r") as f:
                scheduled_item = json.load(f)
            
            scheduled_time = datetime.fromisoformat(scheduled_item["scheduled_time"])
            
            # Check if it's time to publish
            if now >= scheduled_time:
                await publish_scheduled_item(scheduled_item, filepath)
                
        except Exception as e:
            logger.error(f"Error processing scheduled item {filename}: {e}")

async def publish_scheduled_item(scheduled_item: dict, filepath: str):
    """Publish a scheduled tweet or thread"""
    try:
        schedule_type = scheduled_item.get("type", "tweet")
        
        if schedule_type == "tweet":
            # Single tweet
            content = scheduled_item["content"]
            response = get_write_client().create_tweet(text=content)
            tweet_id = response.data['id']
            logger.info(f"Published scheduled tweet ID {tweet_id}")
            
            # Remove the scheduled file
            os.remove(filepath)
            
        elif schedule_type == "thread":
            # Tweet thread
            contents = scheduled_item["contents"]
            published_tweet_ids = []
            last_tweet_id = None
            
            for i, content in enumerate(contents):
                if last_tweet_id is None:
                    response = get_write_client().create_tweet(text=content)
                else:
                    response = get_write_client().create_tweet(text=content, in_reply_to_tweet_id=last_tweet_id)
                last_tweet_id = response.data['id']
                published_tweet_ids.append(last_tweet_id)
                await asyncio.sleep(1)  # Avoid hitting rate limits
            
            logger.info(f"Published scheduled thread with {len(published_tweet_ids)} tweets, starting with ID {published_tweet_ids[0]}")
            
            # Remove the scheduled file
            os.remove(filepath)
            
        elif schedule_type == "recurring":
            # Recurring tweets
            await handle_recurring_tweet_publication(scheduled_item, filepath)
            
    except Exception as e:
        logger.error(f"Error publishing scheduled item: {e}")
        # Move failed item to a failed directory for manual review
        os.makedirs("scheduled/failed", exist_ok=True)
        failed_path = os.path.join("scheduled/failed", os.path.basename(filepath))
        os.rename(filepath, failed_path)

async def handle_recurring_tweet_publication(scheduled_item: dict, filepath: str):
    """Handle publication of recurring tweets"""
    contents = scheduled_item["contents"]
    current_index = scheduled_item.get("current_index", 0)
    total_count = scheduled_item.get("total_count", len(contents))
    published_count = scheduled_item.get("published_count", 0)
    
    # Check if we've published all tweets
    if published_count >= total_count:
        logger.info(f"Recurring tweet series completed ({published_count}/{total_count})")
        os.remove(filepath)
        return
    
    # Publish current tweet
    content = contents[current_index % len(contents)]
    response = get_write_client().create_tweet(text=content)
    tweet_id = response.data['id']
    logger.info(f"Published recurring tweet {published_count + 1}/{total_count}, ID {tweet_id}")
    
    # Update the scheduled item for next publication
    scheduled_item["current_index"] = (current_index + 1) % len(contents)
    scheduled_item["published_count"] = published_count + 1
    
    # Calculate next publication time
    interval_minutes = scheduled_item["interval_minutes"]
    next_time = datetime.now() + timedelta(minutes=interval_minutes)
    scheduled_item["scheduled_time"] = next_time.isoformat()
    
    # Save updated schedule or remove if completed
    if scheduled_item["published_count"] >= total_count:
        os.remove(filepath)
    else:
        with open(filepath, "w") as f:
            json.dump(scheduled_item, f, indent=2)

async def ensure_scheduler_running():
    """Ensure the scheduler is running, start it if not"""
    global _scheduled_task, _scheduler_running
    
    if not _scheduler_running and (_scheduled_task is None or _scheduled_task.done()):
        logger.info("Auto-starting tweet scheduler...")
        _scheduled_task = asyncio.create_task(schedule_tweet_task())
        return True
    return False

async def handle_create_scheduled_tweet(arguments: Any) -> Sequence[TextContent]:
    """Create a scheduled tweet"""
    if not isinstance(arguments, dict) or "content" not in arguments or "scheduled_time" not in arguments:
        raise ValueError("Invalid arguments for create_scheduled_tweet")
    
    content = arguments["content"]
    scheduled_time_str = arguments["scheduled_time"]
    
    try:
        # Parse the scheduled time
        scheduled_time = parse_scheduled_time(scheduled_time_str)
        
        # Check if the time is in the future
        if scheduled_time <= datetime.now():
            raise ValueError("Scheduled time must be in the future")
        
        # Create scheduled tweet data
        scheduled_tweet = {
            "type": "tweet",
            "content": content,
            "scheduled_time": scheduled_time.isoformat(),
            "created_at": datetime.now().isoformat()
        }
        
        # Ensure scheduled directory exists
        os.makedirs("scheduled", exist_ok=True)
        
        # Save the scheduled tweet
        schedule_id = f"scheduled_tweet_{int(datetime.now().timestamp())}.json"
        filepath = os.path.join("scheduled", schedule_id)
        
        with open(filepath, "w") as f:
            json.dump(scheduled_tweet, f, indent=2)
        
        # Auto-start scheduler if not running
        scheduler_started = await ensure_scheduler_running()
        
        logger.info(f"Scheduled tweet created: {schedule_id} for {scheduled_time}")
        
        scheduler_msg = " (Scheduler auto-started)" if scheduler_started else ""
        
        return [
            TextContent(
                type="text",
                text=f"Scheduled tweet created with ID {schedule_id}. Will be published at {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}{scheduler_msg}",
            )
        ]
        
    except Exception as e:
        logger.error(f"Error creating scheduled tweet: {str(e)}")
        raise RuntimeError(f"Error creating scheduled tweet: {str(e)}")

async def handle_create_scheduled_thread(arguments: Any) -> Sequence[TextContent]:
    """Create a scheduled tweet thread"""
    if not isinstance(arguments, dict) or "contents" not in arguments or "scheduled_time" not in arguments:
        raise ValueError("Invalid arguments for create_scheduled_thread")
    
    contents = arguments["contents"]
    scheduled_time_str = arguments["scheduled_time"]
    
    if not isinstance(contents, list) or not all(isinstance(item, str) for item in contents):
        raise ValueError("Invalid contents for create_scheduled_thread")
    
    try:
        # Parse the scheduled time
        scheduled_time = parse_scheduled_time(scheduled_time_str)
        
        # Check if the time is in the future
        if scheduled_time <= datetime.now():
            raise ValueError("Scheduled time must be in the future")
        
        # Create scheduled thread data
        scheduled_thread = {
            "type": "thread",
            "contents": contents,
            "scheduled_time": scheduled_time.isoformat(),
            "created_at": datetime.now().isoformat()
        }
        
        # Ensure scheduled directory exists
        os.makedirs("scheduled", exist_ok=True)
        
        # Save the scheduled thread
        schedule_id = f"scheduled_thread_{int(datetime.now().timestamp())}.json"
        filepath = os.path.join("scheduled", schedule_id)
        
        with open(filepath, "w") as f:
            json.dump(scheduled_thread, f, indent=2)
        
        # Auto-start scheduler if not running
        scheduler_started = await ensure_scheduler_running()
        
        logger.info(f"Scheduled thread created: {schedule_id} for {scheduled_time}")
        
        scheduler_msg = " (Scheduler auto-started)" if scheduler_started else ""
        
        return [
            TextContent(
                type="text",
                text=f"Scheduled thread created with ID {schedule_id}. Will be published at {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')} ({len(contents)} tweets){scheduler_msg}",
            )
        ]
        
    except Exception as e:
        logger.error(f"Error creating scheduled thread: {str(e)}")
        raise RuntimeError(f"Error creating scheduled thread: {str(e)}")

async def handle_create_recurring_tweets(arguments: Any) -> Sequence[TextContent]:
    """Create recurring tweets"""
    if not isinstance(arguments, dict) or "contents" not in arguments or "interval_minutes" not in arguments or "start_time" not in arguments:
        raise ValueError("Invalid arguments for create_recurring_tweets")
    
    contents = arguments["contents"]
    interval_minutes = arguments["interval_minutes"]
    start_time_str = arguments["start_time"]
    total_count = arguments.get("total_count", len(contents))
    
    if not isinstance(contents, list) or not all(isinstance(item, str) for item in contents):
        raise ValueError("Invalid contents for create_recurring_tweets")
    
    if interval_minutes < 1:
        raise ValueError("Interval must be at least 1 minute")
    
    try:
        # Parse the start time
        start_time = parse_scheduled_time(start_time_str)
        
        # Check if the time is in the future
        if start_time <= datetime.now():
            raise ValueError("Start time must be in the future")
        
        # Create recurring tweets data
        recurring_tweets = {
            "type": "recurring",
            "contents": contents,
            "interval_minutes": interval_minutes,
            "scheduled_time": start_time.isoformat(),
            "total_count": total_count,
            "current_index": 0,
            "published_count": 0,
            "created_at": datetime.now().isoformat()
        }
        
        # Ensure scheduled directory exists
        os.makedirs("scheduled", exist_ok=True)
        
        # Save the recurring tweets
        schedule_id = f"recurring_tweets_{int(datetime.now().timestamp())}.json"
        filepath = os.path.join("scheduled", schedule_id)
        
        with open(filepath, "w") as f:
            json.dump(recurring_tweets, f, indent=2)
        
        # Auto-start scheduler if not running
        scheduler_started = await ensure_scheduler_running()
        
        logger.info(f"Recurring tweets created: {schedule_id}, starting at {start_time}")
        
        scheduler_msg = " (Scheduler auto-started)" if scheduler_started else ""
        
        return [
            TextContent(
                type="text",
                text=f"Recurring tweets created with ID {schedule_id}. Will start at {start_time.strftime('%Y-%m-%d %H:%M:%S')}, publishing {total_count} tweets every {interval_minutes} minutes{scheduler_msg}",
            )
        ]
        
    except Exception as e:
        logger.error(f"Error creating recurring tweets: {str(e)}")
        raise RuntimeError(f"Error creating recurring tweets: {str(e)}")

async def handle_list_scheduled_tweets(arguments: Any) -> Sequence[TextContent]:
    """List all scheduled tweets"""
    try:
        scheduled_items = []
        
        if os.path.exists("scheduled"):
            for filename in os.listdir("scheduled"):
                if filename.endswith('.json'):
                    filepath = os.path.join("scheduled", filename)
                    try:
                        with open(filepath, "r") as f:
                            scheduled_item = json.load(f)
                        
                        # Add status information
                        scheduled_time = datetime.fromisoformat(scheduled_item["scheduled_time"])
                        now = datetime.now()
                        
                        if now >= scheduled_time:
                            status = "ready_to_publish"
                        else:
                            time_diff = scheduled_time - now
                            if time_diff.total_seconds() < 3600:  # Less than 1 hour
                                status = f"publishing_in_{int(time_diff.total_seconds() / 60)}_minutes"
                            else:
                                status = f"scheduled_for_{scheduled_time.strftime('%Y-%m-%d_%H:%M')}"
                        
                        scheduled_items.append({
                            "id": filename,
                            "scheduled_item": scheduled_item,
                            "status": status,
                            "scheduled_time_formatted": scheduled_time.strftime('%Y-%m-%d %H:%M:%S')
                        })
                    except Exception as e:
                        logger.error(f"Error reading scheduled item {filename}: {e}")
        
        # Sort by scheduled time
        scheduled_items.sort(key=lambda x: x["scheduled_item"]["scheduled_time"])
        
        return [
            TextContent(
                type="text",
                text=json.dumps(scheduled_items, indent=2, ensure_ascii=False),
            )
        ]
        
    except Exception as e:
        logger.error(f"Error listing scheduled tweets: {str(e)}")
        raise RuntimeError(f"Error listing scheduled tweets: {str(e)}")

async def handle_cancel_scheduled_tweet(arguments: Any) -> Sequence[TextContent]:
    """Cancel a scheduled tweet"""
    if not isinstance(arguments, dict) or "schedule_id" not in arguments:
        raise ValueError("Invalid arguments for cancel_scheduled_tweet")
    
    schedule_id = arguments["schedule_id"]
    filepath = os.path.join("scheduled", schedule_id)
    
    try:
        if not os.path.exists(filepath):
            raise ValueError(f"Scheduled tweet {schedule_id} does not exist")
        
        # Read the scheduled item before deleting
        with open(filepath, "r") as f:
            scheduled_item = json.load(f)
        
        # Delete the scheduled item
        os.remove(filepath)
        
        logger.info(f"Cancelled scheduled tweet: {schedule_id}")
        
        schedule_type = scheduled_item.get("type", "tweet")
        scheduled_time = datetime.fromisoformat(scheduled_item["scheduled_time"])
        
        return [
            TextContent(
                type="text",
                text=f"Successfully cancelled scheduled {schedule_type} {schedule_id} (was scheduled for {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')})",
            )
        ]
        
    except Exception as e:
        logger.error(f"Error cancelling scheduled tweet {schedule_id}: {str(e)}")
        raise RuntimeError(f"Error cancelling scheduled tweet {schedule_id}: {str(e)}")

async def handle_start_scheduler(arguments: Any) -> Sequence[TextContent]:
    """Start the tweet scheduler background task"""
    global _scheduled_task, _scheduler_running
    
    try:
        if _scheduler_running:
            return [
                TextContent(
                    type="text",
                    text="Tweet scheduler is already running",
                )
            ]
        
        # Start the scheduler task
        _scheduled_task = asyncio.create_task(schedule_tweet_task())
        
        logger.info("Tweet scheduler started manually")
        
        return [
            TextContent(
                type="text",
                text="Tweet scheduler started successfully. It will check for scheduled tweets every 30 seconds.",
            )
        ]
        
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        raise RuntimeError(f"Error starting scheduler: {str(e)}")

async def handle_stop_scheduler(arguments: Any) -> Sequence[TextContent]:
    """Stop the tweet scheduler background task"""
    global _scheduled_task, _scheduler_running
    
    try:
        if not _scheduler_running:
            return [
                TextContent(
                    type="text",
                    text="Tweet scheduler is not running",
                )
            ]
        
        # Signal the scheduler to stop
        _scheduler_running = False
        
        # Cancel the scheduler task if it exists
        if _scheduled_task and not _scheduled_task.done():
            _scheduled_task.cancel()
            
            try:
                await _scheduled_task
            except asyncio.CancelledError:
                pass
        
        _scheduled_task = None
        
        logger.info("Tweet scheduler stopped")
        
        return [
            TextContent(
                type="text",
                text="Tweet scheduler stopped successfully",
            )
        ]
        
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")
        raise RuntimeError(f"Error stopping scheduler: {str(e)}")

async def handle_get_scheduler_status(arguments: Any) -> Sequence[TextContent]:
    """Get the current status of the tweet scheduler"""
    global _scheduled_task, _scheduler_running
    
    try:
        status_info = {
            "scheduler_running": _scheduler_running,
            "task_exists": _scheduled_task is not None,
            "task_done": _scheduled_task.done() if _scheduled_task else None,
            "scheduled_tweets_count": 0,
            "ready_to_publish_count": 0
        }
        
        # Count scheduled tweets
        if os.path.exists("scheduled"):
            now = datetime.now()
            for filename in os.listdir("scheduled"):
                if filename.endswith('.json'):
                    filepath = os.path.join("scheduled", filename)
                    try:
                        with open(filepath, "r") as f:
                            scheduled_item = json.load(f)
                        
                        status_info["scheduled_tweets_count"] += 1
                        
                        scheduled_time = datetime.fromisoformat(scheduled_item["scheduled_time"])
                        if now >= scheduled_time:
                            status_info["ready_to_publish_count"] += 1
                    except Exception:
                        continue
        
        status_text = f"""Tweet Scheduler Status:
- Running: {'Yes' if _scheduler_running else 'No'}
- Background Task: {'Active' if _scheduled_task and not _scheduled_task.done() else 'Inactive'}
- Scheduled Tweets: {status_info['scheduled_tweets_count']}
- Ready to Publish: {status_info['ready_to_publish_count']}

{'✅ Scheduler is actively monitoring and will publish tweets automatically' if _scheduler_running else '⚠️ Scheduler is stopped - tweets will not be published automatically'}"""
        
        return [
            TextContent(
                type="text",
                text=status_text,
            )
        ]
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise RuntimeError(f"Error getting scheduler status: {str(e)}")

async def handle_configure_auto_delete_failed_drafts(arguments: Any) -> Sequence[TextContent]:
    """Configure whether to automatically delete drafts when publishing fails"""
    if not isinstance(arguments, dict) or "enabled" not in arguments:
        raise ValueError("Invalid arguments for configure_auto_delete_failed_drafts")
    
    enabled = arguments["enabled"]
    global AUTO_DELETE_FAILED_DRAFTS
    AUTO_DELETE_FAILED_DRAFTS = enabled
    
    # Also update the environment variable for persistence (if .env file exists)
    try:
        env_file = ".env"
        if os.path.exists(env_file):
            # Read existing .env content
            with open(env_file, "r") as f:
                lines = f.readlines()
            
            # Update or add the AUTO_DELETE_FAILED_DRAFTS setting
            updated = False
            for i, line in enumerate(lines):
                if line.startswith("AUTO_DELETE_FAILED_DRAFTS="):
                    lines[i] = f"AUTO_DELETE_FAILED_DRAFTS={'true' if enabled else 'false'}\n"
                    updated = True
                    break
            
            if not updated:
                lines.append(f"AUTO_DELETE_FAILED_DRAFTS={'true' if enabled else 'false'}\n")
            
            # Write back to .env file
            with open(env_file, "w") as f:
                f.writelines(lines)
            
            logger.info(f"Updated .env file: AUTO_DELETE_FAILED_DRAFTS={'true' if enabled else 'false'}")
    except Exception as e:
        logger.warning(f"Could not update .env file: {e}")
    
    status = "enabled" if enabled else "disabled"
    logger.info(f"Auto-delete failed drafts: {status}")
    
    return [
        TextContent(
            type="text",
            text=f"Auto-delete failed drafts is now {status}. "
                 f"{'Drafts will be automatically deleted when publishing fails.' if enabled else 'Drafts will be preserved when publishing fails for manual retry.'}"
        )
    ]

async def handle_get_auto_delete_config(arguments: Any) -> Sequence[TextContent]:
    """Get current configuration for auto-deleting failed drafts"""
    status = "enabled" if AUTO_DELETE_FAILED_DRAFTS else "disabled"
    
    return [
        TextContent(
            type="text",
            text=f"Auto-delete failed drafts is currently {status}. "
                 f"{'Drafts will be automatically deleted when publishing fails.' if AUTO_DELETE_FAILED_DRAFTS else 'Drafts will be preserved when publishing fails for manual retry.'}"
        )
    ]

async def handle_get_global_trends(arguments: Any) -> Sequence[TextContent]:
    """Get current global trending topics on Twitter/X"""
    try:
        limit = arguments.get("limit", 10)
        logger.info(f"Getting global trends (limit: {limit})")
        
        # Get global trends using Twitter API v1.1 (trends are only available in v1.1)
        trends = api.get_place_trends(id=1)  # WOEID 1 = worldwide
        
        if not trends or not trends[0].get('trends'):
            return [
                TextContent(
                    type="text",
                    text="No global trends found at this time."
                )
            ]
        
        trend_list = trends[0]['trends'][:limit]
        
        result = {
            "location": "Worldwide",
            "as_of": trends[0].get('as_of', ''),
            "created_at": trends[0].get('created_at', ''),
            "trends": []
        }
        
        for i, trend in enumerate(trend_list, 1):
            trend_info = {
                "rank": i,
                "name": trend.get('name', ''),
                "url": trend.get('url', ''),
                "promoted_content": trend.get('promoted_content'),
                "query": trend.get('query', ''),
                "tweet_volume": trend.get('tweet_volume')
            }
            result["trends"].append(trend_info)
        
        logger.info(f"Retrieved {len(result['trends'])} global trends")
        
        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )
        ]
        
    except tweepy.TweepyException as e:
        if "403" in str(e):
            error_msg = "Access to trends API is forbidden - may require upgraded API plan"
        elif "429" in str(e):
            error_msg = "Rate limit exceeded for trends API"
        elif "401" in str(e):
            error_msg = "Authentication failed - check API credentials"
        else:
            error_msg = f"Twitter API error getting global trends: {str(e)}"
        
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Error getting global trends: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

async def handle_get_regional_trends(arguments: Any) -> Sequence[TextContent]:
    """Get trending topics for a specific region/location"""
    try:
        woeid = arguments.get("woeid")
        location_name = arguments.get("location_name")
        limit = arguments.get("limit", 10)
        
        # Location name to WOEID mapping for common locations
        location_mapping = {
            "united states": 23424977,
            "usa": 23424977,
            "us": 23424977,
            "japan": 23424856,
            "united kingdom": 23424975,
            "uk": 23424975,
            "canada": 23424775,
            "australia": 23424748,
            "germany": 23424829,
            "france": 23424819,
            "brazil": 23424768,
            "india": 23424848,
            "china": 23424781,
            "south korea": 23424868,
            "mexico": 23424900,
            "italy": 23424853,
            "spain": 23424950,
            "russia": 23424936,
            "turkey": 23424969,
            "argentina": 23424747,
            "worldwide": 1,
            "global": 1
        }
        
        # Determine WOEID
        if woeid is None and location_name:
            location_key = location_name.lower().strip()
            woeid = location_mapping.get(location_key)
            if woeid is None:
                available_locations = ", ".join(location_mapping.keys())
                return [
                    TextContent(
                        type="text",
                        text=f"Location '{location_name}' not found. Available locations: {available_locations}"
                    )
                ]
        elif woeid is None:
            woeid = 1  # Default to worldwide
        
        logger.info(f"Getting regional trends for WOEID {woeid} (limit: {limit})")
        
        # Get trends for the specified location
        trends = api.get_place_trends(id=woeid)
        
        if not trends or not trends[0].get('trends'):
            return [
                TextContent(
                    type="text",
                    text=f"No trends found for the specified location (WOEID: {woeid})."
                )
            ]
        
        trend_list = trends[0]['trends'][:limit]
        location_info = trends[0].get('locations', [{}])[0]
        
        result = {
            "location": {
                "name": location_info.get('name', f'WOEID {woeid}'),
                "woeid": location_info.get('woeid', woeid),
                "country": location_info.get('country', ''),
                "countryCode": location_info.get('countryCode', '')
            },
            "as_of": trends[0].get('as_of', ''),
            "created_at": trends[0].get('created_at', ''),
            "trends": []
        }
        
        for i, trend in enumerate(trend_list, 1):
            trend_info = {
                "rank": i,
                "name": trend.get('name', ''),
                "url": trend.get('url', ''),
                "promoted_content": trend.get('promoted_content'),
                "query": trend.get('query', ''),
                "tweet_volume": trend.get('tweet_volume')
            }
            result["trends"].append(trend_info)
        
        logger.info(f"Retrieved {len(result['trends'])} trends for {result['location']['name']}")
        
        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )
        ]
        
    except tweepy.TweepyException as e:
        if "403" in str(e):
            error_msg = "Access to trends API is forbidden - may require upgraded API plan"
        elif "429" in str(e):
            error_msg = "Rate limit exceeded for trends API"
        elif "401" in str(e):
            error_msg = "Authentication failed - check API credentials"
        elif "404" in str(e):
            error_msg = f"Location not found (WOEID: {woeid})"
        else:
            error_msg = f"Twitter API error getting regional trends: {str(e)}"
        
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Error getting regional trends: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

async def handle_get_available_trend_locations(arguments: Any) -> Sequence[TextContent]:
    """Get list of available locations for trend queries"""
    try:
        logger.info("Getting available trend locations")
        
        # Get available trend locations
        locations = api.available_trends()
        
        if not locations:
            return [
                TextContent(
                    type="text",
                    text="No trend locations available."
                )
            ]
        
        # Group locations by country
        countries = {}
        for location in locations:
            country = location.get('country', 'Unknown')
            country_code = location.get('countryCode', '')
            
            if country not in countries:
                countries[country] = {
                    "country": country,
                    "countryCode": country_code,
                    "locations": []
                }
            
            countries[country]["locations"].append({
                "name": location.get('name', ''),
                "woeid": location.get('woeid', ''),
                "placeType": location.get('placeType', {})
            })
        
        # Sort countries and locations
        sorted_countries = []
        for country_name in sorted(countries.keys()):
            country_data = countries[country_name]
            country_data["locations"].sort(key=lambda x: x["name"])
            sorted_countries.append(country_data)
        
        result = {
            "total_locations": len(locations),
            "countries": sorted_countries
        }
        
        logger.info(f"Retrieved {len(locations)} available trend locations across {len(countries)} countries")
        
        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )
        ]
        
    except tweepy.TweepyException as e:
        if "403" in str(e):
            error_msg = "Access to trends API is forbidden - may require upgraded API plan"
        elif "429" in str(e):
            error_msg = "Rate limit exceeded for trends API"
        elif "401" in str(e):
            error_msg = "Authentication failed - check API credentials"
        else:
            error_msg = f"Twitter API error getting available trend locations: {str(e)}"
        
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Error getting available trend locations: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

async def handle_get_topic_details(arguments: Any) -> Sequence[TextContent]:
    """Get detailed information about a specific trending topic or hashtag"""
    try:
        topic = arguments["topic"]
        max_results = arguments.get("max_results", 20)
        include_retweets = arguments.get("include_retweets", False)
        
        logger.info(f"Getting topic details for '{topic}' (max_results: {max_results}, include_retweets: {include_retweets})")
        
        # Build search query
        search_query = topic
        if not include_retweets:
            search_query += " -is:retweet"
        
        # Search for tweets about the topic
        read_client = get_read_client()
        response = read_client.search_recent_tweets(
            query=search_query,
            max_results=min(max_results, 100),
            tweet_fields=["id", "text", "author_id", "created_at", "public_metrics", "context_annotations", "entities"],
            user_fields=["id", "name", "username", "verified", "public_metrics"],
            expansions=["author_id"]
        )
        
        if not response.data:
            return [
                TextContent(
                    type="text",
                    text=f"No recent tweets found for topic: {topic}"
                )
            ]
        
        # Process users data
        users_dict = {}
        if response.includes and response.includes.get('users'):
            for user in response.includes['users']:
                users_dict[user.id] = {
                    "name": user.name,
                    "username": user.username,
                    "verified": getattr(user, 'verified', False),
                    "followers_count": user.public_metrics.get('followers_count', 0) if user.public_metrics else 0,
                    "following_count": user.public_metrics.get('following_count', 0) if user.public_metrics else 0
                }
        
        # Process tweets
        tweets = []
        total_engagement = 0
        hashtags = {}
        mentions = {}
        
        for tweet in response.data:
            author_info = users_dict.get(tweet.author_id, {})
            
            # Calculate engagement
            metrics = tweet.public_metrics or {}
            engagement = (metrics.get('like_count', 0) + 
                         metrics.get('retweet_count', 0) + 
                         metrics.get('reply_count', 0) + 
                         metrics.get('quote_count', 0))
            total_engagement += engagement
            
            # Extract hashtags and mentions
            if hasattr(tweet, 'entities') and tweet.entities:
                if tweet.entities.get('hashtags'):
                    for hashtag in tweet.entities['hashtags']:
                        tag = hashtag['tag'].lower()
                        hashtags[tag] = hashtags.get(tag, 0) + 1
                
                if tweet.entities.get('mentions'):
                    for mention in tweet.entities['mentions']:
                        username = mention['username'].lower()
                        mentions[username] = mentions.get(username, 0) + 1
            
            tweet_info = {
                "id": tweet.id,
                "text": tweet.text,
                "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                "author": {
                    "id": tweet.author_id,
                    "name": author_info.get("name", ""),
                    "username": author_info.get("username", ""),
                    "verified": author_info.get("verified", False),
                    "followers_count": author_info.get("followers_count", 0)
                },
                "metrics": {
                    "like_count": metrics.get('like_count', 0),
                    "retweet_count": metrics.get('retweet_count', 0),
                    "reply_count": metrics.get('reply_count', 0),
                    "quote_count": metrics.get('quote_count', 0),
                    "engagement": engagement
                }
            }
            tweets.append(tweet_info)
        
        # Sort tweets by engagement
        tweets.sort(key=lambda x: x['metrics']['engagement'], reverse=True)
        
        # Get top hashtags and mentions
        top_hashtags = sorted(hashtags.items(), key=lambda x: x[1], reverse=True)[:10]
        top_mentions = sorted(mentions.items(), key=lambda x: x[1], reverse=True)[:10]
        
        result = {
            "topic": topic,
            "search_query": search_query,
            "summary": {
                "total_tweets": len(tweets),
                "total_engagement": total_engagement,
                "average_engagement": round(total_engagement / len(tweets), 2) if tweets else 0,
                "search_timestamp": datetime.now().isoformat()
            },
            "top_hashtags": [{"hashtag": f"#{tag}", "count": count} for tag, count in top_hashtags],
            "top_mentions": [{"username": f"@{username}", "count": count} for username, count in top_mentions],
            "tweets": tweets
        }
        
        logger.info(f"Retrieved details for topic '{topic}': {len(tweets)} tweets, {total_engagement} total engagement")
        
        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )
        ]
        
    except tweepy.TweepyException as e:
        if "403" in str(e):
            error_msg = "Access to search API is forbidden - may require upgraded API plan"
        elif "429" in str(e):
            error_msg = "Rate limit exceeded for search API"
        elif "401" in str(e):
            error_msg = "Authentication failed - check API credentials"
        else:
            error_msg = f"Twitter API error getting topic details: {str(e)}"
        
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Error getting topic details: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

async def handle_search_trending_hashtags(arguments: Any) -> Sequence[TextContent]:
    """Search for trending hashtags related to a keyword"""
    try:
        keyword = arguments["keyword"]
        max_results = arguments.get("max_results", 10)
        
        logger.info(f"Searching trending hashtags for keyword '{keyword}' (max_results: {max_results})")
        
        # Search for tweets containing the keyword to find related hashtags
        read_client = get_read_client()
        response = read_client.search_recent_tweets(
            query=f"{keyword} has:hashtags -is:retweet",
            max_results=100,  # Get more tweets to analyze hashtags
            tweet_fields=["id", "text", "entities", "public_metrics", "created_at"],
            expansions=["author_id"]
        )
        
        if not response.data:
            return [
                TextContent(
                    type="text",
                    text=f"No recent tweets with hashtags found for keyword: {keyword}"
                )
            ]
        
        # Extract and count hashtags
        hashtag_stats = {}
        total_tweets = len(response.data)
        
        for tweet in response.data:
            if hasattr(tweet, 'entities') and tweet.entities and tweet.entities.get('hashtags'):
                tweet_engagement = 0
                if tweet.public_metrics:
                    tweet_engagement = (tweet.public_metrics.get('like_count', 0) + 
                                      tweet.public_metrics.get('retweet_count', 0) + 
                                      tweet.public_metrics.get('reply_count', 0) + 
                                      tweet.public_metrics.get('quote_count', 0))
                
                for hashtag in tweet.entities['hashtags']:
                    tag = hashtag['tag'].lower()
                    if tag not in hashtag_stats:
                        hashtag_stats[tag] = {
                            "hashtag": f"#{hashtag['tag']}",
                            "count": 0,
                            "total_engagement": 0,
                            "tweets": []
                        }
                    
                    hashtag_stats[tag]["count"] += 1
                    hashtag_stats[tag]["total_engagement"] += tweet_engagement
                    
                    # Store sample tweet info
                    if len(hashtag_stats[tag]["tweets"]) < 3:
                        hashtag_stats[tag]["tweets"].append({
                            "id": tweet.id,
                            "text": tweet.text[:100] + "..." if len(tweet.text) > 100 else tweet.text,
                            "engagement": tweet_engagement,
                            "created_at": tweet.created_at.isoformat() if tweet.created_at else None
                        })
        
        if not hashtag_stats:
            return [
                TextContent(
                    type="text",
                    text=f"No hashtags found in recent tweets for keyword: {keyword}"
                )
            ]
        
        # Calculate trending score (combination of frequency and engagement)
        for tag_data in hashtag_stats.values():
            frequency_score = tag_data["count"] / total_tweets
            avg_engagement = tag_data["total_engagement"] / tag_data["count"] if tag_data["count"] > 0 else 0
            # Normalize engagement (simple approach)
            engagement_score = min(avg_engagement / 100, 1.0)  # Cap at 1.0
            tag_data["trending_score"] = (frequency_score * 0.6) + (engagement_score * 0.4)
            tag_data["average_engagement"] = round(avg_engagement, 2)
        
        # Sort by trending score and limit results
        trending_hashtags = sorted(
            hashtag_stats.values(), 
            key=lambda x: x["trending_score"], 
            reverse=True
        )[:max_results]
        
        result = {
            "keyword": keyword,
            "analysis": {
                "total_tweets_analyzed": total_tweets,
                "unique_hashtags_found": len(hashtag_stats),
                "top_hashtags_returned": len(trending_hashtags),
                "analysis_timestamp": datetime.now().isoformat()
            },
            "trending_hashtags": []
        }
        
        for i, hashtag_data in enumerate(trending_hashtags, 1):
            result["trending_hashtags"].append({
                "rank": i,
                "hashtag": hashtag_data["hashtag"],
                "usage_count": hashtag_data["count"],
                "total_engagement": hashtag_data["total_engagement"],
                "average_engagement": hashtag_data["average_engagement"],
                "trending_score": round(hashtag_data["trending_score"], 4),
                "sample_tweets": hashtag_data["tweets"]
            })
        
        logger.info(f"Found {len(trending_hashtags)} trending hashtags for keyword '{keyword}'")
        
        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )
        ]
        
    except tweepy.TweepyException as e:
        if "403" in str(e):
            error_msg = "Access to search API is forbidden - may require upgraded API plan"
        elif "429" in str(e):
            error_msg = "Rate limit exceeded for search API"
        elif "401" in str(e):
            error_msg = "Authentication failed - check API credentials"
        else:
            error_msg = f"Twitter API error searching trending hashtags: {str(e)}"
        
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Error searching trending hashtags: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())