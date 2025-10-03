#!/usr/bin/env python3
"""
测试趋势与话题功能的脚本
Test script for trends and topics functionality
"""

import os
import json
import asyncio
from dotenv import load_dotenv
import tweepy

# Load environment variables
load_dotenv()

# Get Twitter API credentials
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

def test_credentials():
    """测试API凭据是否正确配置"""
    print("=== 测试API凭据配置 ===")
    
    missing_creds = []
    if not API_KEY:
        missing_creds.append("TWITTER_API_KEY")
    if not API_SECRET:
        missing_creds.append("TWITTER_API_SECRET")
    if not ACCESS_TOKEN:
        missing_creds.append("TWITTER_ACCESS_TOKEN")
    if not ACCESS_TOKEN_SECRET:
        missing_creds.append("TWITTER_ACCESS_TOKEN_SECRET")
    
    if missing_creds:
        print(f"❌ 缺少以下环境变量: {', '.join(missing_creds)}")
        return False
    
    print("✅ OAuth 1.0a 凭据已配置")
    
    if BEARER_TOKEN:
        print("✅ OAuth 2.0 Bearer Token 已配置")
    else:
        print("⚠️ 未配置 TWITTER_BEARER_TOKEN (可选，但推荐)")
    
    return True

def test_trends_api():
    """测试趋势API功能"""
    if not test_credentials():
        return
    
    print("\n=== 测试趋势API功能 ===")
    
    # Initialize API clients
    auth = tweepy.OAuth1UserHandler(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET
    )
    api = tweepy.API(auth, wait_on_rate_limit=True)
    
    # OAuth 1.0a client for write operations
    oauth1_client = tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET,
        wait_on_rate_limit=True
    )
    
    # OAuth 2.0 client for read operations (if available)
    oauth2_client = None
    if BEARER_TOKEN:
        try:
            oauth2_client = tweepy.Client(
                bearer_token=BEARER_TOKEN,
                wait_on_rate_limit=True
            )
        except Exception as e:
            print(f"⚠️ OAuth 2.0 客户端初始化失败: {e}")
    
    # Test 1: Get global trends
    print("\n📊 测试1: 获取全球趋势")
    try:
        trends = api.get_place_trends(id=1)  # WOEID 1 = worldwide
        if trends and trends[0].get('trends'):
            print(f"✅ 成功获取 {len(trends[0]['trends'])} 个全球趋势")
            print("前5个趋势:")
            for i, trend in enumerate(trends[0]['trends'][:5], 1):
                volume = trend.get('tweet_volume', 'N/A')
                print(f"  {i}. {trend['name']} (推文量: {volume})")
        else:
            print("❌ 未获取到全球趋势数据")
    except Exception as e:
        error_str = str(e)
        if "403" in error_str or "Forbidden" in error_str:
            print("❌ 获取全球趋势失败: 免费账户无法访问趋势API")
            print("💡 提示: 趋势功能需要付费API计划 (Basic $100/月 或 Pro $5000/月)")
        else:
            print(f"❌ 获取全球趋势失败: {e}")
    
    # Test 2: Get regional trends (US)
    print("\n🇺🇸 测试2: 获取美国趋势")
    try:
        trends = api.get_place_trends(id=23424977)  # WOEID for US
        if trends and trends[0].get('trends'):
            print(f"✅ 成功获取 {len(trends[0]['trends'])} 个美国趋势")
            location_info = trends[0].get('locations', [{}])[0]
            print(f"位置: {location_info.get('name', 'US')}")
            print("前3个趋势:")
            for i, trend in enumerate(trends[0]['trends'][:3], 1):
                volume = trend.get('tweet_volume', 'N/A')
                print(f"  {i}. {trend['name']} (推文量: {volume})")
        else:
            print("❌ 未获取到美国趋势数据")
    except Exception as e:
        error_str = str(e)
        if "403" in error_str or "Forbidden" in error_str:
            print("❌ 获取美国趋势失败: 免费账户无法访问趋势API")
            print("💡 提示: 地区趋势功能需要付费API计划")
        else:
            print(f"❌ 获取美国趋势失败: {e}")
    
    # Test 3: Get available trend locations
    print("\n🌍 测试3: 获取可用趋势位置")
    try:
        locations = api.available_trends()
        if locations:
            print(f"✅ 成功获取 {len(locations)} 个可用位置")
            
            # Group by country
            countries = {}
            for location in locations:
                country = location.get('country', 'Unknown')
                if country not in countries:
                    countries[country] = []
                countries[country].append(location['name'])
            
            print(f"覆盖 {len(countries)} 个国家/地区")
            print("部分国家示例:")
            for country in list(countries.keys())[:5]:
                city_count = len(countries[country])
                print(f"  {country}: {city_count} 个城市")
        else:
            print("❌ 未获取到可用位置数据")
    except Exception as e:
        error_str = str(e)
        if "403" in error_str or "Forbidden" in error_str:
            print("❌ 获取可用位置失败: 免费账户无法访问趋势API")
            print("💡 提示: 趋势位置查询需要付费API计划")
        else:
            print(f"❌ 获取可用位置失败: {e}")
    
    # Test 4: Search for topic details
    print("\n🔍 测试4: 搜索话题详情")
    read_client = oauth2_client if oauth2_client else oauth1_client
    client_type = "OAuth 2.0" if read_client == oauth2_client else "OAuth 1.0a"
    print(f"使用 {client_type} 客户端进行搜索")
    
    try:
        response = read_client.search_recent_tweets(
            query="AI -is:retweet",
            max_results=10,
            tweet_fields=["id", "text", "public_metrics", "created_at", "entities"],
            user_fields=["id", "name", "username"],
            expansions=["author_id"]
        )
        
        if response.data:
            print(f"✅ 成功搜索到 {len(response.data)} 条关于 'AI' 的推文")
            
            # Analyze hashtags
            hashtags = {}
            total_engagement = 0
            
            for tweet in response.data:
                if tweet.public_metrics:
                    engagement = (tweet.public_metrics.get('like_count', 0) + 
                                tweet.public_metrics.get('retweet_count', 0) + 
                                tweet.public_metrics.get('reply_count', 0))
                    total_engagement += engagement
                
                if hasattr(tweet, 'entities') and tweet.entities and tweet.entities.get('hashtags'):
                    for hashtag in tweet.entities['hashtags']:
                        tag = hashtag['tag'].lower()
                        hashtags[tag] = hashtags.get(tag, 0) + 1
            
            print(f"总参与度: {total_engagement}")
            print(f"平均参与度: {total_engagement / len(response.data):.1f}")
            
            if hashtags:
                print("相关标签:")
                sorted_hashtags = sorted(hashtags.items(), key=lambda x: x[1], reverse=True)
                for tag, count in sorted_hashtags[:5]:
                    print(f"  #{tag}: {count} 次")
            else:
                print("未发现相关标签")
        else:
            print("❌ 未搜索到相关推文")
    except Exception as e:
        error_str = str(e)
        if "403" in error_str or "Forbidden" in error_str:
            print("❌ 搜索话题详情失败: API访问被拒绝")
            print("💡 提示: 免费账户搜索功能有严格限制，建议升级API计划")
        elif "429" in error_str:
            print("❌ 搜索话题详情失败: 已达到免费账户调用限制")
            print("💡 提示: 免费账户每月调用次数很少，请等待下月重置或升级计划")
        else:
            print(f"❌ 搜索话题详情失败: {e}")
    
    # Test 5: Test rate limits and API access
    print("\n⚡ 测试5: API访问状态")
    try:
        # Check rate limit status for trends
        rate_limit = api.get_rate_limit_status()
        trends_limit = rate_limit['resources']['trends']['/trends/place']
        
        print(f"趋势API限制:")
        print(f"  剩余调用次数: {trends_limit['remaining']}/{trends_limit['limit']}")
        print(f"  重置时间: {trends_limit['reset']}")
        
        if trends_limit['remaining'] > 0:
            print("✅ 趋势API调用次数充足")
        else:
            print("⚠️ 趋势API调用次数已用完，需要等待重置")
            
    except Exception as e:
        print(f"⚠️ 无法获取API限制状态: {e}")

def main():
    """主测试函数"""
    print("🚀 开始测试趋势与话题功能")
    print("=" * 50)
    
    test_trends_api()
    
    print("\n" + "=" * 50)
    print("✅ 测试完成！")
    print("\n💡 免费账户限制说明:")
    print("❌ 免费账户无法使用: 全球趋势、地区趋势、趋势位置查询")
    print("✅ 免费账户可以使用: 话题搜索、标签搜索（有严格限制）")
    print("⚠️ 免费账户限制: 仅7天历史数据，月调用次数很少")
    print("\n💰 升级建议:")
    print("• Basic计划 ($100/月): 完整趋势功能 + 30天历史")
    print("• Pro计划 ($5000/月): 企业级功能 + 完整历史")
    print("\n🔧 技术建议:")
    print("1. 配置Bearer Token以提高搜索功能稳定性")
    print("2. 趋势数据每15分钟更新一次")
    print("3. 合理安排API调用频率以避免限制")

if __name__ == "__main__":
    main()