#!/usr/bin/env python3
"""
测试推文获取功能的独立脚本 - 支持OAuth 1.0a和OAuth 2.0双重认证
用于诊断API连接和权限问题

使用方法：
1. 确保你的Claude MCP配置正确
2. 在Claude中直接测试推文获取功能
3. 或者手动设置环境变量后运行此脚本

手动测试环境变量设置：
export TWITTER_API_KEY="your_key"
export TWITTER_API_SECRET="your_secret"  
export TWITTER_ACCESS_TOKEN="your_token"
export TWITTER_ACCESS_TOKEN_SECRET="your_token_secret"
export TWITTER_BEARER_TOKEN="your_bearer_token"  # 可选，用于OAuth 2.0
"""

import os
import tweepy
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取API凭据
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

def test_credentials():
    """测试API凭据是否正确配置"""
    print("=== 测试API凭据 ===")
    
    if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
        print("❌ 错误：缺少必要的API凭据")
        print("请确保设置了以下环境变量：")
        print("- TWITTER_API_KEY")
        print("- TWITTER_API_SECRET") 
        print("- TWITTER_ACCESS_TOKEN")
        print("- TWITTER_ACCESS_TOKEN_SECRET")
        return False
    
    print("✅ 所有API凭据都已设置")
    return True

def test_oauth1_connection():
    """测试OAuth 1.0a客户端连接"""
    print("\n=== 测试OAuth 1.0a客户端连接 ===")
    
    try:
        oauth1_client = tweepy.Client(
            consumer_key=API_KEY,
            consumer_secret=API_SECRET,
            access_token=ACCESS_TOKEN,
            access_token_secret=ACCESS_TOKEN_SECRET
        )
        
        # 测试获取自己的用户信息
        me = oauth1_client.get_me()
        print(f"✅ OAuth 1.0a 连接成功！当前用户：{me.data.name} (@{me.data.username})")
        return oauth1_client
        
    except Exception as e:
        print(f"❌ OAuth 1.0a 连接失败：{e}")
        return None

def test_oauth2_connection():
    """测试OAuth 2.0客户端连接"""
    print("\n=== 测试OAuth 2.0客户端连接 ===")
    
    if not BEARER_TOKEN:
        print("⚠️ 未设置TWITTER_BEARER_TOKEN，跳过OAuth 2.0测试")
        return None
    
    try:
        oauth2_client = tweepy.Client(bearer_token=BEARER_TOKEN)
        
        # OAuth 2.0不支持get_me()，所以我们测试搜索功能
        response = oauth2_client.search_recent_tweets(
            query="hello",
            max_results=5,
            tweet_fields=["id", "text"]
        )
        
        if response.data:
            print(f"✅ OAuth 2.0 连接成功！搜索到 {len(response.data)} 条推文")
        else:
            print("⚠️ OAuth 2.0 连接成功但搜索返回空结果")
        
        return oauth2_client
        
    except Exception as e:
        print(f"❌ OAuth 2.0 连接失败：{e}")
        return None

def get_best_read_client(oauth1_client, oauth2_client):
    """获取最佳的读取客户端"""
    if oauth2_client:
        print("📖 使用OAuth 2.0进行读取操作（推荐）")
        return oauth2_client, "OAuth 2.0"
    elif oauth1_client:
        print("📖 使用OAuth 1.0a进行读取操作（备选）")
        return oauth1_client, "OAuth 1.0a"
    else:
        return None, "无可用客户端"

def test_get_tweet(client, client_type, tweet_id="1234567890123456789"):
    """测试获取单条推文"""
    print(f"\n=== 测试获取推文 {tweet_id} (使用{client_type}) ===")
    
    try:
        response = client.get_tweet(
            id=tweet_id,
            tweet_fields=["id", "text", "created_at", "author_id", "lang"],
            user_fields=["id", "name", "username", "verified"],
            expansions=["author_id"]
        )
        
        if response.data:
            tweet = response.data
            print(f"✅ 成功获取推文：{tweet.text[:50]}...")
            return True
        else:
            print("❌ 推文不存在或无法访问")
            return False
            
    except tweepy.TweepyException as e:
        print(f"❌ Twitter API错误：{e}")
        if "401" in str(e):
            print("   可能原因：认证失败，检查API凭据")
        elif "403" in str(e):
            print("   可能原因：权限不足或推文受保护")
        elif "404" in str(e):
            print("   可能原因：推文不存在或已删除")
        return False
    except Exception as e:
        print(f"❌ 其他错误：{e}")
        return False

