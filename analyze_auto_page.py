#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析/auto页面，查找品牌数据
"""

import requests
from bs4 import BeautifulSoup
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

print("分析 /auto 页面...")
response = requests.get('https://www.dongchedi.com/auto', headers=headers, timeout=15)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 1. 查找所有品牌链接
    print("\n1. 查找品牌链接...")
    brand_links = soup.find_all('a', href=re.compile(r'/auto/library-brand/\d+'))
    print(f"   找到 {len(brand_links)} 个品牌链接")
    
    if brand_links:
        brand_ids = set()
        for link in brand_links[:20]:
            href = link.get('href', '')
            match = re.search(r'/auto/library-brand/(\d+)', href)
            if match:
                brand_id = match.group(1)
                brand_name = link.text.strip()
                brand_ids.add(brand_id)
                print(f"     ID {brand_id}: {brand_name}")
        
        print(f"\n   总共找到 {len(brand_ids)} 个唯一品牌ID")
    
    # 2. 查找JavaScript中的JSON数据
    print("\n2. 查找JavaScript数据...")
    scripts = soup.find_all('script')
    
    for idx, script in enumerate(scripts):
        if script.string:
            content = script.string
            
            # 查找包含品牌数据的JSON
            if 'brand' in content.lower() and '{' in content:
                # 尝试提取JSON
                try:
                    # 查找可能的JSON对象
                    json_matches = re.findall(r'\{[^{}]*brand[^{}]*\}', content, re.IGNORECASE)
                    if json_matches:
                        print(f"   Script {idx}: 发现可能的品牌JSON")
                        for match in json_matches[:2]:
                            print(f"     {match[:200]}...")
                except:
                    pass
                    
                # 查找__NEXT_DATA__（Next.js的数据）
                if '__NEXT_DATA__' in content or 'window.__INITIAL_STATE__' in content:
                    print(f"   Script {idx}: 发现页面初始数据")
                    # 尝试提取和解析
                    try:
                        # 提取JSON部分
                        if '__NEXT_DATA__' in content:
                            json_start = content.find('__NEXT_DATA__') + len('__NEXT_DATA__ = ')
                            json_end = content.find('</script>', json_start)
                            json_str = content[json_start:json_end].strip()
                            if json_str.endswith(';'):
                                json_str = json_str[:-1]
                            
                            data = json.loads(json_str)
                            
                            # 递归查找品牌相关数据
                            def find_brands(obj, path=""):
                                if isinstance(obj, dict):
                                    if 'brand' in obj or 'brand_id' in obj or 'brandId' in obj:
                                        print(f"     找到品牌数据路径: {path}")
                                        print(f"     {str(obj)[:300]}...")
                                    for key, value in obj.items():
                                        find_brands(value, f"{path}.{key}")
                                elif isinstance(obj, list) and len(obj) > 0:
                                    find_brands(obj[0], f"{path}[0]")
                            
                            find_brands(data, "root")
                            
                    except Exception as e:
                        print(f"     解析失败: {e}")
    
    # 3. 查找可能的API endpoint
    print("\n3. 查找API endpoint...")
    api_patterns = [
        r'(https?://[^"\']+/api/[^"\']+brand[^"\']*)',
        r'(https?://[^"\']+/motor/[^"\']+brand[^"\']*)',
        r'(/api/[^"\']+brand[^"\']*)',
    ]
    
    for pattern in api_patterns:
        matches = re.findall(pattern, response.text, re.IGNORECASE)
        if matches:
            print(f"   Pattern: {pattern}")
            for match in set(matches)[:5]:
                print(f"     {match}")

print("\n完成")
