#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：探测懂车帝的API和页面结构
"""

import requests
import json
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

print("=" * 60)
print("测试1: 尝试访问品牌详情页")
print("=" * 60)

test_ids = [3, 4, 9, 12, 16]
for brand_id in test_ids:
    url = f"https://www.dongchedi.com/auto/library-brand/{brand_id}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"\nID {brand_id}: Status {response.status_code}")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('title')
            if title:
                print(f"  Title: {title.text}")

            # 查找可能包含品牌名的元素
            h1 = soup.find('h1')
            if h1:
                print(f"  H1: {h1.text}")

    except Exception as e:
        print(f"  Error: {str(e)}")

print("\n" + "=" * 60)
print("测试2: 尝试访问选车页面")
print("=" * 60)

url = "https://www.dongchedi.com/auto/x-x-x-x-x"
try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"页面长度: {len(response.text)} 字符")
        # 查找可能的品牌链接
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=lambda x: x and 'library-brand' in x)
        print(f"找到 {len(links)} 个品牌链接")
        for link in links[:5]:
            print(f"  {link.get('href')} - {link.text}")
except Exception as e:
    print(f"Error: {str(e)}")

print("\n" + "=" * 60)
print("测试3: 尝试API端点")
print("=" * 60)

api_urls = [
    "https://www.dongchedi.com/motor/pc/car/brand_model_new",
    "https://www.dongchedi.com/motor/pc/car/brand/select_series_v2",
    "https://www.dongchedi.com/api/motor/pc/car/brand_model_new",
]

for api_url in api_urls:
    print(f"\nTrying: {api_url}")
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  JSON响应: {json.dumps(data, ensure_ascii=False)[:200]}")
            except:
                print(f"  非JSON响应，长度: {len(response.text)}")
    except Exception as e:
        print(f"  Error: {str(e)}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
