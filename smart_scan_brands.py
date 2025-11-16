#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能ID扫描策略：
1. 采样检测找出有效ID区间
2. 对有效区间进行密集扫描
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
from typing import List, Tuple

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class SmartBrandScanner:
    def __init__(self):
        self.base_url = "https://www.dongchedi.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }

    def check_brand_id(self, brand_id: int) -> Tuple[bool, str]:
        """检查单个ID是否有效"""
        url = f"{self.base_url}/auto/library-brand/{brand_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.find('title')
                
                if title:
                    title_text = title.text.strip()
                    # 过滤占位符
                    if '汽车报价大全' not in title_text and title_text:
                        brand_name = title_text.split('_')[0]
                        return True, brand_name
                        
            return False, ""
            
        except:
            return False, ""

    def sample_scan(self, max_id: int = 20000, step: int = 100) -> List[int]:
        """
        采样扫描：每隔step测试一个ID
        找出可能有品牌的ID区间
        """
        logger.info(f"第1步：采样扫描（0-{max_id}，步长{step}）")
        logger.info("="*60)
        
        valid_samples = []
        
        for test_id in range(0, max_id + 1, step):
            is_valid, brand_name = self.check_brand_id(test_id)
            
            if is_valid:
                logger.info(f"✓ ID {test_id:5d}: {brand_name}")
                valid_samples.append(test_id)
            
            # 每检查10个ID暂停一下
            if test_id % (step * 10) == 0:
                logger.info(f"  进度: {test_id}/{max_id}")
                time.sleep(0.5)
        
        logger.info(f"\n采样结果：找到 {len(valid_samples)} 个有效样本")
        return valid_samples

    def find_ranges(self, samples: List[int], margin: int = 200) -> List[Tuple[int, int]]:
        """
        根据采样结果确定需要密集扫描的区间
        """
        if not samples:
            return []
        
        samples.sort()
        ranges = []
        
        # 为每个样本创建扫描区间
        for sample_id in samples:
            start = max(1, sample_id - margin)
            end = sample_id + margin
            ranges.append((start, end))
        
        # 合并重叠的区间
        merged = []
        for start, end in sorted(ranges):
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        
        logger.info(f"\n确定 {len(merged)} 个扫描区间：")
        for start, end in merged:
            logger.info(f"  {start:5d} - {end:5d} (范围: {end-start+1})")
        
        return merged

    def dense_scan_range(self, start: int, end: int) -> List[dict]:
        """密集扫描指定区间"""
        logger.info(f"\n密集扫描: {start}-{end}")
        brands = []
        
        for brand_id in range(start, end + 1):
            is_valid, brand_name = self.check_brand_id(brand_id)
            
            if is_valid:
                brands.append({
                    'code_brand': str(brand_id),
                    'brand': brand_name,
                    'url': f"{self.base_url}/auto/library-brand/{brand_id}"
                })
                logger.info(f"  ✓ {brand_id}: {brand_name}")
            
            # 进度显示
            if brand_id % 50 == 0:
                logger.info(f"    进度: {brand_id}/{end}, 已找到 {len(brands)} 个")
                time.sleep(0.2)
        
        return brands

    def smart_scan(self, max_id: int = 15000) -> List[dict]:
        """主扫描流程"""
        logger.info("智能ID扫描开始")
        logger.info("="*60)
        
        # 步骤1：采样
        samples = self.sample_scan(max_id=max_id, step=100)
        
        if not samples:
            logger.warning("未找到有效样本！")
            return []
        
        # 步骤2：确定扫描区间  
        ranges = self.find_ranges(samples, margin=200)
        
        # 步骤3：密集扫描每个区间
        logger.info(f"\n第2步：密集扫描")
        logger.info("="*60)
        
        all_brands = []
        for idx, (start, end) in enumerate(ranges, 1):
            logger.info(f"\n区间 {idx}/{len(ranges)}: {start}-{end}")
            brands = self.dense_scan_range(start, end)
            all_brands.extend(brands)
            logger.info(f"  本区间找到 {len(brands)} 个品牌")
        
        return all_brands


def main():
    scanner = SmartBrandScanner()
    
    # 执行智能扫描
    brands = scanner.smart_scan(max_id=15000)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"扫描完成！")
    logger.info(f"总计找到 {len(brands)} 个品牌")
    logger.info(f"{'='*60}")
    
    if brands:
        # 保存结果
        import csv
        with open('complete_brands.tsv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['code_brand', 'brand', 'url'])
            writer.writerow(['品牌编码', '品牌', '网址'])
            
            for brand in sorted(brands, key=lambda x: int(x['code_brand'])):
                writer.writerow([brand['code_brand'], brand['brand'], brand['url']])
        
        logger.info(f"\n已保存到 complete_brands.tsv")
        
        # 检查关键品牌
        brand_ids = [int(b['code_brand']) for b in brands]
        logger.info(f"\nID范围: {min(brand_ids)} - {max(brand_ids)}")
        
        if 10293 in brand_ids:
            logger.info(f"✓ 包含尊界(ID 10293)")
        else:
            logger.warning(f"✗ 未找到尊界(ID 10293)，需要扩大扫描范围")


if __name__ == '__main__':
    main()
