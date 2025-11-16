#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
懂车帝品牌数据爬虫 - Selenium版本
使用Selenium处理前端渲染的页面
"""

import time
import csv
import re
import logging
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DongchediSeleniumScraper:
    """懂车帝品牌爬虫 - Selenium版本"""

    def __init__(self, headless: bool = True):
        """
        初始化爬虫
        :param headless: 是否使用无头模式
        """
        self.base_url = "https://www.dongchedi.com"
        self.brands = []

        # 配置Chrome选项
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 15)
        except Exception as e:
            logger.error(f"初始化Chrome浏览器失败: {str(e)}")
            raise

    def __del__(self):
        """清理资源"""
        if hasattr(self, 'driver'):
            self.driver.quit()

    def scrape_from_selection_page(self) -> List[Dict]:
        """
        从选车页面爬取品牌列表
        """
        logger.info("尝试从选车页面获取品牌列表...")

        try:
            # 访问选车页面
            url = f"{self.base_url}/auto/x-x-x-x-x"
            logger.info(f"访问页面: {url}")
            self.driver.get(url)

            # 等待页面加载
            time.sleep(3)

            # 查找品牌选择区域的不同可能选择器
            selectors = [
                "//div[contains(@class, 'brand')]//a",
                "//a[contains(@href, '/auto/library-brand/')]",
                "//div[contains(@class, 'filter')]//a[contains(@href, 'brand')]",
                "//ul[contains(@class, 'brand')]//li//a",
            ]

            brands_found = []

            for selector in selectors:
                try:
                    logger.info(f"尝试选择器: {selector}")
                    elements = self.driver.find_elements(By.XPATH, selector)

                    if elements:
                        logger.info(f"找到 {len(elements)} 个元素")

                        for element in elements:
                            try:
                                href = element.get_attribute('href')
                                text = element.text.strip()

                                if href and '/auto/library-brand/' in href:
                                    # 提取品牌ID
                                    match = re.search(r'/auto/library-brand/(\d+)', href)
                                    if match and text:
                                        brand_id = match.group(1)
                                        brands_found.append({
                                            'code_brand': brand_id,
                                            'brand': text,
                                            'url': href if href.startswith('http') else f"{self.base_url}{href}"
                                        })

                            except Exception as e:
                                logger.debug(f"提取元素信息失败: {str(e)}")
                                continue

                        if brands_found:
                            break

                except Exception as e:
                    logger.debug(f"选择器 {selector} 失败: {str(e)}")
                    continue

            # 去重
            seen = set()
            unique_brands = []
            for brand in brands_found:
                key = brand['code_brand']
                if key not in seen:
                    seen.add(key)
                    unique_brands.append(brand)

            logger.info(f"从选车页面获取到 {len(unique_brands)} 个品牌")
            return unique_brands

        except Exception as e:
            logger.error(f"从选车页面爬取失败: {str(e)}")
            return []

    def scrape_from_network_requests(self) -> List[Dict]:
        """
        监听网络请求获取API数据
        """
        logger.info("尝试从网络请求获取数据...")

        try:
            # 启用网络日志
            self.driver.execute_cdp_cmd('Network.enable', {})

            # 访问首页或选车页面触发API调用
            url = f"{self.base_url}/auto/x-x-x-x-x"
            self.driver.get(url)

            # 等待页面加载
            time.sleep(5)

            # 获取网络日志
            logs = self.driver.get_log('performance')

            for log in logs:
                try:
                    message = log.get('message', '')
                    if 'brand' in message.lower() and 'response' in message.lower():
                        logger.debug(f"发现可能的品牌API: {message[:200]}")
                        # 这里可以进一步解析API响应
                except:
                    continue

        except Exception as e:
            logger.warning(f"网络请求监听失败: {str(e)}")

        return []

    def scrape_brand_detail(self, brand_id: int) -> Dict:
        """
        访问品牌详情页获取品牌名称
        """
        try:
            url = f"{self.base_url}/auto/library-brand/{brand_id}"
            self.driver.get(url)
            time.sleep(1)

            # 尝试获取品牌名称
            selectors = [
                "//h1[contains(@class, 'brand')]",
                "//title",
                "//div[contains(@class, 'brand-name')]",
            ]

            for selector in selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    text = element.text.strip()
                    if text:
                        return {
                            'code_brand': str(brand_id),
                            'brand': text.split('-')[0].strip(),  # 去除可能的后缀
                            'url': url
                        }
                except:
                    continue

            return None

        except Exception as e:
            logger.debug(f"获取品牌 {brand_id} 详情失败: {str(e)}")
            return None

    def scrape_by_id_range(self, start_id: int = 1, end_id: int = 300) -> List[Dict]:
        """
        通过ID范围遍历获取品牌
        """
        logger.info(f"使用ID遍历方案，范围: {start_id}-{end_id}")
        brands = []

        for brand_id in range(start_id, end_id + 1):
            brand = self.scrape_brand_detail(brand_id)
            if brand:
                logger.info(f"发现品牌: {brand['brand']} (ID: {brand_id})")
                brands.append(brand)

            if brand_id % 10 == 0:
                logger.info(f"进度: {brand_id}/{end_id}, 已找到 {len(brands)} 个品牌")

        return brands

    def scrape(self, method: str = 'auto') -> List[Dict]:
        """
        主爬取方法
        :param method: 爬取方法 ('auto', 'selection', 'id_range')
        """
        logger.info(f"开始爬取懂车帝品牌数据，方法: {method}...")

        if method == 'auto':
            # 先尝试从选车页面获取
            brands = self.scrape_from_selection_page()

            # 如果失败，使用ID遍历
            if not brands or len(brands) < 10:
                logger.warning("选车页面方式失败或数据不足，切换到ID遍历方式")
                brands = self.scrape_by_id_range(1, 300)

        elif method == 'selection':
            brands = self.scrape_from_selection_page()

        elif method == 'id_range':
            brands = self.scrape_by_id_range(1, 300)

        else:
            logger.error(f"未知的爬取方法: {method}")
            return []

        # 按ID排序
        brands.sort(key=lambda x: int(x['code_brand']))

        return brands

    def save_to_tsv(self, brands: List[Dict], filename: str = 'dongchedi_brands.tsv'):
        """
        保存数据到TSV文件
        """
        if not brands:
            logger.error("没有数据可保存")
            return

        logger.info(f"保存 {len(brands)} 个品牌到 {filename}")

        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            # 写入表头
            writer.writerow(['code_brand', 'brand', 'url'])
            writer.writerow(['品牌编码', '品牌', '网址'])

            # 写入数据
            for brand in brands:
                writer.writerow([
                    brand['code_brand'],
                    brand['brand'],
                    brand['url']
                ])

        logger.info(f"数据已保存到 {filename}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='懂车帝品牌爬虫')
    parser.add_argument('--method', choices=['auto', 'selection', 'id_range'],
                        default='auto', help='爬取方法')
    parser.add_argument('--headless', action='store_true', default=True,
                        help='使用无头模式')
    parser.add_argument('--output', default='dongchedi_brands.tsv',
                        help='输出文件名')

    args = parser.parse_args()

    try:
        scraper = DongchediSeleniumScraper(headless=args.headless)
        brands = scraper.scrape(method=args.method)

        if brands:
            scraper.save_to_tsv(brands, args.output)
            logger.info(f"爬取完成！共获取 {len(brands)} 个品牌")
        else:
            logger.error("爬取失败，未获取到任何品牌数据")

    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        raise


if __name__ == '__main__':
    main()
