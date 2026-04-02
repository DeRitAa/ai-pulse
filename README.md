# AI Pulse

AI 行业动态自动追踪系统 — RSS 聚合 → LLM 分析 → 邮件推送 → 可视化看板

每天上午 10:00 / 晚上 22:00 自动抓取过去 12 小时的 AI 行业动态，经 LLM 分析后生成结构化邮件报告。

## Features

**数据聚合**
- 微信公众号 — 通过 [WeWeRSS](https://github.com/cooderl/wewe-rss) 转 RSS，支持一键同步订阅列表
- X / Twitter — 通过 [xcancel.com](https://xcancel.com) Nitter 镜像（可切换自建 RSSHub）
- 厂商官方博客 — OpenAI / Anthropic / Google / Meta 原生 RSS

**智能分析**
- MiniMax-M2.5 自动分类：重要动态 / 推荐阅读 / 开放程度评估
- 自动提取微信公众号全文（绕过 feedparser 的 HTML 清洗问题）

**模型看板**
- OpenRouter API 实时数据：模型定价、上下文长度、模态支持
- 覆盖 OpenAI / Anthropic / Google / Meta / xAI / DeepSeek / 阿里 / Mistral

**邮件推送**
- Gmail SMTP，上午版 / 晚间版自动区分
- GitHub Dark 风格 HTML 模板

**管理面板**
- Flask Web Dashboard（`localhost:5001`）
- RSS 源可视化增删改
- WeWeRSS 一键同步
- 历史邮件预览 / 手动触发运行

## Quick Start

```bash
# 1. Clone
git clone https://github.com/DeRitAa/ai-pulse.git
cd ai-pulse

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt
pip install flask requests python-dotenv openai

# 4. 配置密钥
cp .env.example .env
# 编辑 .env，填入 Gmail 应用专用密码和 MiniMax API Key

# 5. 测试运行（不发邮件）
python main.py --dry-run

# 6. 正式运行（发送邮件）
python main.py

# 7. 启动管理面板
python dashboard.py
# 打开 http://localhost:5001
```

## Configuration

编辑 `config.yaml`：

```yaml
sources:
  wechat_rss:    # 微信公众号 (WeWeRSS Atom feeds)
    - url: "https://your-wewerss.up.railway.app/feeds/MP_WXS_xxx.atom"
      name: "公众号名"
  x_rss:          # X / Twitter
    - url: "https://xcancel.com/username/rss"
      name: "@username"
  official_blogs:  # 官方博客
    - url: "https://openai.com/blog/rss.xml"
      name: "OpenAI Blog"

email:
  from_addr: "your@gmail.com"
  to_addrs:
    - "your@gmail.com"

schedule:
  times: ["10:00", "22:00"]
  timezone: "Asia/Shanghai"
  window_hours: 12

wewerss:
  base_url: "https://your-wewerss.up.railway.app"
```

## 定时任务

使用 cron 实现每日两次自动运行：

```bash
crontab -e

# 每天 10:00 和 22:00 运行（Asia/Shanghai）
0 10 * * * /path/to/ai-pulse/run.sh
0 22 * * * /path/to/ai-pulse/run.sh
```

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  WeWeRSS    │    │  xcancel    │    │ Official    │
│  (微信RSS)   │    │  (X/RSS)    │    │ Blogs RSS   │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
                   ┌──────▼──────┐
                   │  fetcher.py │  RSS 抓取 + 去重
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │ analyzer.py │  MiniMax LLM 分析
                   └──────┬──────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
       ┌──────▼──┐ ┌──────▼──┐ ┌─────▼──────┐
       │renderer │ │openrout-│ │  emailer   │
       │  .py    │ │  er.py  │ │   .py      │
       └────┬────┘ └────┬────┘ └─────┬──────┘
            │           │            │
            └───────────┼────────────┘
                        │
                 ┌──────▼──────┐
                 │  Gmail SMTP │
                 └─────────────┘
```

## Email Preview

邮件包含四个板块：

1. **重要动态** — 厂商发布 / 融资 / 安全漏洞 / 财报等重大事件
2. **推荐阅读** — 技术实践 / 行业洞察 / 深度分析类文章
3. **模型看板** — OpenRouter 实时数据（定价 / 上下文 / 模态）
4. **开放程度** — 各厂商开源 / API / 定价透明度

## Tech Stack

| Component | Tech |
|-----------|------|
| RSS 解析 | feedparser + 自定义微信 HTML 提取 |
| LLM 分析 | MiniMax-M2.5 (OpenAI-compatible API) |
| 模型数据 | OpenRouter `/api/v1/models` |
| 邮件渲染 | Jinja2 + HTML/CSS |
| 邮件发送 | Gmail SMTP (smtplib) |
| 管理面板 | Flask |
| 微信订阅 | WeWeRSS (Docker / Railway) |
| X 订阅 | xcancel.com (Nitter mirror) |

## License

MIT
