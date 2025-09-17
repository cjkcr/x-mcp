# X(Twitter) MCP Server / X(Twitter) MCP 服务器

[![smithery badge](https://smithery.ai/badge/x-mcp)](https://smithery.ai/server/x-mcp)

**English** | [中文](#中文版本)

An MCP server to create, manage and publish X/Twitter posts directly through Claude chat.

一个通过 Claude 聊天直接创建、管理和发布 X/Twitter 帖子的 MCP 服务器。

## Features / 功能特性

- ✅ Create draft tweets / 创建推文草稿
- ✅ Create draft tweet threads / 创建推文串草稿
- ✅ Create draft replies to existing tweets / 创建回复推文草稿
- ✅ List all drafts / 列出所有草稿
- ✅ Publish drafts (tweets, threads, and replies) / 发布草稿（推文、推文串和回复）
- ✅ Reply to tweets directly (without creating drafts) / 直接回复推文（无需创建草稿）
- ✅ Delete drafts / 删除草稿
- ✅ Draft preservation on publish failure / 发布失败时保留草稿

<a href="https://glama.ai/mcp/servers/jsxr09dktf">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/jsxr09dktf/badge" alt="X(Twitter) Server MCP server" />
</a>

## Quick Setup / 快速设置

### Installing via Smithery / 通过 Smithery 安装

To install X(Twitter) MCP Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/x-mcp):

通过 [Smithery](https://smithery.ai/server/x-mcp) 自动为 Claude Desktop 安装 X(Twitter) MCP 服务器：

```bash
npx -y @smithery/cli install x-mcp --client claude
```

### Manual Installation / 手动安装

1. **Clone the repository / 克隆仓库：**
```bash
git clone https://github.com/yourusername/x-mcp.git
```

2. **Install UV globally using Homebrew in Terminal / 使用 Homebrew 在终端中全局安装 UV：**
```bash
brew install uv
```

3. **Create claude_desktop_config.json / 创建 claude_desktop_config.json：**
   - **For MacOS / macOS 系统：** Open directory `~/Library/Application Support/Claude/` and create the file inside it / 打开目录 `~/Library/Application Support/Claude/` 并在其中创建文件
   - **For Windows / Windows 系统：** Open directory `%APPDATA%/Claude/` and create the file inside it / 打开目录 `%APPDATA%/Claude/` 并在其中创建文件

4. **Add this configuration to claude_desktop_config.json / 将此配置添加到 claude_desktop_config.json：**
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

5. **Get your X/Twitter API credentials / 获取您的 X/Twitter API 凭据：**
   - Go to [X API Developer Portal](https://developer.x.com/en/products/x-api) / 前往 [X API 开发者门户](https://developer.x.com/en/products/x-api)
   - Create a project / 创建一个项目
   - In User Authentication Settings: Set up with Read and Write permissions, Web App type / 在用户身份验证设置中：设置为读写权限，Web 应用类型
   - Set Callback URL to `http://localhost/` and Website URL to `http://example.com/` / 将回调 URL 设置为 `http://localhost/`，网站 URL 设置为 `http://example.com/`
   - Generate and copy all keys and tokens from Keys and Tokens section / 从密钥和令牌部分生成并复制所有密钥和令牌

6. **Update the config file / 更新配置文件：**
   - Replace `/path/to/x-mcp` with your actual repository path / 将 `/path/to/x-mcp` 替换为您的实际仓库路径
   - Add your X/Twitter API credentials / 添加您的 X/Twitter API 凭据

7. **Quit Claude completely and reopen it / 完全退出 Claude 并重新打开**

## Usage Examples / 使用示例

**English Examples:**
* "Tweet 'Just learned how to tweet through AI - mind blown! 🤖✨'"
* "Create a thread about the history of pizza"
* "Show me my draft tweets"
* "Publish this draft!"
* "Delete that draft"
* "Reply to tweet 1234567890 with 'Great point! Thanks for sharing.'"
* "Create a draft reply to tweet 1234567890 saying 'I completely agree with this perspective.'"

**中文示例：**
* "发推文'刚学会通过AI发推文 - 太震撼了！🤖✨'"
* "创建一个关于披萨历史的推文串"
* "显示我的推文草稿"
* "发布这个草稿！"
* "删除那个草稿"
* "回复推文 1234567890，说'很棒的观点！感谢分享。'"
* "为推文 1234567890 创建回复草稿，内容是'我完全同意这个观点。'"

## Troubleshooting / 故障排除

**If not working / 如果无法正常工作：**
- Make sure UV is installed globally (if not, uninstall with `pip uninstall uv` and reinstall with `brew install uv`) / 确保 UV 已全局安装（如果没有，请使用 `pip uninstall uv` 卸载，然后使用 `brew install uv` 重新安装）
- Or find UV path with `which uv` and replace `"command": "uv"` with the full path / 或者使用 `which uv` 找到 UV 路径，并将 `"command": "uv"` 替换为完整路径
- Verify all X/Twitter credentials are correct / 验证所有 X/Twitter 凭据是否正确
- Check if the x-mcp path in config matches your actual repository location / 检查配置中的 x-mcp 路径是否与您的实际仓库位置匹配

---

# 中文版本

## 功能特性

- ✅ **创建推文草稿** - 在发布前准备和编辑推文
- ✅ **创建推文串草稿** - 创建多条相关推文的串联
- ✅ **创建回复草稿** - 为现有推文准备回复内容
- ✅ **列出所有草稿** - 查看和管理所有未发布的内容
- ✅ **发布草稿** - 将草稿发布为实际的推文、推文串或回复
- ✅ **直接回复推文** - 无需创建草稿即可快速回复
- ✅ **删除草稿** - 清理不需要的草稿内容
- ✅ **发布失败时保留草稿** - 确保内容安全，支持重试

## 安装说明

请参考上方的英文安装说明，步骤完全相同。

## 高级功能

### 草稿管理系统
- **智能草稿保存** - 发布失败时自动保留草稿，成功时自动删除
- **多类型草稿支持** - 支持普通推文、推文串和回复推文草稿
- **详细状态反馈** - 清晰的操作结果和错误信息

### 回复功能
- **草稿回复模式** - 创建回复草稿，可以编辑后再发布
- **直接回复模式** - 立即回复推文，适合快速互动
- **回复链追踪** - 自动处理回复关系和推文串连接

### 错误处理
- **网络错误恢复** - API 调用失败时保留草稿内容
- **部分发布处理** - 推文串发布中断时记录已发布内容
- **详细错误报告** - 提供具体的错误信息和解决建议

## 技术特性

- **基于 MCP 协议** - 与 Claude 无缝集成
- **异步处理** - 支持高效的并发操作
- **本地草稿存储** - 安全的本地文件系统存储
- **完整的日志记录** - 详细的操作日志和调试信息

## 支持与贡献

如果您遇到问题或有改进建议，欢迎：
- 提交 Issue 报告问题
- 提交 Pull Request 贡献代码
- 参与讨论和功能建议

---

**English** | **中文**