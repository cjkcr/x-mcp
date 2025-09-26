# Twitter API OAuth 双重认证配置指南

## 概述

为了解决Twitter API的401 Unauthorized错误并提供更稳定的服务，我们现在支持OAuth 1.0a和OAuth 2.0双重认证：

- **OAuth 1.0a**: 用于写入操作（发推文、转推、回复等）
- **OAuth 2.0**: 用于读取操作（获取推文、搜索等），通常更稳定

## 配置步骤

### 1. 获取OAuth 1.0a凭据（必需）

在[Twitter Developer Portal](https://developer.x.com/)中：

1. 创建或选择你的项目
2. 生成以下凭据：
   - `API Key` (Consumer Key)
   - `API Secret` (Consumer Secret)
   - `Access Token`
   - `Access Token Secret`

### 2. 获取OAuth 2.0 Bearer Token（推荐）

在同一个项目中：

1. 进入项目设置
2. 找到"Bearer Token"部分
3. 生成Bearer Token

### 3. 配置环境变量

#### 方法1：在Claude Desktop配置中设置

编辑你的`claude_desktop_config.json`：

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

#### 方法2：使用.env文件

在项目根目录创建`.env`文件：

```bash
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token
```

## 权限设置

### Twitter Developer Portal设置

1. **项目类型**: 选择适合的项目类型
2. **用户身份验证设置**:
   - 应用权限：`Read and write`
   - 应用类型：`Web App`
   - 回调URL：`http://localhost/`
   - 网站URL：`http://example.com/`

### API访问级别

- **免费用户**: 基本功能，有限制
- **付费用户**: 完整功能，更高限制

## 测试配置

### 使用测试脚本

```bash
cd /path/to/x-mcp
python test_tweet_functions.py
```

### 在Claude中测试

```
测试API连接
```

## 故障排除

### 常见错误及解决方案

#### 401 Unauthorized
- **原因**: API凭据无效或过期
- **解决**: 重新生成API密钥和令牌

#### 403 Forbidden
- **原因**: 权限不足或功能需要付费计划
- **解决**: 检查权限设置或升级API计划

#### 429 Rate Limit Exceeded
- **原因**: API调用频率超限
- **解决**: 等待限制重置或升级计划

### 配置验证清单

- [ ] OAuth 1.0a凭据已设置且有效
- [ ] OAuth 2.0 Bearer Token已设置（推荐）
- [ ] Twitter项目权限设置为"Read and write"
- [ ] API密钥未过期
- [ ] 网络连接正常

## 优势对比

### 仅OAuth 1.0a配置
- ✅ 支持所有写入操作
- ✅ 支持读取操作
- ⚠️ 读取操作可能不够稳定
- ⚠️ 更容易遇到权限问题

### OAuth 1.0a + OAuth 2.0配置（推荐）
- ✅ 支持所有写入操作
- ✅ 更稳定的读取操作
- ✅ 自动选择最佳认证方式
- ✅ 更好的错误处理
- ✅ 更高的成功率

## 系统行为

### 自动客户端选择

系统会自动选择最佳的客户端：

1. **读取操作**: 优先使用OAuth 2.0，回退到OAuth 1.0a
2. **写入操作**: 始终使用OAuth 1.0a

### 错误处理

- 提供详细的错误信息和建议
- 自动重试机制
- 智能降级处理

## 监控和维护

### 定期检查

1. **API使用情况**: 在Twitter Developer Portal查看
2. **错误日志**: 检查应用日志
3. **权限状态**: 确保权限未被撤销

### 更新凭据

当需要更新凭据时：

1. 在Twitter Developer Portal生成新凭据
2. 更新配置文件
3. 重启MCP服务器
4. 运行测试验证

## 支持

如果遇到问题：

1. 运行测试脚本诊断问题
2. 检查Twitter Developer Portal设置
3. 查看详细错误日志
4. 参考故障排除指南

记住：Twitter API的政策和限制经常变化，建议定期检查官方文档和更新配置。