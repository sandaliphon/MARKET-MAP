# -*- coding: utf-8 -*-
import os
import re


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def find_latest_month(base_dir):
    monthly_dir = os.path.join(base_dir, "input", "monthly")
    if not os.path.isdir(monthly_dir):
        return ""

    month_pattern = re.compile(r"^\d{4}-\d{2}$")
    months = [
        name
        for name in os.listdir(monthly_dir)
        if month_pattern.match(name) and os.path.isdir(os.path.join(monthly_dir, name))
    ]
    return sorted(months)[-1] if months else ""


LATEST_MONTH = find_latest_month(BASE_DIR)

class AppConfig:
    # 1. 基础路径管理
    BASE_DIR = BASE_DIR
    CURRENT_MONTH = LATEST_MONTH
    MONTHLY_INPUT_DIR = os.path.join(BASE_DIR, "input", "monthly", CURRENT_MONTH)
    DATA_PATH = os.path.join(BASE_DIR, "input", "master", "25年城市容量.csv")
    TROOP_PATH = os.path.join(BASE_DIR, "input", "master", "兵力部署.csv")
    TROOP_MONTHLY_PATH = os.path.join(MONTHLY_INPUT_DIR, "兵力部署.csv")
    SALESPERSON_PATH = os.path.join(BASE_DIR, "input", "master", "销售员对应城市.csv")
    SALESPERSON_MONTHLY_PATH = os.path.join(MONTHLY_INPUT_DIR, "销售员月度销量.csv")
    REGION_MAPPING_PATH = os.path.join(BASE_DIR, "input", "master", "region_city_mapping.csv")
    OUTPUT_HTML = os.path.join(BASE_DIR, "china_city_double_track_map.html")
    OUTPUT_DIR = os.path.join(BASE_DIR, "output")
    
    # 2. ⚡【核心扩展点】CSV列名映射配置
    # 如果你的 CSV 更改了表头或调换了列顺序，只需在这里修改对应的字符串即可
    COLUMNS = {
        "CITY": "城市",
        "MAP_VAL": "市场容量",
    }
    TROOP_COLUMNS = {
        "CITY": "城市",
        "HEADQUARTER": "营部",
        "TEAM": "连队",
        "SALES": "中集销量",
        "SHARE": "市占率",
        "PEOPLE": "人数",
        "CAPTAIN": "连长",
        "MEMBERS": "团队成员",
    }
    TROOP_MONTHLY_COLUMNS = {
        "HEADQUARTER": "营部",
        "TEAM": "连队",
        "SALES": "销量",
        "SHARE": "市占率",
    }
    REGION_COLUMNS = {
        "HEADQUARTER": "营部",
        "TEAM": "连队",
        "CITY": "城市",
    }
    SALESPERSON_COLUMNS = {
        "NAME": "姓名",
        "HEADQUARTER": "营",
        "TEAM": "连队",
        "BUDGET": "年度目标",
        "COMPLETION": "年度订单完成率",
        "MARK_CITY": "标记点",
        "AREA": "负责区域",
    }
    SALESPERSON_MONTHLY_COLUMNS = {
        "NAME": "姓名",
        "HEADQUARTER": "营",
        "TEAM": "连队",
        "BUDGET": "年度目标",
        "ORDER_COUNT": "订单数",
        "ORDER_COMPLETION": "订单年度达成率",
        "INVOICE_COUNT": "开票数",
        "INVOICE_COMPLETION": "开票达成度",
    }

    # 3. 商业视觉通用配置
    THEME_STYLE = "white"  # 可选: 'white', 'dark', 'chalk', 'essos'
    TITLE = "聚焦产品市场热力图"

    class Files:
        """输入输出文件命名配置"""
        MARKET_DATA_DISPLAY = "input/master/25年城市容量.csv"
        TROOP_DATA_DISPLAY = "input/master/兵力部署.csv"
        TROOP_MONTHLY_DATA_DISPLAY = os.path.join("input", "monthly", LATEST_MONTH, "兵力部署.csv").replace("\\", "/")
        SALESPERSON_DATA_DISPLAY = "input/master/销售员对应城市.csv"
        SALESPERSON_MONTHLY_DATA_DISPLAY = os.path.join("input", "monthly", LATEST_MONTH, "销售员月度销量.csv").replace("\\", "/")
        REGION_MAPPING_DISPLAY = "input/master/region_city_mapping.csv"
        INDEX_HTML = "index.html"
        VIEWER_HTML = "viewer.html"
        MAP_MANIFEST = "maps.json"
        MAP_DATA_DIR = "data"

    class Site:
        """静态入口页和通用页面增强配置"""
        TITLE = "中集车辆半挂车业务集团市场总览"
        HEADER = "中集车辆半挂车业务集团市场总览"
        LABEL_TOGGLE_TEXT = "气泡常驻"

    class MapTypes:
        """地图类型命名配置"""
        TEAM_DEPLOYMENT = "兵力部署-连队"
        SALESPERSON_DEPLOYMENT = "兵力部署-销售员"
        TEAM_COUNT_UNIT = "条城市数据"
        SALESPERSON_COUNT_UNIT = "个销售员标记点"

    class Messages:
        """控制台输出文案"""
        BANNER = "================ 城市双轨地图生成系统 (区域输出版) ================"
        SUCCESS = "🎉 区域地图输出完成！"

    # 4. 地图输出配置
    # REGIONS 由 region_city_mapping.csv 自动生成；这里保留全国图配置。
    NATIONAL_REGION = {
        "id": "national",
        "name": "全国",
        "title": "全国聚焦产品市场热力图",
        "output_group": "national",
        "html_name": f"全国{MapTypes.TEAM_DEPLOYMENT}.html",
        "data_name": f"全国{MapTypes.TEAM_DEPLOYMENT}_数据.csv",
        "cities": None,
        "boundary_geojson": None,
    }
    
    class Market:
        """🗺️ 市场容量底图控制台"""
        SERIES_NAME = "市场容量"
        DATA_UNIT = "台"        
        COLOR_RANGE = ["#fff7bc", "#fec44f", "#d95f0e", "#990000"]

    class Team:
        """🎯 营销团队圆点控制台"""
        SERIES_NAME = "连队"
        DATA_UNIT = "人"
        SYMBOL_COLOR = "#0841eb"
        SIZE_RANGE = [6, 20]

    class Salesperson:
        """👤 销售员兵力部署圆点控制台"""
        SERIES_NAME = "销售员"
        SYMBOL_COLOR = "#e11d48"
        SIZE_RANGE = [8, 18]
