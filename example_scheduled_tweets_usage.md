# 定时发推文使用示例

## 快速开始

### 1. 启动调度器
首先需要启动后台调度器：
```bash
start_scheduler
```

### 2. 创建定时推文

#### 10分钟后发一条推文
```bash
create_scheduled_tweet "内容：学习新技术真有趣！#编程" "+10m"
```

#### 明天上午9点发推文
```bash
create_scheduled_tweet "早安！新的一天开始了 🌅" "2024-01-16T09:00:00"
```

### 3. 创建推文串

#### 1小时后发布推文串
```bash
create_scheduled_thread ["第一条推文", "第二条推文", "第三条推文"] "+1h"
```

### 4. 循环发推文

#### 每10分钟发一条，共发3条
```bash
create_recurring_tweets ["消息1", "消息2", "消息3"] 10 "+5m" 3
```

### 5. 管理定时推文

#### 查看所有定时推文
```bash
list_scheduled_tweets
```

#### 取消定时推文
```bash
cancel_scheduled_tweet "scheduled_tweet_1704567890.json"
```

## 实际场景

### 产品发布倒计时
每小时发布一次倒计时推文：
```bash
create_recurring_tweets [
  "产品发布倒计时：还有3小时！🚀",
  "产品发布倒计时：还有2小时！⏰", 
  "产品发布倒计时：还有1小时！🎯"
] 60 "+1h" 3
```

这样就完成了定时发推文功能的添加！