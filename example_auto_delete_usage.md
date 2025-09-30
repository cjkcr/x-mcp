# 自动删除失败草稿功能使用示例

## 基本使用

### 1. 查看当前配置状态
```
查看当前自动删除草稿的配置状态
```

**输出示例：**
```
Auto-delete failed drafts is currently enabled. Drafts will be automatically deleted when publishing fails.
```

### 2. 启用自动删除功能
```
启用发布失败时自动删除草稿功能
```

**输出示例：**
```
Auto-delete failed drafts is now enabled. Drafts will be automatically deleted when publishing fails.
```

### 3. 禁用自动删除功能
```
禁用发布失败时自动删除草稿功能
```

**输出示例：**
```
Auto-delete failed drafts is now disabled. Drafts will be preserved when publishing fails for manual retry.
```

## 实际场景示例

### 场景1：启用自动删除时的发布失败

1. **创建草稿：**
```
创建推文草稿"这是一个测试推文 #test"
```

2. **尝试发布（假设失败）：**
```
发布草稿 draft_1234567890.json
```

3. **启用自动删除时的输出：**
```
Error publishing draft draft_1234567890.json: Twitter API error: Invalid credentials. Draft has been deleted.
```

### 场景2：禁用自动删除时的发布失败

1. **禁用自动删除：**
```
禁用发布失败时自动删除草稿功能
```

2. **创建草稿：**
```
创建推文草稿"这是另一个测试推文 #test2"
```

3. **尝试发布（假设失败）：**
```
发布草稿 draft_1234567891.json
```

4. **禁用自动删除时的输出：**
```
Error publishing draft draft_1234567891.json: Twitter API error: Invalid credentials. Draft preserved for retry.
```

5. **稍后重试：**
```
发布草稿 draft_1234567891.json
```

### 场景3：推文串部分发布成功

1. **创建推文串草稿：**
```
创建推文串草稿，内容为：
- "这是推文串的第一条 1/3"
- "这是推文串的第二条 2/3"  
- "这是推文串的第三条 3/3"
```

2. **尝试发布（假设第三条失败）：**
```
发布草稿 thread_draft_1234567892.json
```

3. **部分成功时的输出：**
```
Thread publishing failed after 2 tweets. Published tweets: ['1234567890123456789', '1234567890123456790']. Draft has been deleted. Error: Rate limit exceeded.
```

## 配置文件示例

### Claude Desktop 配置
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
        "AUTO_DELETE_FAILED_DRAFTS": "true"
      }
    }
  }
}
```

### .env 文件示例
```env
# Twitter API Credentials
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here

# Auto-delete configuration
AUTO_DELETE_FAILED_DRAFTS=true
```

## 支持的环境变量值

### 启用自动删除的值：
- `true`
- `True`
- `TRUE`
- `1`
- `yes`
- `on`

### 禁用自动删除的值：
- `false`
- `False`
- `FALSE`
- `0`
- `no`
- `off`

### 默认行为：
- 空值或未设置：默认启用（`true`）
- 无效值：禁用（`false`）

## 日志示例

### 启用自动删除时的日志：
```
2024-01-01 12:00:00 - ERROR - Twitter API error publishing draft draft_123.json: Invalid credentials
2024-01-01 12:00:00 - INFO - Deleted draft draft_123.json due to publishing failure (auto-delete enabled)
```

### 禁用自动删除时的日志：
```
2024-01-01 12:00:00 - ERROR - Twitter API error publishing draft draft_123.json: Invalid credentials  
2024-01-01 12:00:00 - INFO - Draft draft_123.json preserved for retry (auto-delete disabled)
```

### 配置更改时的日志：
```
2024-01-01 12:00:00 - INFO - Auto-delete failed drafts: enabled
2024-01-01 12:00:00 - INFO - Updated .env file: AUTO_DELETE_FAILED_DRAFTS=true
```