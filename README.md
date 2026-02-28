# 美股卖出Put期权筛选 - GitHub Actions 部署指南

## 功能说明

- 每天晚上北京时间 **21:00** 自动运行
- 筛选月度收益率 ≥ 6% 的卖出Put期权
- 自动推送Excel文件到企业微信
- 完全免费，无需自己的服务器

---

## 部署步骤（5分钟搞定）

### 第一步：创建 GitHub 仓库

1. 访问 https://github.com
2. 登录你的账号（没有就注册一个，免费）
3. 点击右上角 **+** → **New repository**
4. 填写仓库信息：
   - **Repository name**: `put-options-screener`（随便取）
   - **Description**: 美股卖出Put期权筛选推送
   - **Public** / **Private** 都可以
5. 点击 **Create repository**

---

### 第二步：上传代码文件

在新建的仓库页面，点击 **"uploading an existing file"**

上传以下3个文件（都在本文件夹中）：

```
📁 你的仓库/
├── 📁 .github/
│   └── 📁 workflows/
│       └── screener.yml      ← 工作流配置
├── put_screener.py           ← 主程序
├── requirements.txt          ← 依赖列表
└── README.md                 ← 说明文档（可选）
```

**上传方法：**
1. 点击 **"uploading an existing file"**
2. 拖拽文件到上传区域，或点击选择文件
3. 点击 **Commit changes**

---

### 第三步：配置 Webhook 密钥

1. 在仓库页面，点击 **Settings**（设置）
2. 左侧菜单点击 **Secrets and variables** → **Actions**
3. 点击 **New repository secret**
4. 填写：
   - **Name**: `WECHAT_WEBHOOK`
   - **Secret**: `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=5eba0b2e-a3ca-4aa3-91a4-9ee9311f9835`
5. 点击 **Add secret**

```
┌─────────────────────────────────────────────┐
│  Settings → Secrets and variables → Actions │
│                                             │
│  [New repository secret]                    │
│                                             │
│  Name: WECHAT_WEBHOOK                       │
│  Secret: https://qyapi.weixin.qq.com/...    │
│                                             │
│  [Add secret]                               │
└─────────────────────────────────────────────┘
```

---

### 第四步：手动测试运行

1. 在仓库页面，点击 **Actions**
2. 点击左侧的 **"美股卖出Put期权筛选推送"**
3. 点击右侧的 **Run workflow** → **Run workflow**
4. 等待运行完成（约1-2分钟）
5. 检查企业微信群是否收到推送

```
┌─────────────────────────────────────────────┐
│  Actions                                    │
│                                             │
│  美股卖出Put期权筛选推送                    │
│  ─────────────────────────                  │
│  [Run workflow ▼]                           │
│       └── Run workflow                      │
│                                             │
│  等待状态变成 ✅ 绿色                       │
└─────────────────────────────────────────────┘
```

---

### 第五步：完成！

现在系统已经配置完成，每天晚上 **北京时间21:00** 会自动：
1. 运行期权筛选
2. 生成Excel文件
3. 推送到你的企业微信群

---

## 查看运行记录

1. 进入仓库 → **Actions**
2. 可以看到每次运行的记录
3. 点击任意一次运行，可以查看详细日志

---

## 常见问题

### Q1: 没有收到推送？

**检查清单：**
- [ ] Webhook 地址是否正确（在 Secrets 中检查）
- [ ] 企业微信群机器人是否被删除
- [ ] 查看 Actions 运行日志是否有错误

**查看日志方法：**
1. Actions → 点击失败的运行记录
2. 点击 "运行期权筛选" 查看详细日志

### Q2: 想修改运行时间？

编辑 `.github/workflows/screener.yml` 第7行：

```yaml
# 每天晚上北京时间21点 (UTC 13:00)
- cron: '0 13 * * *'

# 其他示例：
# 每天早上9点: '0 1 * * *' (UTC 1:00 = 北京时间9:00)
# 每小时运行: '0 * * * *'
# 每周一9点: '0 1 * * 1'
```

### Q3: 想手动触发运行？

1. Actions → 美股卖出Put期权筛选推送
2. Run workflow → Run workflow

### Q4: 推送内容可以自定义吗？

可以！修改 `put_screener.py` 文件：

- 修改筛选条件：搜索 `min_yield=6.0` 改为其他值
- 修改股票列表：编辑 `tickers` 列表
- 修改推送格式：编辑 `format_summary()` 函数

### Q5: 如何接入真实数据？

当前版本使用模拟数据演示。要接入真实数据，需要：

1. 在 `put_screener.py` 中添加 Yahoo Finance API 调用
2. 由于 GitHub Actions 网络限制，可能需要代理
3. 或者使用其他数据源 API

**简单方案**：使用 `yfinance` 库
```python
import yfinance as yf

# 获取期权数据
stock = yf.Ticker("AAPL")
options = stock.option_chain('2026-03-27')
puts = options.puts
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `.github/workflows/screener.yml` | GitHub Actions 工作流配置 |
| `put_screener.py` | 主程序：筛选 + 推送 |
| `requirements.txt` | Python 依赖包列表 |
| `README.md` | 本说明文档 |

---

## 费用说明

**完全免费！**
- GitHub Actions 免费额度：每月 2000 分钟
- 本脚本每次运行约 1-2 分钟
- 每天运行一次，每月约 30-60 分钟
- 远小于免费额度

---

## 技术支持

遇到问题？
1. 查看 Actions 运行日志
2. 检查 Secrets 配置是否正确
3. 确认企业微信群机器人正常

---

**🎉 部署完成后，每天晚上21点准时收到推送！**