def test_search_tweets(client, client_type, query="AI"):
    """测试搜索推文"""
    print(f"\n=== 测试搜索推文 '{query}' (使用{client_type}) ===")
    
    try:
        response = client.search_recent_tweets(
            query=query,
            max_results=5,
            tweet_fields=["id", "text", "created_at", "author_id", "lang"],
            user_fields=["id", "name", "username"],
            expansions=["author_id"]
        )
        
        if response.data:
            print(f"✅ 搜索成功！找到 {len(response.data)} 条推文")
            for i, tweet in enumerate(response.data[:2], 1):
                print(f"  {i}. {tweet.text[:50]}...")
            return True
        else:
            print("❌ 没有找到相关推文")
            return False
            
    except tweepy.TweepyException as e:
        print(f"❌ Twitter API错误：{e}")
        if "401" in str(e):
            print("   可能原因：认证失败，检查API凭据")
        elif "403" in str(e):
            print("   可能原因：API权限不足，需要升级到付费计划")
        elif "429" in str(e):
            print("   可能原因：API调用频率限制")
        return False
    except Exception as e:
        print(f"❌ 其他错误：{e}")
        return False

def test_mcp_functionality():
    """测试MCP功能的建议"""
    print("\n=== MCP功能测试建议 ===")
    print("由于你的API凭据在Claude MCP配置中，建议直接在Claude中测试：")
    print()
    print("1. 测试搜索功能：")
    print("   '搜索包含\"hello\"的最近推文'")
    print()
    print("2. 测试获取推文（需要真实的推文ID）：")
    print("   '获取推文 1234567890123456789 的内容'")
    print()
    print("3. 测试批量获取：")
    print("   '批量获取推文 123456789, 987654321 的信息'")
    print()
    print("如果这些命令在Claude中不工作，问题可能是：")
    print("- API权限设置（需要Read权限）")
    print("- 推文ID无效或推文不存在")
    print("- API使用限制")
    print("- 网络连接问题")

def main():
    """主测试函数"""
    print("Twitter API 推文获取功能测试 - 双重认证版本")
    print("=" * 50)
    
    # 测试凭据
    if not test_credentials():
        print("\n由于没有设置环境变量，无法进行直接API测试。")
        test_mcp_functionality()
        return
    
    # 测试OAuth 1.0a连接
    oauth1_client = test_oauth1_connection()
    
    # 测试OAuth 2.0连接
    oauth2_client = test_oauth2_connection()
    
    if not oauth1_client and not oauth2_client:
        print("❌ 所有认证方式都失败了")
        return
    
    # 获取最佳读取客户端
    read_client, client_type = get_best_read_client(oauth1_client, oauth2_client)
    
    if not read_client:
        print("❌ 没有可用的读取客户端")
        return
    
    # 测试搜索功能
    search_success = test_search_tweets(read_client, client_type, "AI")
    
    # 测试获取推文（需要有效的推文ID）
    print("\n注意：获取特定推文需要有效的推文ID")
    print("你可以修改脚本中的tweet_id来测试特定推文")
    
    # 测试写入功能（如果OAuth 1.0a可用）
    if oauth1_client:
        print(f"\n=== 写入功能测试 ===")
        print("✅ OAuth 1.0a 客户端可用于写入操作")
        print("   支持：发推文、转推、回复、上传媒体")
    else:
        print(f"\n=== 写入功能测试 ===")
        print("❌ 没有可用的写入客户端（需要OAuth 1.0a）")
    
    # 总结
    print("\n=== 测试总结 ===")
    print(f"OAuth 1.0a: {'✅ 可用' if oauth1_client else '❌ 不可用'}")
    print(f"OAuth 2.0: {'✅ 可用' if oauth2_client else '❌ 不可用'}")
    print(f"读取功能: {'✅ 正常' if search_success else '❌ 异常'} (使用{client_type})")
    print(f"写入功能: {'✅ 可用' if oauth1_client else '❌ 不可用'}")
    
    if search_success:
        print("\n✅ 推文获取功能基本正常")
        print("如果在MCP中仍有问题，请检查：")
        print("1. Claude Desktop配置是否正确")
        print("2. 服务器是否正确启动")
        print("3. 网络连接是否稳定")
    else:
        print("\n❌ 推文获取功能存在问题")
        print("建议检查：")
        print("1. API权限设置")
        print("2. 账户类型（免费vs付费）")
        print("3. API使用限制")
        
    print("\n=== 配置建议 ===")
    if not oauth2_client:
        print("💡 建议添加TWITTER_BEARER_TOKEN以启用OAuth 2.0")
        print("   OAuth 2.0在读取操作上通常更稳定")
    if oauth1_client and oauth2_client:
        print("🎉 完美配置！同时支持OAuth 1.0a和OAuth 2.0")
        print("   系统将自动选择最佳认证方式")

if __name__ == "__main__":
    main()