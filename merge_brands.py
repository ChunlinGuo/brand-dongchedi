#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并两个ID段的品牌数据，过滤占位符
"""

import csv

def load_brands(filename):
    """加载TSV文件"""
    brands = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        next(reader)  # 跳过第二行表头
        for row in reader:
            brands.append(row)
    return brands

# 加载两个文件
print("加载数据文件...")
brands_1_1000 = load_brands('brands_1_1000.tsv')
brands_10000_11000 = load_brands('brands_10000_11000.tsv')

print(f"ID 1-1000: {len(brands_1_1000)} 条记录")
print(f"ID 10000-11000: {len(brands_10000_11000)} 条记录")

# 合并
all_brands = brands_1_1000 + brands_10000_11000
print(f"合并后: {len(all_brands)} 条记录")

# 过滤占位符
filtered_brands = [
    b for b in all_brands 
    if '汽车报价大全' not in b['brand']
]

print(f"过滤后: {len(filtered_brands)} 个真实品牌")

# 按ID排序
filtered_brands.sort(key=lambda x: int(x['code_brand']))

# 保存完整数据
output_file = 'dongchedi_brands_complete.tsv'
with open(output_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f, delimiter='\t')
    writer.writerow(['code_brand', 'brand', 'url'])
    writer.writerow(['品牌编码', '品牌', '网址'])
    
    for brand in filtered_brands:
        writer.writerow([brand['code_brand'], brand['brand'], brand['url']])

print(f"\n✓ 已保存到 {output_file}")

# 显示统计
brand_ids = [int(b['code_brand']) for b in filtered_brands]
print(f"\n统计信息:")
print(f"  品牌总数: {len(filtered_brands)}")
print(f"  ID范围: {min(brand_ids)} - {max(brand_ids)}")

# 检查关键品牌
print(f"\n关键品牌检查:")
if 10293 in brand_ids:
    brand_10293 = next(b for b in filtered_brands if int(b['code_brand']) == 10293)
    print(f"  ✓ 尊界 (ID 10293): {brand_10293['brand']}")
else:
    print(f"  ✗ 未找到尊界 (ID 10293)")

# 显示10000+的品牌
large_id_brands = [b for b in filtered_brands if int(b['code_brand']) >= 10000]
if large_id_brands:
    print(f"\n大ID品牌 (ID >= 10000): {len(large_id_brands)} 个")
    for brand in large_id_brands[:10]:
        print(f"  - ID {brand['code_brand']}: {brand['brand']}")
    if len(large_id_brands) > 10:
        print(f"  ... 还有 {len(large_id_brands) - 10} 个")

# 显示前10个和后10个品牌
print(f"\n前10个品牌:")
for brand in filtered_brands[:10]:
    print(f"  {brand['code_brand']}\t{brand['brand']}")

print(f"\n后10个品牌:")
for brand in filtered_brands[-10:]:
    print(f"  {brand['code_brand']}\t{brand['brand']}")

print(f"\n✓ 完成！")
