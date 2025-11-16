#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从懂车帝页面的JavaScript数据中提取品牌列表
不需要Selenium，直接分析页面源码
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def extract_json_from_script(html):
    """从script标签中提取JSON数据"""
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script')

    extracted_data = []

    for idx, script in enumerate(scripts):
        if not script.string:
            continue

        content = script.string

        # 查找包含品牌数据的模式
        patterns = [
            # Next.js数据
            r'__NEXT_DATA__\s*=\s*({.*?})\s*;?\s*</script>',
            # 其他可能的全局变量
            r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
            r'window\.pageData\s*=\s*({.*?});',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match)
                    extracted_data.append({
                        'source': f'script_{idx}',
                        'pattern': pattern[:30],
                        'data': data
                    })
                    logger.info(f"✓ 从script {idx}提取到JSON数据")
                except:
                    continue

    return extracted_data


def find_brands_in_data(data, path=""):
    """递归查找JSON数据中的品牌信息"""
    brands = []

    if isinstance(data, dict):
        # 检查当前层是否包含品牌信息
        if 'brand' in data or 'brand_id' in data or 'brandId' in data:
            brand_id = data.get('brand_id') or data.get('brandId') or data.get('id')
            brand_name = data.get('brand') or data.get('brand_name') or data.get('name')

            if brand_id and brand_name:
                brands.append({
                    'id': str(brand_id),
                    'name': brand_name,
                    'path': path
                })

        # 查找可能包含品牌列表的字段
        for key in ['brands', 'brand_list', 'brandList', 'list', 'items', 'data']:
            if key in data and isinstance(data[key], (list, dict)):
                brands.extend(find_brands_in_data(data[key], f"{path}.{key}"))

        # 递归其他字段
        for key, value in data.items():
            if key not in ['brands', 'brand_list', 'brandList', 'list', 'items']:
                brands.extend(find_brands_in_data(value, f"{path}.{key}"))

    elif isinstance(data, list):
        for idx, item in enumerate(data):
            brands.extend(find_brands_in_data(item, f"{path}[{idx}]"))

    return brands


def fetch_and_analyze_page(url):
    """访问页面并分析"""
    logger.info(f"访问页面: {url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        logger.info(f"页面大小: {len(response.text)} 字符")

        # 提取JSON数据
        json_data = extract_json_from_script(response.text)

        logger.info(f"提取到 {len(json_data)} 个JSON对象")

        # 在JSON中查找品牌
        all_brands = []
        for item in json_data:
            brands = find_brands_in_data(item['data'])
            if brands:
                logger.info(f"  在 {item['source']} 中找到 {len(brands)} 个品牌")
                all_brands.extend(brands)

        return all_brands

    except Exception as e:
        logger.error(f"访问失败: {str(e)}")
        return []


def main():
    """主函数"""
    logger.info("="*60)
    logger.info("从懂车帝页面提取品牌数据")
    logger.info("="*60)

    # 测试多个页面
    pages = [
        'https://www.dongchedi.com/auto',
        'https://www.dongchedi.com/',
    ]

    all_brands = []

    for page_url in pages:
        brands = fetch_and_analyze_page(page_url)
        all_brands.extend(brands)

    # 去重
    unique_brands = {}
    for brand in all_brands:
        brand_id = brand['id']
        if brand_id not in unique_brands:
            unique_brands[brand_id] = brand

    logger.info(f"\n{'='*60}")
    logger.info(f"总计找到 {len(unique_brands)} 个唯一品牌")
    logger.info(f"{'='*60}")

    if unique_brands:
        # 显示前10个
        for i, (brand_id, brand) in enumerate(list(unique_brands.items())[:10], 1):
            logger.info(f"{i}. ID {brand_id}: {brand['name']}")

        # 保存结果
        with open('brands_from_page.json', 'w', encoding='utf-8') as f:
            json.dump(list(unique_brands.values()), f, indent=2, ensure_ascii=False)

        logger.info(f"\n结果已保存到 brands_from_page.json")

        # 检查是否包含大ID品牌
        large_ids = [b for b in unique_brands.values() if int(b['id']) > 1000]
        if large_ids:
            logger.info(f"\n✓ 找到 {len(large_ids)} 个大ID品牌（ID > 1000）")
            for brand in large_ids[:5]:
                logger.info(f"  - ID {brand['id']}: {brand['name']}")
        else:
            logger.warning("\n✗ 未找到大ID品牌，可能需要其他方法")

        return list(unique_brands.values())
    else:
        logger.warning("未从页面中找到品牌数据")
        return []


if __name__ == '__main__':
    brands = main()

    if brands:
        logger.info(f"\n✓ 成功提取 {len(brands)} 个品牌")
    else:
        logger.info("\n下一步：尝试直接查找API URL")
