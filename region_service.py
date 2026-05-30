# -*- coding: utf-8 -*-
import csv
import os

from config import AppConfig
import data_loader


def filter_salespersons_by_region(records, region):
    """按营部筛选销售员兵力部署点。全国入口展示全部。"""
    region_name = region.get("name")
    if not region_name or region_name == "全国":
        return list(records)
    return [record for record in records if record.get("headquarter") == region_name]


def export_salesperson_data(records, output_path):
    """导出兵力部署-销售员地图使用的数据。"""
    fieldnames = ["营", "连队", "姓名", "年度预算目标", "年度订单完成率", "标记点", "负责区域"]
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow({
                "营": record.get("headquarter", ""),
                "连队": record.get("team", ""),
                "姓名": record.get("name", ""),
                "年度预算目标": record.get("budget", ""),
                "年度订单完成率": record.get("completion", ""),
                "标记点": record.get("mark_city", ""),
                "负责区域": record.get("area", ""),
            })


def merge_market_and_troop_data(market_records, troop_records):
    """把热力色块数据和连队圆点数据按城市合并。"""
    troop_by_city = {}
    for troop in troop_records:
        key = troop.get("city_key") or data_loader.city_match_key(troop.get("city", ""))
        if key:
            troop_by_city[key] = troop

    merged_records = []
    matched_troop_keys = set()
    for record in market_records:
        merged = dict(record)
        key = data_loader.city_match_key(record.get("city", ""))
        troop = troop_by_city.get(key)
        if troop:
            matched_troop_keys.add(key)
            merged["point_val"] = troop.get("sales")
            merged["troop_headquarter"] = troop.get("headquarter", "")
            merged["team_name"] = troop.get("team", "")
            merged["team_sales"] = troop.get("sales")
            merged["team_share"] = troop.get("share", "")
            merged["deployment"] = troop.get("people", "")
            merged["people"] = troop.get("people", "")
            merged["captain"] = troop.get("captain", "")
            merged["members"] = troop.get("members", "")
            merged["budget"] = troop.get("budget", "")
        merged_records.append(merged)

    for key, troop in troop_by_city.items():
        if key in matched_troop_keys:
            continue
        merged_records.append({
            "city": troop.get("city", ""),
            "map_val": 0.0,
            "point_val": troop.get("sales"),
            "troop_headquarter": troop.get("headquarter", ""),
            "team_name": troop.get("team", ""),
            "team_sales": troop.get("sales"),
            "team_share": troop.get("share", ""),
            "deployment": troop.get("people", ""),
            "people": troop.get("people", ""),
            "captain": troop.get("captain", ""),
            "members": troop.get("members", ""),
            "budget": troop.get("budget", ""),
        })

    return merged_records


def resolve_region_mapping_path(config):
    """兼容 Windows 隐藏扩展名导致的 .csv.csv 文件名。"""
    configured_path = getattr(config, "REGION_MAPPING_PATH", "")
    candidates = [
        configured_path,
        configured_path + ".csv" if configured_path else "",
        os.path.join(config.BASE_DIR, "region_city_mapping.csv"),
        os.path.join(config.BASE_DIR, "region_city_mapping.csv.csv"),
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


def build_regions_from_mappings(mappings, config=AppConfig):
    """按“营部”自动生成一级营销区地图配置。"""
    grouped = {}
    city_meta = {}
    for item in mappings:
        grouped.setdefault(item["headquarter"], set()).add(item["city"])
        city_meta.setdefault(item["headquarter"], {}).setdefault(item["city"], set()).add(item["team"])

    regions = [dict(config.NATIONAL_REGION)]
    for hq_name in sorted(grouped.keys()):
        safe_id = safe_filename(hq_name)
        cities = sorted(grouped[hq_name])
        city_teams = {
            city: "、".join(sorted(team for team in city_meta[hq_name].get(city, set()) if team))
            for city in cities
        }
        regions.append({
            "id": safe_id,
            "name": hq_name,
            "title": f"{hq_name}{config.MapTypes.TEAM_DEPLOYMENT}",
            "output_group": os.path.join("regions", hq_name),
            "html_name": f"{hq_name}{config.MapTypes.TEAM_DEPLOYMENT}.html",
            "data_name": f"{hq_name}{config.MapTypes.TEAM_DEPLOYMENT}_数据.csv",
            "cities": cities,
            "city_teams": city_teams,
            "boundary_geojson": None,
        })
    return regions


def filter_by_region(records, region):
    """按营销区城市清单过滤；cities 为空时代表全国。"""
    cities = region.get("cities")
    if not cities:
        return list(records)

    city_set = {data_loader.align_echarts_city_name(str(city).strip()) for city in cities}
    city_teams = region.get("city_teams", {})
    region_records = []
    for record in records:
        city = record.get("city")
        enriched = dict(record)
        enriched["region_name"] = region.get("name", "")
        enriched["region_team"] = city_teams.get(city, "")
        if city not in city_set:
            if record.get("point_val") is None or record.get("troop_headquarter") != region.get("name"):
                continue
            enriched["region_team"] = record.get("team_name", "")
        if not is_point_in_region(enriched):
            clear_point_data(enriched)
        region_records.append(enriched)
    return region_records


def is_point_in_region(record):
    """跨区城市只在兵力数据归属与当前区域匹配时显示圆点。"""
    if record.get("point_val") is None:
        return True

    troop_hq = str(record.get("troop_headquarter", "")).strip()
    troop_team = str(record.get("team_name", "")).strip()
    region_name = str(record.get("region_name", "")).strip()
    region_team = str(record.get("region_team", "")).strip()

    if troop_hq and region_name and troop_hq != region_name:
        return False
    if troop_team and region_team:
        region_teams = {team.strip() for team in region_team.split("、") if team.strip()}
        if region_teams and troop_team not in region_teams:
            return False
    return True


def clear_point_data(record):
    """保留热力色块，清掉不属于当前区域的圆点和气泡信息。"""
    record["point_val"] = None
    record["troop_headquarter"] = ""
    record["team_name"] = ""
    record["team_sales"] = ""
    record["team_share"] = ""
    record["deployment"] = ""
    record["people"] = ""
    record["captain"] = ""
    record["members"] = ""
    record["budget"] = ""


def export_region_data(records, output_path):
    """导出某张兵力部署-连队地图实际使用的数据，便于核对。"""
    fieldnames = [
        "营部",
        "区划连队",
        "城市",
        "市场容量",
        "圆点连队",
        "销量",
        "市占率",
        "人数",
        "26年年度预算",
    ]
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow({
                "营部": record.get("region_name", ""),
                "区划连队": record.get("region_team", ""),
                "城市": record.get("city", ""),
                "市场容量": record.get("map_val", ""),
                "圆点连队": record.get("team_name", ""),
                "销量": record.get("team_sales", ""),
                "市占率": record.get("team_share", ""),
                "人数": record.get("people") or record.get("deployment", ""),
                "26年年度预算": record.get("budget", ""),
            })


def safe_filename(value):
    """清理 Windows 文件名不允许的字符。"""
    text = str(value).strip()
    for char in '<>:"/\\|?*':
        text = text.replace(char, "_")
    return text or "region"
