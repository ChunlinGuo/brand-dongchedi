#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
懂车帝品牌数据爬虫
通过遍历品牌ID，访问品牌详情页，提取品牌名称和URL
"""

import requests
import time
import csv
from typing import List, Dict, Optional
import logging
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DongchediScraper:
    """懂车帝品牌爬虫"""

    def __init__(self, max_workers: int = 10, delay: float = 0.1):
        """
        初始化爬虫
        :param max_workers: 最大并发数
        :param delay: 请求延迟（秒）
        """
        self.base_url = "https://www.dongchedi.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.dongchedi.com/',
            'Connection': 'keep-alive',
        }
        self.max_workers = max_workers
        self.delay = delay

    def get_brand_info(self, brand_id: int) -> Optional[Dict]:
        """
        获取单个品牌信息
        :param brand_id: 品牌ID
        :return: 品牌信息字典或None
        """
        url = f"{self.base_url}/auto/library-brand/{brand_id}"

        try:
            # 创建独立的session用于并发请求
            session = requests.Session()
            session.headers.update(self.headers)

            response = session.get(url, timeout=10)

            # 如果页面存在
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # 从title提取品牌名
                brand_name = None
                title = soup.find('title')
                if title:
                    # 标题格式: "奔驰_Mercedes-Benz_德系_懂车帝"
                    title_text = title.text.strip()
                    if title_text:
                        parts = title_text.split('_')
                        if parts:
                            brand_name = parts[0].strip()

                # 如果title提取失败，尝试h1标签
                if not brand_name:
                    h1 = soup.find('h1')
                    if h1:
                        brand_name = h1.text.strip()

                # 验证是否是有效的品牌页面
                if brand_name and brand_name != '懂车帝':
                    logger.info(f"✓ 品牌 {brand_id}: {brand_name}")
                    return {
                        'code_brand': str(brand_id),
                        'brand': brand_name,
                        'url': url
                    }
                else:
                    logger.debug(f"✗ ID {brand_id}: 无效页面")

            elif response.status_code == 404:
                logger.debug(f"✗ ID {brand_id}: 404")
            else:
                logger.debug(f"✗ ID {brand_id}: Status {response.status_code}")

            # 请求延迟
            if self.delay > 0:
                time.sleep(self.delay)

        except requests.RequestException as e:
            logger.debug(f"✗ ID {brand_id}: 请求失败 - {str(e)}")
        except Exception as e:
            logger.error(f"✗ ID {brand_id}: 解析失败 - {str(e)}")

        return None

    def scrape_sequential(self, start_id: int = 1, end_id: int = 500) -> List[Dict]:
        """
        顺序爬取品牌数据
        :param start_id: 起始ID
        :param end_id: 结束ID
        :return: 品牌列表
        """
        logger.info(f"开始顺序爬取，ID范围: {start_id}-{end_id}")
        brands = []

        for brand_id in range(start_id, end_id + 1):
            brand = self.get_brand_info(brand_id)
            if brand:
                brands.append(brand)

            # 进度显示
            if brand_id % 50 == 0:
                logger.info(f"进度: {brand_id}/{end_id}, 已找到 {len(brands)} 个品牌")

        return brands

    def scrape_parallel(self, start_id: int = 1, end_id: int = 500) -> List[Dict]:
        """
        并发爬取品牌数据
        :param start_id: 起始ID
        :param end_id: 结束ID
        :return: 品牌列表
        """
        logger.info(f"开始并发爬取，ID范围: {start_id}-{end_id}, 并发数: {self.max_workers}")
        brands = []
        total = end_id - start_id + 1
        completed = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_id = {
                executor.submit(self.get_brand_info, brand_id): brand_id
                for brand_id in range(start_id, end_id + 1)
            }

            # 处理完成的任务
            for future in as_completed(future_to_id):
                completed += 1
                brand_id = future_to_id[future]

                try:
                    brand = future.result()
                    if brand:
                        brands.append(brand)

                    # 进度显示
                    if completed % 50 == 0 or completed == total:
                        logger.info(f"进度: {completed}/{total}, 已找到 {len(brands)} 个品牌")

                except Exception as e:
                    logger.error(f"处理品牌 {brand_id} 时出错: {str(e)}")

        return brands

    def save_to_tsv(self, brands: List[Dict], filename: str = 'dongchedi_brands.tsv'):
        """
        保存数据到TSV文件
        :param brands: 品牌列表
        :param filename: 输出文件名
        """
        if not brands:
            logger.error("没有数据可保存")
            return

        # 按品牌ID排序
        brands.sort(key=lambda x: int(x['code_brand']))

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

        logger.info(f"✓ 数据已保存到 {filename}")

        # 显示前几条数据作为预览
        logger.info("\n数据预览（前5条）:")
        for brand in brands[:5]:
            logger.info(f"  {brand['code_brand']}\t{brand['brand']}\t{brand['url']}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='懂车帝品牌爬虫',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 scrape_brands.py --start 1 --end 500 --parallel
  python3 scrape_brands.py --start 1 --end 1000 --workers 20
  python3 scrape_brands.py --quick-test
        """
    )

    parser.add_argument('--start', type=int, default=1,
                        help='起始品牌ID (默认: 1)')
    parser.add_argument('--end', type=int, default=500,
                        help='结束品牌ID (默认: 500)')
    parser.add_argument('--output', default='dongchedi_brands.tsv',
                        help='输出文件名 (默认: dongchedi_brands.tsv)')
    parser.add_argument('--workers', type=int, default=10,
                        help='并发线程数 (默认: 10)')
    parser.add_argument('--delay', type=float, default=0.05,
                        help='请求延迟秒数 (默认: 0.05)')
    parser.add_argument('--parallel', action='store_true',
                        help='使用并发模式 (默认: 顺序模式)')
    parser.add_argument('--quick-test', action='store_true',
                        help='快速测试模式 (只爬取前50个ID)')

    args = parser.parse_args()

    # 快速测试模式
    if args.quick_test:
        args.start = 1
        args.end = 50
        args.parallel = True
        logger.info("快速测试模式")

    # 创建爬虫
    scraper = DongchediScraper(
        max_workers=args.workers,
        delay=args.delay
    )

    # 爬取数据
    start_time = time.time()

    if args.parallel:
        brands = scraper.scrape_parallel(args.start, args.end)
    else:
        brands = scraper.scrape_sequential(args.start, args.end)

    elapsed = time.time() - start_time

    # 保存数据
    if brands:
        scraper.save_to_tsv(brands, args.output)
        logger.info(f"\n{'='*60}")
        logger.info(f"✓ 爬取完成！")
        logger.info(f"  总耗时: {elapsed:.2f} 秒")
        logger.info(f"  扫描范围: {args.start}-{args.end} ({args.end - args.start + 1} 个ID)")
        logger.info(f"  找到品牌: {len(brands)} 个")
        logger.info(f"  输出文件: {args.output}")
        logger.info(f"{'='*60}")
    else:
        logger.error("爬取失败，未获取到任何品牌数据")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
