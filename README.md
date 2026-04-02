# AI Pulse

AI 行业动态自动追踪系统 — RSS 聚合 → LLM 分析 → 邮件推送 → 可视化看板

每天上午 10:00 / 晚上 22:00 自动抓取过去 12 小时的 AI 行业动态，经 LLM 分析后生成结构化邮件报告。

---

## 背景与需求

### 为什么做这个

2026 年 AI 厂商更新节奏极快，几乎每天都有新模型发布、融资新闻、API 调整或开源动态。手动刷微信公众号和 X 既耗时又容易遗漏，需要一个自动化工具帮助理清每天的发展进度和最新热点。

### 核心需求

| 维度 | 需求描述 |
|------|---------|
| **数据源** | 微信特定公众号 + X 特定博主的内容聚合 |
| **重点关注** | Meta / Anthropic / OpenAI / Google / xAI / 阿里 / 字节 / MiniMax / Kimi 等主流厂商，以及各细分领域独角兽 |
| **更新频率** | 每天上午 10:00 / 晚上 22:00 各一次，梳理过去 12h 内容 |
| **输出结果** | 邮件看板：重要动态 + 推荐阅读 + 模型能力评分 + 开放程度评估 |
| **推送渠道** | Gmail 邮件 |

### 设计决策

- **微信 RSS**：用 [WeWeRSS](https://github.com/cooderl/wewe-rss) 托管在 Railway，通过微信读书 API 稳定拉取公众号内容
- **X/Twitter RSS**：先用 xcancel.com Nitter 镜像（零配置），备选方案为自建 RSSHub + auth_token
- **LLM 分析**：MiniMax-M2.5（国内版），OpenAI 兼容接口
- **模型数据**：OpenRouter `/api/v1/models` 实时拉取各厂商模型定价和能力数据
- **邮件模块布局**：重要动态 → 推荐阅读 → 模型看板（能力评分按维度分模块展示）

---

## 开发进度（v1.0）

### 已完成 ✅

| 模块 | 文件 | 说明 |
|------|------|------|
| RSS 抓取 | `src/fetcher.py` | 支持时间窗口过滤、去重、微信全文提取 |
| LLM 分析 | `src/analyzer.py` | MiniMax 分析分类：重要动态 / 推荐阅读 / 开放程度 |
| HTML 渲染 | `src/renderer.py` + `templates/email.html` | Jinja2 模板，GitHub Dark 主题，四板块布局 |
| 邮件发送 | `src/emailer.py` | Gmail SMTP，上午版/晚间版自动区分 |
| OpenRouter | `src/openrouter.py` | 实时拉取各厂商模型数据用于能力看板 |
| WeWeRSS 同步 | `src/sync.py` | 自动从 WeWeRSS API 同步订阅列表到 config.yaml |
| 主程序 | `main.py` | 完整 pipeline 串联，支持 `--dry-run` |
| 管理面板 | `dashboard.py` + `templates/dashboard/` | Flask Web UI，RSS 源管理、设置编辑、历史预览 |
| 定时任务 | `run.sh` | cron 入口脚本 |

### 数据源现状

- **微信公众号**：11 个（量子位、机器之心、42章经、数字生命卡兹克、Founder Park、葬AI、海外独角兽、InfoQ 等）
- **X/Twitter**：25 个（Sam Altman、Karpathy、Yann LeCun、Elon Musk、Demis Hassabis、Francois Chollet、李开复 等）
- **官方博客**：4 个（OpenAI / Anthropic / Google / Meta）

### 待优化 / v1.1 规划

- [ ] X 数据源切换为自建 RSSHub（xcancel 稳定性存疑）
- [ ] 邮件模板样式精调（维度模块视觉优化）
- [ ] Dashboard 定时任务可视化编辑（替代 crontab 手动操作）
- [ ] 支持更多推送渠道（Telegram Bot / 企业微信）

---

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
