#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探索懂车帝品牌数据的真实来源
"""

import requests
from bs4 import BeautifulSoup
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

print("="*60)
print("探索懂车帝品牌数据来源")
print("="*60)

# 尝试1: 访问首页，查找品牌相关的JavaScript数据
print("\n1. 访问首页...")
try:
    response = requests.get('https://www.dongchedi.com/', headers=headers, timeout=10)
    if response.status_code == 200:
        print(f"   ✓ 状态码: {response.status_code}")
        
        # 查找可能包含品牌数据的script标签
        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all('script')
        
        for script in scripts:
            if script.string and 'brand' in script.string.lower():
                content = script.string[:500]
                print(f"   发现包含'brand'的script: {content}...")
                
except Exception as e:
    print(f"   ✗ 失败: {e}")

# 尝试2: 访问车型库页面
print("\n2. 尝试车型库页面...")
urls_to_try = [
    'https://www.dongchedi.com/auto/library',
    'https://www.dongchedi.com/auto',
    'https://www.dongchedi.com/motor/pc/car/brand_model_list',
]

for url in urls_to_try:
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   {url}: {response.status_code}")
        
        if response.status_code == 200:
            # 查找品牌链接
            soup = BeautifulSoup(response.text, 'html.parser')
            brand_links = soup.find_all('a', href=re.compile(r'/auto/library-brand/\d+'))
            if brand_links:
                print(f"   ✓ 找到 {len(brand_links)} 个品牌链接")
                for link in brand_links[:5]:
                    print(f"     - {link.get('href')}: {link.text}")
                    
    except Exception as e:
        print(f"   ✗ {url}: {e}")

# 尝试3: 检查已知品牌ID的分布
print("\n3. 检查品牌ID分布规律...")
test_ids = [1, 10, 100, 1000, 5000, 10000, 10293, 10500, 11000, 15000, 20000]

valid_ids = []
for brand_id in test_ids:
    try:
        url = f"https://www.dongchedi.com/auto/library-brand/{brand_id}"
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('title')
            if title and '汽车报价大全' not in title.text:
                brand_name = title.text.split('_')[0]
                valid_ids.append(brand_id)
                print(f"   ✓ ID {brand_id}: {brand_name}")
            else:
                print(f"   - ID {brand_id}: 占位符")
        else:
            print(f"   - ID {brand_id}: {response.status_code}")
            
    except Exception as e:
        print(f"   ✗ ID {brand_id}: {e}")

print(f"\n有效ID样本: {valid_ids}")
if len(valid_ids) >= 2:
    print(f"ID跨度: {min(valid_ids)} - {max(valid_ids)}")

print("\n" + "="*60)
print("探索完成")
print("="*60)
