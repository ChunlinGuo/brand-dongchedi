#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Selenium监控网络请求，找到品牌列表API
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def setup_driver():
    """配置Chrome driver并启用网络监控"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')

    # 启用性能日志以捕获网络请求
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def get_network_logs(driver):
    """获取并解析网络日志"""
    logs = driver.get_log('performance')

    network_requests = []
    for log in logs:
        try:
            message = json.loads(log['message'])
            method = message['message']['method']

            # 只关注网络请求
            if method == 'Network.requestWillBeSent':
                request = message['message']['params']['request']
                url = request['url']
                network_requests.append({
                    'url': url,
                    'method': request.get('method', 'GET'),
                })

            # 捕获响应
            elif method == 'Network.responseReceived':
                response = message['message']['params']['response']
                url = response['url']
                mime_type = response.get('mimeType', '')

                # 重点关注JSON响应
                if 'json' in mime_type or 'application/json' in mime_type:
                    network_requests.append({
                        'url': url,
                        'type': 'response',
                        'mimeType': mime_type,
                        'status': response.get('status')
                    })

        except Exception as e:
            continue

    return network_requests


def find_brand_api():
    """主函数：访问页面并找到品牌API"""
    driver = None

    try:
        logger.info("启动Chrome浏览器...")
        driver = setup_driver()

        # 尝试访问几个可能包含品牌筛选的页面
        pages_to_test = [
            'https://www.dongchedi.com/auto',
            'https://www.dongchedi.com/auto/x-x-x-x-x',
        ]

        all_api_candidates = []

        for page_url in pages_to_test:
            logger.info(f"\n访问页面: {page_url}")
            driver.get(page_url)

            # 等待页面加载
            time.sleep(5)

            # 获取网络请求
            requests = get_network_logs(driver)

            logger.info(f"捕获到 {len(requests)} 个网络请求")

            # 筛选可能是品牌API的请求
            for req in requests:
                url = req.get('url', '')

                # 查找包含brand关键词的API
                if any(keyword in url.lower() for keyword in ['brand', 'library', 'filter', 'series', 'model']):
                    if any(pattern in url for pattern in ['/api/', '/motor/', '.json']):
                        all_api_candidates.append(req)
                        logger.info(f"  ⭐ 候选API: {url}")

        # 输出所有候选API
        logger.info(f"\n\n{'='*60}")
        logger.info(f"发现 {len(all_api_candidates)} 个候选API")
        logger.info(f"{'='*60}")

        # 去重并显示
        unique_urls = list(set([req['url'] for req in all_api_candidates]))
        for i, url in enumerate(unique_urls, 1):
            logger.info(f"{i}. {url}")

        # 保存结果
        with open('api_candidates.json', 'w', encoding='utf-8') as f:
            json.dump({
                'total': len(unique_urls),
                'apis': unique_urls
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"\n结果已保存到 api_candidates.json")

        return unique_urls

    except Exception as e:
        logger.error(f"执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

    finally:
        if driver:
            driver.quit()


if __name__ == '__main__':
    logger.info("开始寻找品牌列表API...")
    apis = find_brand_api()

    if apis:
        logger.info(f"\n✓ 成功！找到 {len(apis)} 个候选API")
        logger.info("下一步：分析这些API并提取品牌数据")
    else:
        logger.warning("\n✗ 未找到明显的品牌API")
        logger.info("建议：尝试备用方案（从页面筛选器提取）")
