#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探测懂车帝可能的API端点
"""

import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.dongchedi.com/',
}

# 常见的API模式
api_patterns = [
    # 品牌相关
    'https://www.dongchedi.com/motor/pc/car/brand_model_list',
    'https://www.dongchedi.com/motor/brand/list',
    'https://www.dongchedi.com/api/motor/brand/list',
    'https://www.dongchedi.com/motor/pc/brand/list',
    'https://www.dongchedi.com/motor/pc/brand/all',
    
    # 筛选相关
    'https://www.dongchedi.com/motor/pc/car/filter/brand',
    'https://www.dongchedi.com/motor/filter/brand',
    'https://www.dongchedi.com/api/filter/brand',
    
    # 车型库相关
    'https://www.dongchedi.com/motor/pc/library/brand',
    'https://www.dongchedi.com/api/library/brand',
    
    # 通用数据
    'https://www.dongchedi.com/motor/pc/car/brand',
    'https://www.dongchedi.com/motor/pc/brand',
]

print("探测API端点...")
print("="*60)

working_apis = []

for api_url in api_patterns:
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        status = response.status_code
        
        print(f"{api_url}")
        print(f"  Status: {status}")
        
        if status == 200:
            content_type = response.headers.get('Content-Type', '')
            print(f"  Content-Type: {content_type}")
            
            # 尝试解析JSON
            if 'json' in content_type:
                try:
                    data = response.json()
                    print(f"  ✓ JSON响应，大小: {len(json.dumps(data))} 字符")
                    
                    # 检查是否包含品牌数据
                    data_str = json.dumps(data).lower()
                    if 'brand' in data_str:
                        print(f"  ⭐ 包含'brand'关键词")
                        working_apis.append(api_url)
                        
                        # 保存响应
                        filename = api_url.split('/')[-1] + '.json'
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        print(f"  💾 已保存到 {filename}")
                        
                except:
                    print(f"  ✗ 非JSON或解析失败")
            else:
                print(f"  - 非JSON响应，大小: {len(response.text)}")
        
        print()
        
    except requests.exceptions.Timeout:
        print(f"  ✗ 超时")
        print()
    except Exception as e:
        print(f"  ✗ 错误: {str(e)}")
        print()

print("="*60)
print(f"发现 {len(working_apis)} 个有效API：")
for api in working_apis:
    print(f"  - {api}")
