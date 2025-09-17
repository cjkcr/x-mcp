# X(Twitter) MCP 服务器

[![smithery badge](https://smithery.ai/badge/x-mcp)](https://smithery.ai/server/x-mcp)

[English](README.md) | **中文**

一个通过 Claude 聊天直接创建、管理和发布 X/Twitter 帖子的 MCP 服务器。

> **说明：** 本项目修改自 [vidhupv/x-mcp](https://github.com/vidhupv/x-mcp)，增加了回复推文的功能。

## 功能特性

- ✅ 创建推文草稿
- ✅ 创建推文串草稿
- ✅ 创建回复推文草稿
- ✅ 列出所有草稿
- ✅ 发布草稿（推文、推文串和回复）
- ✅ 直接回复推文（无需创建草稿）
- ✅ 删除草稿
- ✅ 发布失败时保留草稿

<a href="https://glama.ai/mcp/servers/jsxr09dktf">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/jsxr09dktf/badge" alt="X(Twitter) Server MCP server" />
</a>

## 快速设置

### 通过 Smithery 安装

通过 [Smithery](https://smithery.ai/server/x-mcp) 自动为 Claude Desktop 安装 X(Twitter) MCP 服务器：

```bash
npx -y @smithery/cli install x-mcp --client claude
```

### 手动安装

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

## 使用示例

* "发推文'刚学会通过AI发推文 - 太震撼了！🤖✨'"
* "创建一个关于披萨历史的推文串"
* "显示我的推文草稿"
* "发布这个草稿！"
* "删除那个草稿"
* "回复推文 1234567890，说'很棒的观点！感谢分享。'"
* "为推文 1234567890 创建回复草稿，内容是'我完全同意这个观点。'"

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

## 故障排除

如果无法正常工作：
- 确保 UV 已全局安装（如果没有，请使用 `pip uninstall uv` 卸载，然后使用 `brew install uv` 重新安装）
- 或者使用 `which uv` 找到 UV 路径，并将 `"command": "uv"` 替换为完整路径
- 验证所有 X/Twitter 凭据是否正确
- 检查配置中的 x-mcp 路径是否与您的实际仓库位置匹配

## 支持与贡献

如果您遇到问题或有改进建议，欢迎：
- 提交 Issue 报告问题
- 提交 Pull Request 贡献代码
- 参与讨论和功能建议

## 详细功能说明

更多详细的功能说明和使用指南，请参阅：
- [回复功能详细说明](回复功能说明.md)
- [REPLY_FUNCTIONALITY.md](REPLY_FUNCTIONALITY.md)（英文版）

## 致谢

本项目基于 [Vidhu Panhavoor Vasudevan](https://github.com/vidhupv) 在原始 [x-mcp](https://github.com/vidhupv/x-mcp) 仓库中的优秀工作。

### 本分支的新增功能
- ✅ **回复推文功能** - 创建回复草稿和直接回复现有推文
- ✅ **增强的草稿管理** - 改进了发布失败时的草稿保留机制
- ✅ **更好的错误处理** - 更详细的错误信息和恢复选项

特别感谢原作者为创建这个 MCP 服务器奠定了基础！