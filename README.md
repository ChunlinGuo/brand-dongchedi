# 懂车帝品牌数据爬虫

这个项目用于爬取懂车帝网站的所有汽车品牌数据。

## 功能特性

- 爬取懂车帝所有品牌信息
- 包含品牌编码、品牌名称和对应URL
- 支持并发爬取，提高效率
- 自动过滤无效数据
- 输出TSV格式数据

## 数据统计

- **总品牌数**: 556个真实品牌
- **有效ID范围**: 1-939
- **扫描ID范围**: 1-1000（已过滤444个占位符）
- **数据完整性**: ✅ 100% 覆盖所有品牌
- **数据格式**: TSV（制表符分隔）
- **包含最新品牌**: 智界、享界、乐道、JAECOO等2024年新品牌

📊 [查看详细统计报告](STATISTICS.md)

## 安装依赖

```bash
pip install -r requirements.txt
```

需要的依赖：
- requests
- beautifulsoup4
- lxml

## 使用方法

### 快速测试（推荐先运行）

```bash
python3 scrape_brands.py --quick-test
```

### 完整爬取

```bash
# 基础用法（顺序模式，ID 1-500）
python3 scrape_brands.py

# 并发模式（推荐）
python3 scrape_brands.py --parallel --workers 20

# 自定义ID范围
python3 scrape_brands.py --start 1 --end 1000 --parallel

# 指定输出文件
python3 scrape_brands.py --output my_brands.tsv --parallel
```

### 参数说明

- `--start`: 起始品牌ID（默认：1）
- `--end`: 结束品牌ID（默认：500）
- `--output`: 输出文件名（默认：dongchedi_brands.tsv）
- `--workers`: 并发线程数（默认：10）
- `--delay`: 请求延迟秒数（默认：0.05）
- `--parallel`: 使用并发模式
- `--quick-test`: 快速测试模式（只爬取前50个ID）

## 输出格式

输出文件：`dongchedi_brands.tsv`

格式示例：
```
code_brand	brand	url
品牌编码	品牌	网址
1	大众	https://www.dongchedi.com/auto/library-brand/1
2	奥迪	https://www.dongchedi.com/auto/library-brand/2
3	奔驰	https://www.dongchedi.com/auto/library-brand/3
4	宝马	https://www.dongchedi.com/auto/library-brand/4
16	比亚迪	https://www.dongchedi.com/auto/library-brand/16
```

## 技术实现

1. **数据来源**: 直接访问品牌详情页面（`/auto/library-brand/{id}`）
2. **提取方法**: 从HTML的`<title>`和`<h1>`标签提取品牌名称
3. **并发处理**: 使用`ThreadPoolExecutor`实现多线程并发
4. **数据清理**: 自动过滤"汽车报价大全"等占位符

## 项目文件

- `scrape_brands.py` - 主爬虫脚本（推荐使用）
- `scrape_brands_selenium.py` - Selenium版本（适用于需要浏览器渲染的场景）
- `test_api.py` - API测试脚本
- `dongchedi_brands.tsv` - 输出数据文件（556个品牌）
- `requirements.txt` - Python依赖

## 注意事项

- 爬取过程请遵守网站的robots.txt规则
- 建议使用`--parallel`模式提高效率
- 已自动过滤无效品牌数据
- 推荐ID范围：1-1000（覆盖所有品牌）
