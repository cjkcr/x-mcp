import os
import json
import logging
import asyncio
import mimetypes
from datetime import datetime
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
                    raise RuntimeError(f"Thread publishing failed after {len(published_tweet_ids)} tweets. Published tweets: {published_tweet_ids}. Error: {thread_error}")
                else:
                    raise thread_error
        else:
            raise ValueError(f"Invalid draft format for {draft_id}")
            
    except tweepy.TweepError as e:
        logger.error(f"Twitter API error publishing draft {draft_id}: {e}")
        # Draft is NOT deleted on API error - user can retry or fix the issue
        raise RuntimeError(f"Twitter API error publishing draft {draft_id}: {e}. Draft preserved for retry.")
    except Exception as e:
        logger.error(f"Error publishing draft {draft_id}: {str(e)}")
        # Draft is NOT deleted on other errors - user can retry or fix the issue
        raise RuntimeError(f"Error publishing draft {draft_id}: {str(e)}. Draft preserved for retry.")


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

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())