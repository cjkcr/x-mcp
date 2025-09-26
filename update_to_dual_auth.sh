#!/bin/bash

# Twitter API 双重认证更新脚本
# 用于将现有的x-mcp安装更新到支持OAuth 1.0a + OAuth 2.0的版本

echo "🔄 Twitter API 双重认证更新脚本"
echo "=================================="

# 检查是否在正确的目录
if [ ! -f "pyproject.toml" ] || [ ! -d "src/x_mcp" ]; then
    echo "❌ 错误：请在x-mcp项目根目录运行此脚本"
    exit 1
fi

echo "✅ 检测到x-mcp项目"

# 备份当前配置
echo "📦 备份当前草稿..."
if [ -d "drafts" ]; then
    cp -r drafts drafts_backup_$(date +%Y%m%d_%H%M%S)
    echo "✅ 草稿已备份"
fi

# 检查git状态
if command -v git &> /dev/null && [ -d ".git" ]; then
    echo "📋 检查git状态..."
    if [ -n "$(git status --porcelain)" ]; then
        echo "⚠️  警告：有未提交的更改，建议先提交或备份"
        read -p "是否继续？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ 更新已取消"
            exit 1
        fi
    fi
fi

# 拉取最新更改（如果是git仓库）
if command -v git &> /dev/null && [ -d ".git" ]; then
    echo "🔄 拉取最新更改..."
    git pull origin main || git pull origin master
fi

# 安装/更新依赖
echo "📦 更新依赖..."
if command -v uv &> /dev/null; then
    uv sync
else
    echo "⚠️  警告：未找到uv，请确保已安装"
fi

# 运行测试
echo "🧪 运行连接测试..."
python test_tweet_functions.py

echo ""
echo "🎉 更新完成！"
echo ""
echo "📋 下一步："
echo "1. 在Twitter Developer Portal获取Bearer Token"
echo "2. 更新Claude Desktop配置，添加TWITTER_BEARER_TOKEN"
echo "3. 重启Claude Desktop"
echo "4. 在Claude中运行'测试API连接'验证配置"
echo ""
echo "📚 详细配置指南："
echo "- OAuth双重认证配置指南.md"
echo "- README_CN.md"
echo ""
echo "🔧 如果遇到问题："
echo "- 运行 'python test_tweet_functions.py' 进行诊断"
echo "- 查看 '推文获取功能故障排除指南.md'"
echo "- 在Claude中运行 '测试API连接'"