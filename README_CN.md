# X(Twitter) MCP 服务器

[![smithery badge](https://smithery.ai/badge/x-mcp)](https://smithery.ai/server/x-mcp)

[English](README.md) | **中文**

一个通过 Claude code 和 Gemini CLI 聊天直接创建、管理和发布 X/Twitter 帖子的 MCP 服务器。

> **说明：** 本项目修改自 [vidhupv/x-mcp](https://github.com/vidhupv/x-mcp)，增加了回复推文的功能。

## 功能特性

### 🔐 双重认证支持
- ✅ **OAuth 1.0a**: 用于写入操作（发推文、转推等）
- ✅ **OAuth 2.0**: 用于读取操作（获取推文、搜索等）
- ✅ **自动客户端选择**: 系统自动选择最佳认证方式
- ✅ **智能降级**: OAuth 2.0不可用时自动回退到OAuth 1.0a

### 📝 推文管理
- ✅ 创建推文草稿
- ✅ 创建推文串草稿
- ✅ 创建回复推文草稿
- ✅ 列出所有草稿
- ✅ 发布草稿（推文、推文串和回复）
- ✅ 直接回复推文（无需创建草稿）
- ✅ 转发现有推文
- ✅ 带评论的引用转发
- ✅ 创建引用转发草稿
- ✅ 删除草稿
- ✅ 发布失败时保留草稿

### 📷 媒体支持
- ✅ 上传媒体文件（图片、视频、GIF）
- ✅ 创建带媒体附件的推文
- ✅ 为图片添加无障碍Alt文本
- ✅ 获取媒体文件信息

### 📖 推文获取（改进版）
- ✅ 获取推文内容和信息（支持双重认证）
- ✅ 搜索最近推文（优化的错误处理）
- ✅ 批量获取多条推文（更稳定的连接）
- ✅ 详细的错误诊断和建议
- ✅ API连接测试工具

<a href="https://glama.ai/mcp/servers/jsxr09dktf">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/jsxr09dktf/badge" alt="X(Twitter) Server MCP server" />
</a>

## 快速设置

### 通过 Smithery 安装

通过 [Smithery](https://smithery.ai/server/x-mcp) 自动为 Claude code 安装 X(Twitter) MCP 服务器：

```bash
npx -y @smithery/cli install x-mcp --client claude
```

### Claude code 手动安装

1. **克隆仓库：**
```bash
git clone https://github.com/yourusername/x-mcp.git
```

2. **使用 Homebrew 在终端中全局安装 UV：**
```bash
brew install uv
```

3. **创建 claude_desktop_config.json：**
   - **macOS 系统：** 打开目录 `~/Library/Application Support/Claude/` 并在其中创建文件
   - **Windows 系统：** 打开目录 `%APPDATA%/Claude/` 并在其中创建文件

4. **将此配置添加到 claude_desktop_config.json：**

#### 基础配置（仅OAuth 1.0a）
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

#### 推荐配置（OAuth 1.0a + OAuth 2.0双重认证）
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

> **💡 推荐使用双重认证配置**：添加`TWITTER_BEARER_TOKEN`可以显著提高推文获取功能的稳定性和成功率。

5. **获取您的 X/Twitter API 凭据：**
   - 前往 [X API 开发者门户](https://developer.x.com/en/products/x-api)
   - 创建一个项目
   - 在用户身份验证设置中：设置为读写权限，Web 应用类型
   - 将回调 URL 设置为 `http://localhost/`，网站 URL 设置为 `http://example.com/`
   - 从密钥和令牌部分生成并复制所有密钥和令牌

6. **更新配置文件：**
   - 将 `/path/to/x-mcp` 替换为您的实际仓库路径
   - 添加您的 X/Twitter API 凭据

7. **完全退出 Claude 并重新打开**

### Gemini CLI 配置

如果您想在 Gemini CLI 中使用此 MCP 服务器而不是 Claude code：

1. **安装 Gemini CLI：**
```bash
npm install -g @google/gemini-cli
```

2. **创建或更新您的 MCP 配置文件：**
   - 创建名为 `~/.gemini/settings.json` 的文件
   - 添加以下配置：

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

3. **启动支持 MCP 的 Gemini CLI：**
```bash
重新启动gemini cli
```

4. **更新配置文件：**
   - 将 `/path/to/x-mcp` 替换为您的实际仓库路径
   - 添加您的 X/Twitter API 凭据

## 使用示例

适用于 Claude code 和 Gemini CLI：

* "发推文'刚学会通过AI发推文 - 太震撼了！🤖✨'"
* "创建一个关于披萨历史的推文串"
* "显示我的推文草稿"
* "发布这个草稿！"
* "删除那个草稿"
* "回复推文 1234567890，说'很棒的观点！感谢分享。'"
* "为推文 1234567890 创建回复草稿，内容是'我完全同意这个观点。'"
* "转发推文 1234567890"
* "引用转发推文 1234567890，评论'这正是我想说的！'"
* "为推文 1234567890 创建引用转发草稿，评论'这里有很棒的见解'"
* "上传图片 /path/to/image.jpg，Alt文本为'山峦上的美丽日落'"
* "使用媒体ID 123456789 创建推文'看看这张精彩的照片！'"
* "创建带媒体的推文草稿'我的最新项目'，附加 /path/to/video.mp4"
* "获取推文 1234567890 的内容和信息"
* "搜索包含'人工智能 OR AI'的最近7天推文"
* "批量获取推文 123456789, 987654321, 555666777 的信息"

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

- **基于 MCP 协议** - 与 Claude code 无缝集成
- **异步处理** - 支持高效的并发操作
- **本地草稿存储** - 安全的本地文件系统存储
- **完整的日志记录** - 详细的操作日志和调试信息

## 故障排除

### 基本问题
如果无法正常工作：
- 确保 UV 已全局安装（如果没有，请使用 `pip uninstall uv` 卸载，然后使用 `brew install uv` 重新安装）
- 或者使用 `which uv` 找到 UV 路径，并将 `"command": "uv"` 替换为完整路径
- 验证所有 X/Twitter 凭据是否正确
- 检查配置中的 x-mcp 路径是否与您的实际仓库位置匹配

### 🔧 API连接测试

**快速诊断：**
```
测试API连接
```
在Claude中运行此命令可以：
- 测试OAuth 1.0a和OAuth 2.0连接
- 检查API权限和限制
- 提供详细的诊断信息和建议

**运行测试脚本：**
```bash
cd /path/to/x-mcp
python test_tweet_functions.py
```

### 🚨 401 Unauthorized 错误修复

**问题症状：**
- 发推文时出现"401 Unauthorized"错误
- 能发推文但无法获取推文

**解决方案：**

1. **添加Bearer Token（推荐）：**
   ```json
   "env": {
     "TWITTER_API_KEY": "your_api_key",
     "TWITTER_API_SECRET": "your_api_secret",
     "TWITTER_ACCESS_TOKEN": "your_access_token",
     "TWITTER_ACCESS_TOKEN_SECRET": "your_access_token_secret",
     "TWITTER_BEARER_TOKEN": "your_bearer_token"
   }
   ```

2. **重新生成API凭据：**
   - 访问[Twitter Developer Portal](https://developer.x.com/)
   - 重新生成所有API密钥和令牌
   - 确保权限设置为"Read and write"

3. **检查项目设置：**
   - 用户身份验证设置：读写权限
   - 应用类型：Web应用
   - 回调URL：`http://localhost/`
   - 网站URL：`http://example.com/`

### 📖 推文获取功能问题

**双重认证优势：**
- OAuth 2.0用于读取操作（更稳定）
- OAuth 1.0a用于写入操作（必需）
- 自动降级处理

**常见错误及解决：**

| 错误代码 | 原因 | 解决方案 |
|---------|------|----------|
| 401 | 认证失败 | 检查API凭据，重新生成令牌 |
| 403 | 权限不足 | 升级API计划或检查权限设置 |
| 404 | 推文不存在 | 验证推文ID，检查推文是否公开 |
| 429 | 频率限制 | 等待15分钟或升级API计划 |

**API计划限制：**
- **免费用户**: 基本功能，有限制
- **Basic ($100/月)**: 完整读取功能
- **Pro ($5000/月)**: 高级功能和更高限制

### 🔍 详细诊断步骤

1. **检查认证状态：**
   ```
   测试API连接
   ```

2. **验证配置：**
   - 确认所有环境变量已设置
   - 检查路径是否正确
   - 验证API密钥格式

3. **测试特定功能：**
   ```
   搜索包含"hello"的推文
   获取推文 1234567890 的内容
   ```

4. **查看详细日志：**
   - 检查Claude Desktop控制台
   - 查看MCP服务器日志
   - 注意具体错误信息

## 支持与贡献

如果您遇到问题或有改进建议，欢迎：
- 提交 Issue 报告问题
- 提交 Pull Request 贡献代码
- 参与讨论和功能建议

## 详细功能说明

更多详细的功能说明和使用指南，请参阅：
- **[OAuth双重认证配置指南](OAuth双重认证配置指南.md)** - 🆕 详细的双重认证设置指南
- [推文获取功能说明](推文获取功能说明.md)
- [推文获取功能故障排除指南](推文获取功能故障排除指南.md)
- [回复功能详细说明](回复功能说明.md)
- [REPLY_FUNCTIONALITY.md](REPLY_FUNCTIONALITY.md)（英文版）

## 致谢

本项目基于 [Vidhu Panhavoor Vasudevan](https://github.com/vidhupv) 在原始 [x-mcp](https://github.com/vidhupv/x-mcp) 仓库中的优秀工作。

### 本分支的新增功能
- 🆕 **OAuth双重认证系统** - 支持OAuth 1.0a + OAuth 2.0，自动选择最佳认证方式
- 🆕 **401错误修复** - 解决了推文获取时的认证问题
- 🆕 **智能客户端选择** - 读取操作优先使用OAuth 2.0，写入操作使用OAuth 1.0a
- 🆕 **增强的错误处理** - 详细的错误诊断和中文错误提示
- 🆕 **API连接测试工具** - 内置的连接测试和诊断功能
- ✅ **回复推文功能** - 创建回复草稿和直接回复现有推文
- ✅ **转发推文功能** - 简单转发和带评论的引用转发
- ✅ **媒体功能** - 上传图片、视频、GIF，支持Alt文本
- ✅ **推文获取功能** - 获取推文内容、搜索推文、批量获取多条推文
- ✅ **增强的草稿管理** - 改进了发布失败时的草稿保留机制，支持所有草稿类型

特别感谢原作者为创建这个 MCP 服务器奠定了基础！