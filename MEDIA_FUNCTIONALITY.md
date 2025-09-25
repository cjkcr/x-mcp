# Media Functionality Documentation

## Overview

This project now supports comprehensive media functionality, including uploading images, videos, and GIF animations, creating tweets with media attachments, and accessibility alt text support, providing users with rich multimedia tweet experiences.

## New Tools

### 1. `upload_media` - Upload Media Files
Upload images, videos, or GIF files to Twitter and get media IDs for subsequent tweets.

**Parameters:**
- `file_path` (string, required): Local path to the media file
- `media_type` (string, required): Media type, options: `"image"`, `"video"`, `"gif"`
- `alt_text` (string, optional): Alternative text for accessibility (for images)

**Supported File Formats:**
- **Images**: JPG, JPEG, PNG, WebP
- **Videos**: MP4, MOV, AVI
- **GIFs**: GIF animations

**Use Cases:**
- Prepare media content for tweets
- Batch upload multiple media files
- Add accessibility descriptions to images

**Example:**
```json
{
  "name": "upload_media",
  "arguments": {
    "file_path": "/Users/username/Pictures/sunset.jpg",
    "media_type": "image",
    "alt_text": "Beautiful sunset over mountains with orange-red gradient sky"
  }
}
```

### 2. `create_tweet_with_media` - Create Tweet with Media
Create tweets using uploaded media IDs.

**Parameters:**
- `content` (string, required): Text content of the tweet
- `media_ids` (array, required): List of media IDs, maximum 4

**Use Cases:**
- Post tweets with images
- Share video content
- Post GIF animations

**Example:**
```json
{
  "name": "create_tweet_with_media",
  "arguments": {
    "content": "Beautiful sunset I captured today! 🌅",
    "media_ids": ["1234567890123456789"]
  }
}
```

### 3. `create_draft_tweet_with_media` - Create Media Tweet Draft
Create tweet drafts containing media files for later publishing.

**Parameters:**
- `content` (string, required): Text content of the tweet
- `media_files` (array, required): List of media file information

**Media File Object Structure:**
```json
{
  "file_path": "file path",
  "media_type": "media type",
  "alt_text": "alt text (optional)"
}
```

**Use Cases:**
- Prepare tweets with multiple media files
- Content requiring review
- Scheduled media tweets

**Example:**
```json
{
  "name": "create_draft_tweet_with_media",
  "arguments": {
    "content": "My photography portfolio 📸",
    "media_files": [
      {
        "file_path": "/path/to/photo1.jpg",
        "media_type": "image",
        "alt_text": "City nightscape with bright lights"
      },
      {
        "file_path": "/path/to/photo2.jpg",
        "media_type": "image",
        "alt_text": "Natural landscape with green trees"
      }
    ]
  }
}
```

### 4. `get_media_info` - Get Media Information
Retrieve detailed information about uploaded media.

**Parameters:**
- `media_id` (string, required): Media ID to query

**Returned Information:**
- Media ID
- Media type
- File size
- Media URL (if available)

**Example:**
```json
{
  "name": "get_media_info",
  "arguments": {
    "media_id": "1234567890123456789"
  }
}
```

## Enhanced Existing Features

### Enhanced `publish_draft` Function
Now supports publishing media drafts with automatic:

1. **Media File Upload** - Automatically upload media files from drafts
2. **Alt Text Application** - Add accessibility descriptions to images and GIFs
3. **Tweet Creation** - Create tweets using uploaded media IDs
4. **Draft Cleanup** - Delete draft files after successful publishing

### Enhanced `list_drafts` Function
Now displays detailed information about media drafts:

- Tweet content preview
- Number and type of media files
- Path and alt text for each media file
- Draft type identifier (tweet_with_media)

**Display Example:**
```
📷 Media Tweet Draft: media_draft_1234567890.json
   Content: My photography portfolio 📸
   Media Files: 2 files
     - image: /path/to/photo1.jpg (Alt: City nightscape with bright lights)
     - image: /path/to/photo2.jpg (Alt: Natural landscape with green trees)
```

## Data Structure

### Media Tweet Draft JSON Structure
```json
{
  "content": "Tweet text content",
  "media_files": [
    {
      "file_path": "/path/to/file.jpg",
      "media_type": "image",
      "alt_text": "Alt text description for image"
    }
  ],
  "timestamp": "2025-09-17T10:30:00.000000",
  "type": "tweet_with_media"
}
```

**Field Descriptions:**
- `content`: Tweet text content
- `media_files`: Array of media file information
- `timestamp`: Draft creation time
- `type`: Draft type identifier, value is "tweet_with_media"

## Workflows

### Workflow 1: Direct Media Tweet Publishing
1. **Upload Media**
   - User: `"Upload image /path/to/sunset.jpg with alt text 'Beautiful sunset'"`
   - System calls `upload_media`
   - Returns media ID

2. **Create Tweet**
   - User: `"Create tweet 'Today's sunset is beautiful!' using media ID 123456789"`
   - System calls `create_tweet_with_media`
   - Immediately publishes tweet with media

