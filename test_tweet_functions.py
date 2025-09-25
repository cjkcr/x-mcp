#!/usr/bin/env python3
"""
测试推文获取功能的独立脚本
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

def test_client_connection():
    """测试客户端连接"""
    print("\n=== 测试客户端连接 ===")
    
    try:
        client = tweepy.Client(
            consumer_key=API_KEY,
            consumer_secret=API_SECRET,
            access_token=ACCESS_TOKEN,
            access_token_secret=ACCESS_TOKEN_SECRET
        )
        
        # 测试获取自己的用户信息
        me = client.get_me()
        print(f"✅ 连接成功！当前用户：{me.data.name} (@{me.data.username})")
        return client
        
    except Exception as e:
        print(f"❌ 连接失败：{e}")
        return None

def test_get_tweet(client, tweet_id="1234567890123456789"):
    """测试获取单条推文"""
    print(f"\n=== 测试获取推文 {tweet_id} ===")
    
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
        return False
    except Exception as e:
        print(f"❌ 其他错误：{e}")
        return False

def test_search_tweets(client, query="python"):
    """测试搜索推文"""
    print(f"\n=== 测试搜索推文 '{query}' ===")
    
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
        if "403" in str(e):
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
    print("Twitter API 推文获取功能测试")
    print("=" * 40)
    
    # 测试凭据
    if not test_credentials():
        print("\n由于没有设置环境变量，无法进行直接API测试。")
        test_mcp_functionality()
        return
    
    # 测试连接
    client = test_client_connection()
    if not client:
        return
    
    # 测试搜索功能（最容易测试的功能）
    search_success = test_search_tweets(client, "AI")
    
    # 测试获取推文（需要有效的推文ID）
    print("\n注意：获取特定推文需要有效的推文ID")
    print("你可以修改脚本中的tweet_id来测试特定推文")
    
    # 总结
    print("\n=== 测试总结 ===")
    if search_success:
        print("✅ 推文获取功能基本正常")
        print("如果在MCP中仍有问题，请检查：")
        print("1. Claude Desktop配置是否正确")
        print("2. 服务器是否正确启动")
        print("3. 网络连接是否稳定")
    else:
        print("❌ 推文获取功能存在问题")
        print("建议检查：")
        print("1. API权限设置")
        print("2. 账户类型（免费vs付费）")
        print("3. API使用限制")

if __name__ == "__main__":
    main()