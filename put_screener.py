#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美股卖出Put期权筛选系统 - GitHub Actions 版本
每天晚上自动推送Excel文件到企业微信
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import os
import sys
import json

# ==================== 配置区域 ====================
# 从环境变量读取 Webhook 地址
WECHAT_WEBHOOK = os.environ.get('WECHAT_WEBHOOK', '')

# 标的列表
tickers = ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "GOOGL", "AMZN", 
           "TSLA", "NVDA", "META", "AMD", "NFLX", "BABA", "COIN", "PLTR"]

stock_names = {
    "SPY": "SPDR S&P 500 ETF",
    "QQQ": "Invesco QQQ ETF", 
    "IWM": "iShares Russell 2000 ETF",
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corp.",
    "GOOGL": "Alphabet Inc.",
    "AMZN": "Amazon.com Inc.",
    "TSLA": "Tesla Inc.",
    "NVDA": "NVIDIA Corp.",
    "META": "Meta Platforms Inc.",
    "AMD": "Advanced Micro Devices",
    "NFLX": "Netflix Inc.",
    "BABA": "Alibaba Group",
    "COIN": "Coinbase Global Inc.",
    "PLTR": "Palantir Technologies"
}

# ==================== 核心函数 ====================

def calculate_monthly_yield(option_price, strike_price, days_to_expiration):
    """计算卖出Put的月度收益率"""
    if strike_price == 0 or days_to_expiration <= 0:
        return 0
    base_yield = (option_price / strike_price) * 100
    monthly_yield = base_yield * (30 / days_to_expiration)
    return monthly_yield

def filter_put_options(puts_df, stock_price, stock_symbol, expiration_date, min_yield=6.0):
    """筛选月度收益率大于指定值的put期权"""
    results = []
    
    exp_date = datetime.strptime(expiration_date, "%Y-%m-%d")
    today = datetime.now()
    days_to_expiration = (exp_date - today).days
    
    if days_to_expiration <= 0:
        return results
    
    for _, row in puts_df.iterrows():
        strike = row['strike']
        
        if strike < stock_price * 0.85 or strike > stock_price * 1.05:
            continue
        
        option_price = row['lastPrice']
        if pd.isna(option_price) or option_price <= 0:
            continue
        
        monthly_yield = calculate_monthly_yield(option_price, strike, days_to_expiration)
        
        if monthly_yield >= min_yield:
            results.append({
                '股票代码': stock_symbol,
                '股票名称': stock_names.get(stock_symbol, stock_symbol),
                '到期日': expiration_date,
                '行权价': strike,
                '期权价格': option_price,
                '股票现价': stock_price,
                '距离到期(天)': days_to_expiration,
                '月度收益率': round(monthly_yield, 2),
                '期权代码': row['contractSymbol']
            })
    
    results.sort(key=lambda x: x['月度收益率'], reverse=True)
    return results

def generate_excel(results, output_path):
    """生成带样式的Excel文件"""
    if not results:
        print("⚠️  没有找到符合条件的期权")
        return None
    
    df = pd.DataFrame(results)
    df = df.sort_values('月度收益率', ascending=False)
    
    df_export = df[['股票代码', '股票名称', '到期日', '股票现价', '行权价', '期权价格', 
                     '月度收益率', '距离到期(天)']].copy()
    
    df_export.columns = ['股票代码', '股票名称', '到期日', '股票现价($)', '行权价($)', 
                         '期权价格($)', '月度收益率(%)', '距离到期(天)']
    
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        df_export.to_excel(writer, sheet_name='卖出Put期权筛选', index=False, startrow=3, startcol=1)
        
        workbook = writer.book
        worksheet = writer.sheets['卖出Put期权筛选']
        
        # 隐藏网格线
        worksheet.hide_gridlines(2)
        
        # 格式定义
        title_format = workbook.add_format({
            'bold': True, 'font_size': 16, 'font_color': '#1F4E79',
            'align': 'center', 'valign': 'vcenter'
        })
        subtitle_format = workbook.add_format({
            'font_size': 10, 'font_color': '#666666', 'align': 'center', 'valign': 'vcenter'
        })
        header_format = workbook.add_format({
            'bold': True, 'font_size': 11, 'font_color': 'white', 
            'bg_color': '#1F4E79', 'align': 'center', 'valign': 'vcenter', 'border': 1
        })
        data_format = workbook.add_format({
            'align': 'center', 'valign': 'vcenter', 'font_size': 10
        })
        yield_format = workbook.add_format({
            'bold': True, 'font_color': '#008000', 'align': 'center', 'valign': 'vcenter'
        })
        currency_format = workbook.add_format({
            'num_format': '$#,##0.00', 'align': 'center', 'valign': 'vcenter', 'font_size': 10
        })
        
        # 标题
        worksheet.merge_range('B2:I2', '美股卖出Put期权筛选清单', title_format)
        worksheet.set_row(1, 30)
        
        # 副标题
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        worksheet.merge_range('B3:I3', 
            f'筛选条件：月度收益率 ≥ 6% | 数据更新时间：{now_str}', 
            subtitle_format)
        
        # 表头
        for col_num, value in enumerate(df_export.columns.values):
            worksheet.write(3, col_num + 1, value, header_format)
        
        # 数据行
        for row_num in range(len(df_export)):
            for col_num in range(len(df_export.columns)):
                value = df_export.iloc[row_num, col_num]
                row = 4 + row_num
                col = col_num + 1
                
                if col_num in [3, 4, 5]:  # 价格列
                    worksheet.write(row, col, value, currency_format)
                elif col_num == 6:  # 月度收益率
                    worksheet.write(row, col, value, yield_format)
                else:
                    worksheet.write(row, col, value, data_format)
        
        # 设置列宽
        worksheet.set_column('A:A', 3)
        worksheet.set_column('B:B', 10)
        worksheet.set_column('C:C', 26)
        worksheet.set_column('D:D', 12)
        worksheet.set_column('E:G', 12)
        worksheet.set_column('H:H', 14)
        worksheet.set_column('I:I', 12)
    
    print(f"✅ Excel已生成: {output_path}")
    return output_path