### Workflow 2: Draft Mode Media Tweet
1. **Create Media Draft**
   - User: `"Create media tweet draft 'My portfolio' with image /path/to/photo.jpg"`
   - System calls `create_draft_tweet_with_media`
   - Draft saved to local file system

2. **View and Manage Drafts**
   - User: `"Show my drafts"`
   - System calls `list_drafts`
   - Displays all drafts including media drafts

3. **Publish Draft**
   - User: `"Publish this media draft"`
   - System calls `publish_draft`
   - Automatically uploads media files and publishes tweet

## Accessibility Features

### Alt Text Support
- **Automatic Application** - Automatically add alt text to images and GIFs
- **Optional Setting** - Users can set alt text for each media file individually
- **Accessibility Compliance** - Complies with Web Content Accessibility Guidelines (WCAG)

### File Validation
- **Type Checking** - Verify file type matches specified media type
- **Existence Check** - Ensure file exists at specified path
- **Format Support** - Support mainstream image, video, and GIF formats

## Error Handling

### 🔧 Media Upload Error Handling

**Common Error Types:**

1. **File Not Found**
   ```
   File not found: /path/to/image.jpg
   ```

2. **File Type Mismatch**
   ```
   File is not an image: /path/to/document.pdf
   ```

3. **File Size Limit**
   ```
   File size exceeds Twitter's limits
   ```

4. **Unsupported Format**
   ```
   Cannot determine media type for file
   ```

### Draft Preservation Mechanism
Consistent with other features, media functionality also supports draft preservation:

- ✅ **Drafts preserved on upload failure** - Users can fix file issues and retry
- ✅ **Drafts deleted on successful publishing** - Avoid duplicate publishing
- ✅ **Partial upload failure handling** - Record successfully uploaded media

## Technical Implementation

### Media Upload Process
1. **File Validation** - Check file existence and type
2. **MIME Type Detection** - Use mimetypes library to detect file type
3. **Twitter Upload** - Use tweepy's media_upload method
4. **Alt Text Application** - Call create_media_metadata to add descriptions
5. **Return Media ID** - Provide for subsequent tweet use

### Supported Media Limits
- **Images**: Maximum 5MB, supports JPG, PNG, WebP, GIF
- **Videos**: Maximum 512MB, supports MP4, MOV
- **GIFs**: Maximum 15MB
- **Quantity Limit**: Maximum 4 media files per tweet

### API Call Examples
```python
# Upload media
media_upload = client.media_upload(filename=file_path)
media_id = media_upload.media_id_string

# Add alt text
client.create_media_metadata(media_id=media_id, alt_text=alt_text)

# Create tweet with media
response = client.create_tweet(text=content, media_ids=media_ids)
```

## Best Practices

### Media File Preparation
- **Optimize File Size** - Compress images and videos for faster upload
- **Choose Appropriate Formats** - Use Twitter-recommended file formats
- **Prepare Alt Text** - Provide meaningful descriptions for all images

### Alt Text Writing Guidelines
- **Describe Content** - Concisely describe the main content of images
- **Avoid Redundancy** - Don't repeat information already in the tweet
- **Keep Concise** - Keep within 125 characters
- **Focus on Key Points** - Highlight key information in images

### Performance Optimization
- **Batch Upload** - Prepare multiple media files at once
- **Local Caching** - Save media IDs to avoid duplicate uploads
- **Asynchronous Processing** - Use asynchronous methods for large file uploads

### Security Considerations
- **File Scanning** - Ensure uploaded files are safe and harmless
- **Path Validation** - Verify file path legitimacy
- **Permission Checking** - Ensure read permissions for files

## Compatibility

### Twitter API Compatibility
- Supports Twitter API v2 media upload
- Compatible with tweepy library media features
- Follows Twitter's media policies and limits

### File System Compatibility
- Supports Windows, macOS, Linux file paths
- Automatically handles different OS path separators
- Supports relative and absolute paths

## Usage Examples

### Basic Media Upload
```bash
# Upload image
"Upload image /Users/username/photos/sunset.jpg with media type image and alt text 'Beautiful sunset by the sea'"

# Upload video
"Upload video /Users/username/videos/demo.mp4 with media type video"

# Upload GIF
"Upload GIF /Users/username/gifs/funny.gif with media type gif and alt text 'Funny cat animation'"
```

### Create Media Tweets
```bash
# Create tweet with media directly
"Create tweet 'Today's photography work 📸' using media ID 1234567890123456789"

# Create multimedia tweet
"Create tweet 'My travel photo collection 🌍' using media IDs 123456789,987654321"
```

### Media Draft Management
```bash
# Create media draft
"Create media tweet draft 'My new project showcase' with file /path/to/screenshot.png, media type image, alt text 'Project interface screenshot'"

# Publish media draft
"Publish media draft media_draft_1234567890.json"
```

## Future Extensions

Potential future features to consider:
- Media file preprocessing (compression, cropping)
- Batch media upload management
- Local media file caching
- Video thumbnail generation
- Media file metadata extraction
- Automatic alt text generation (AI-assisted)

This media functionality implementation greatly enhances users' ability to create rich multimedia content, providing a complete, user-friendly, and accessible media tweet solution.