def upload_file_to_wecom(file_path, webhook_url):
    """上传文件到企业微信，获取 media_id"""
    if not webhook_url or "xxxx" in webhook_url:
        print("⚠️  Webhook 地址未配置")
        return None
    
    # 提取 key 参数
    import re
    key_match = re.search(r'key=([^&]+)', webhook_url)
    if not key_match:
        print("❌ Webhook 地址格式错误")
        return None
    
    key = key_match.group(1)
    upload_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media?key={key}&type=file"
    
    try:
        with open(file_path, 'rb') as f:
            files = {'media': (os.path.basename(file_path), f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post(upload_url, files=files, timeout=30)
            result = response.json()
            
            if result.get("errcode") == 0:
                media_id = result.get("media_id")
                print(f"✅ 文件上传成功")
                return media_id
            else:
                print(f"❌ 上传失败: {result.get('errmsg')}")
                return None
    except Exception as e:
        print(f"❌ 上传异常: {e}")
        return None

def send_file_to_wecom(media_id, webhook_url):
    """发送文件消息到企业微信"""
    data = {
        "msgtype": "file",
        "file": {
            "media_id": media_id
        }
    }
    
    try:
        response = requests.post(webhook_url, json=data, timeout=10)
        result = response.json()
        
        if result.get("errcode") == 0:
            print(f"✅ 文件推送成功！")
            return True
        else:
            print(f"❌ 推送失败: {result.get('errmsg')}")
            return False
    except Exception as e:
        print(f"❌ 推送异常: {e}")
        return False

def send_text_to_wecom(content, webhook_url):
    """发送文本消息到企业微信"""
    data = {
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }
    
    try:
        response = requests.post(webhook_url, json=data, timeout=10)
        result = response.json()
        
        if result.get("errcode") == 0:
            print(f"✅ 文本推送成功！")
            return True
        else:
            print(f"❌ 推送失败: {result.get('errmsg')}")
            return False
    except Exception as e:
        print(f"❌ 推送异常: {e}")
        return False

def format_summary(results):
    """格式化文本摘要"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    content = f"""## 📊 美股卖出Put期权筛选结果

**更新时间**: {now}  
**筛选条件**: 月度收益率 ≥ 6% | 月末到期  
**共找到**: {len(results)} 个符合条件的期权

### 📋 收益率TOP 10

| 股票 | 到期日 | 行权价 | 期权价 | 收益率 |
|------|--------|--------|--------|--------|
"""
    
    for item in results[:10]:
        content += f"| **{item['股票代码']}** | {item['到期日']} | ${item['行权价']:.0f} | ${item['期权价格']:.2f} | **{item['月度收益率']:.2f}%** |\n"
    
    content += f"""
> ⚠️ **风险提示**：卖出Put期权有本金亏损风险，请谨慎投资
> 
> 📎 **详细数据请查看附件 Excel 文件**
"""
    
    return content

def send_to_wecom(file_path, results, webhook_url):
    """完整推送流程：先发送文本摘要，再发送文件"""
    # 1. 发送文本摘要
    print("\n📤 正在发送文本摘要...")
    summary = format_summary(results)
    send_text_to_wecom(summary, webhook_url)
    
    # 2. 上传文件
    print("\n📤 正在上传Excel文件...")
    media_id = upload_file_to_wecom(file_path, webhook_url)
    
    if media_id:
        # 3. 发送文件
        print("\n📤 正在发送文件...")
        send_file_to_wecom(media_id, webhook_url)
    else:
        print("❌ 文件上传失败，仅发送了文本摘要")

# ==================== 模拟数据（演示用）====================

def get_sample_results():
    """获取模拟筛选结果（实际使用时替换为真实数据获取）"""
    return [
        {'股票代码': 'COIN', '股票名称': 'Coinbase Global Inc.', '到期日': '2026-03-27', 
         '行权价': 170.0, '期权价格': 16.90, '股票现价': 162.03, '月度收益率': 10.28, 
         '期权代码': 'COIN260327P00170000'},
        {'股票代码': 'COIN', '股票名称': 'Coinbase Global Inc.', '到期日': '2026-03-27', 
         '行权价': 165.0, '期权价格': 14.67, '股票现价': 162.03, '月度收益率': 9.20, 
         '期权代码': 'COIN260327P00165000'},
        {'股票代码': 'PLTR', '股票名称': 'Palantir Technologies', '到期日': '2026-03-27', 
         '行权价': 135.0, '期权价格': 11.60, '股票现价': 128.84, '月度收益率': 8.89, 
         '期权代码': 'PLTR260327P00135000'},
        {'股票代码': 'AMD', '股票名称': 'Advanced Micro Devices', '到期日': '2026-03-27', 
         '行权价': 220.0, '期权价格': 17.20, '股票现价': 213.84, '月度收益率': 8.09, 
         '期权代码': 'AMD260327P00220000'},
        {'股票代码': 'NVDA', '股票名称': 'NVIDIA Corp.', '到期日': '2026-03-27', 
         '行权价': 200.0, '期权价格': 14.60, '股票现价': 192.85, '月度收益率': 7.55, 
         '期权代码': 'NVDA260327P00200000'},
        {'股票代码': 'COIN', '股票名称': 'Coinbase Global Inc.', '到期日': '2026-03-27', 
         '行权价': 160.0, '期权价格': 11.60, '股票现价': 162.03, '月度收益率': 7.50, 
         '期权代码': 'COIN260327P00160000'},
        {'股票代码': 'COIN', '股票名称': 'Coinbase Global Inc.', '到期日': '2026-03-27', 
         '行权价': 155.0, '期权价格': 11.00, '股票现价': 162.03, '月度收益率': 7.34, 
         '期权代码': 'COIN260327P00155000'},
        {'股票代码': 'PLTR', '股票名称': 'Palantir Technologies', '到期日': '2026-03-27', 
         '行权价': 130.0, '期权价格': 8.85, '股票现价': 128.84, '月度收益率': 7.04, 
         '期权代码': 'PLTR260327P00130000'},
        {'股票代码': 'AMD', '股票名称': 'Advanced Micro Devices', '到期日': '2026-03-27', 
         '行权价': 215.0, '期权价格': 14.53, '股票现价': 213.84, '月度收益率': 6.99, 
         '期权代码': 'AMD260327P00215000'},
        {'股票代码': 'TSLA', '股票名称': 'Tesla Inc.', '到期日': '2026-03-27', 
         '行权价': 425.0, '期权价格': 27.20, '股票现价': 409.38, '月度收益率': 6.62, 
         '期权代码': 'TSLA260327P00425000'},
        {'股票代码': 'NVDA', '股票名称': 'NVIDIA Corp.', '到期日': '2026-03-27', 
         '行权价': 195.0, '期权价格': 11.45, '股票现价': 192.85, '月度收益率': 6.07, 
         '期权代码': 'NVDA260327P00195000'},
        {'股票代码': 'AMD', '股票名称': 'Advanced Micro Devices', '到期日': '2026-03-27', 
         '行权价': 210.0, '期权价格': 12.25, '股票现价': 213.84, '月度收益率': 6.03, 
         '期权代码': 'AMD260327P00210000'},
    ]

# ==================== 主程序 ====================

def main():
    """主函数 - 运行筛选、生成Excel、推送到企业微信"""
    print(f"\n{'='*60}")
    print(f"📊 美股卖出Put期权筛选系统 - GitHub Actions")
    print(f"⏰ 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # 检查 Webhook 配置
    if not WECHAT_WEBHOOK:
        print("❌ 错误：WECHAT_WEBHOOK 环境变量未设置")
        print("   请在 GitHub Secrets 中设置 WECHAT_WEBHOOK")
        sys.exit(1)
    
    # 获取筛选结果（当前使用模拟数据）
    # TODO: 接入真实数据源（Yahoo Finance API）
    sample_results = get_sample_results()
    
    # 设置输出路径
    date_str = datetime.now().strftime('%Y%m%d')
    excel_path = f"put_options_{date_str}.xlsx"
    
    # 生成Excel
    excel_path = generate_excel(sample_results, excel_path)
    
    if not excel_path:
        print("❌ Excel生成失败")
        sys.exit(1)
    
    # 推送到企业微信
    send_to_wecom(excel_path, sample_results, WECHAT_WEBHOOK)
    
    print(f"\n{'='*60}")
    print("✅ 运行完成")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
