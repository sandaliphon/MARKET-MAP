# -*- coding: utf-8 -*-
import os

import pandas as pd

from config import AppConfig


ENCODINGS = ["utf-8-sig", "gbk", "utf-8", "gb18030"]


def align_echarts_city_name(city_name):
    """标准地图名称过滤器。"""
    if any(z in city_name for z in ["北京", "上海", "天津", "重庆"]):
        return city_name
    return city_name


def city_match_key(city_name):
    """用于跨表匹配城市，兼容“成都/成都市”这类写法差异。"""
    city = str(city_name).strip()
    for suffix in ["市", "地区", "自治州", "盟"]:
        if city.endswith(suffix):
            city = city[:-len(suffix)]
            break
    return city


def text_key(value):
    """用于业务名称匹配，去掉空格并统一空值。"""
    if pd.isna(value):
        return ""
    return str(value).strip().replace(" ", "")


def read_csv_auto(file_path):
    """按常见中文编码读取 CSV。"""
    df = None
    for enc in ENCODINGS:
        try:
            df = pd.read_csv(file_path, encoding=enc, engine="python")
            break
        except (UnicodeDecodeError, Exception):
            continue
    if df is None:
        raise FileNotFoundError(f"❌ 无法解析或找不到指定数据文件: {file_path}")
    return df.dropna(how="all")


def load_market_data(file_path, config=AppConfig):
    """读取热力图色块数据，只使用城市和市场容量。"""
    df = read_csv_auto(file_path)

    required_cols = [config.COLUMNS["CITY"], config.COLUMNS["MAP_VAL"]]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"CSV 表格缺少必要的列: '{col}'。请检查表头设置。")

    raw_records = []
    for _, row in df.iterrows():
        try:
            raw_name = str(row[config.COLUMNS["CITY"]]).strip()
            name = align_echarts_city_name(raw_name)
            if not name or name in ["nan", "None"]:
                continue

            map_col = config.COLUMNS["MAP_VAL"]
            map_val = float(row[map_col]) if pd.notna(row[map_col]) else 0.0

            raw_records.append({
                "city": name,
                "map_val": map_val,
                "point_val": None,
                "team_name": "",
                "team_sales": None,
                "team_share": "",
                "deployment": "",
                "people": "",
            })
        except:
            continue
    return raw_records


def load_csv_data(file_path):
    """兼容旧调用：读取市场热力数据。"""
    return load_market_data(file_path)


def load_troop_data(file_path, config=AppConfig):
    """读取连队兵力部署圆点数据。"""
    df = read_csv_auto(file_path)
    columns = config.TROOP_COLUMNS
    required_cols = [
        columns["CITY"],
        columns["HEADQUARTER"],
        columns["TEAM"],
        columns["PEOPLE"],
        columns["CAPTAIN"],
        columns["MEMBERS"],
        columns["BUDGET"],
    ]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"兵力部署表缺少必要的列: '{col}'。请检查表头设置。")

    hq_col = columns.get("HEADQUARTER")
    team_col = columns.get("TEAM")
    captain_col = columns.get("CAPTAIN")
    members_col = columns.get("MEMBERS")
    budget_col = columns.get("BUDGET")
    sales_col = columns.get("SALES")
    share_col = columns.get("SHARE")

    monthly_metrics = {}
    monthly_path = getattr(config, "TROOP_MONTHLY_PATH", "")
    if monthly_path and os.path.exists(monthly_path):
        monthly_df = read_csv_auto(monthly_path)
        monthly_columns = getattr(config, "TROOP_MONTHLY_COLUMNS", {})
        monthly_required_cols = [
            monthly_columns["HEADQUARTER"],
            monthly_columns["TEAM"],
            monthly_columns["SALES"],
            monthly_columns["SHARE"],
        ]
        for col in monthly_required_cols:
            if col not in monthly_df.columns:
                raise ValueError(f"月度兵力部署表缺少必要的列: '{col}'。请检查表头设置。")

        for _, metric_row in monthly_df.iterrows():
            hq_key = text_key(metric_row[monthly_columns["HEADQUARTER"]])
            team_key = text_key(metric_row[monthly_columns["TEAM"]])
            if not hq_key or not team_key:
                continue
            monthly_metrics[(hq_key, team_key)] = {
                "sales": metric_row[monthly_columns["SALES"]],
                "share": metric_row[monthly_columns["SHARE"]],
            }

    troop_records = []
    for _, row in df.iterrows():
        try:
            city = str(row[columns["CITY"]]).strip() if pd.notna(row[columns["CITY"]]) else ""
            if not city or city in ["nan", "None"]:
                continue

            hq = str(row[hq_col]).strip() if hq_col and hq_col in df.columns and pd.notna(row[hq_col]) else ""
            team = str(row[team_col]).strip() if team_col and team_col in df.columns and pd.notna(row[team_col]) else ""
            metric = monthly_metrics.get((text_key(hq), text_key(team)), {})

            raw_sales = metric.get("sales")
            if raw_sales is None and sales_col and sales_col in df.columns:
                raw_sales = row[sales_col]
            sales = None
            if pd.notna(raw_sales) and str(raw_sales).strip() != "":
                sales = float(raw_sales)
            else:
                sales = 0.0

            raw_share = metric.get("share")
            if raw_share is None and share_col and share_col in df.columns:
                raw_share = row[share_col]
            share = str(raw_share).strip() if raw_share is not None and pd.notna(raw_share) else ""
            people = str(row[columns["PEOPLE"]]).strip() if pd.notna(row[columns["PEOPLE"]]) else ""
            captain = str(row[captain_col]).strip() if captain_col and captain_col in df.columns and pd.notna(row[captain_col]) else ""
            members = str(row[members_col]).strip() if members_col and members_col in df.columns and pd.notna(row[members_col]) else ""
            budget = str(row[budget_col]).strip() if budget_col and budget_col in df.columns and pd.notna(row[budget_col]) else ""
            if people and not people.endswith("人"):
                people = f"{people}人"

            troop_records.append({
                "city": align_echarts_city_name(city),
                "city_key": city_match_key(city),
                "headquarter": hq,
                "team": team,
                "sales": sales,
                "share": share,
                "people": people,
                "captain": captain,
                "members": members,
                "budget": budget,
            })
        except:
            continue
    return troop_records


def load_salesperson_data(file_path, config=AppConfig):
    """读取销售员标记点数据，用于兵力部署-销售员地图。"""
    df = read_csv_auto(file_path)
    columns = config.SALESPERSON_COLUMNS
    required_cols = [
        columns["NAME"],
        columns["HEADQUARTER"],
        columns["BUDGET"],
        columns["MARK_CITY"],
        columns["AREA"],
    ]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"销售员对应城市表缺少必要的列: '{col}'。请检查表头设置。")

    team_col = columns.get("TEAM")
    completion_col = columns.get("COMPLETION")
    monthly_metrics = {}
    monthly_path = getattr(config, "SALESPERSON_MONTHLY_PATH", "")
    if monthly_path and os.path.exists(monthly_path):
        monthly_df = read_csv_auto(monthly_path)
        monthly_columns = getattr(config, "SALESPERSON_MONTHLY_COLUMNS", {})
        monthly_required_cols = [
            monthly_columns["NAME"],
            monthly_columns["HEADQUARTER"],
            monthly_columns["TEAM"],
        ]
        for col in monthly_required_cols:
            if col not in monthly_df.columns:
                raise ValueError(f"销售员月度销量表缺少必要的列: '{col}'。请检查表头设置。")

        for _, metric_row in monthly_df.iterrows():
            name_key = text_key(metric_row[monthly_columns["NAME"]])
            hq_key = text_key(metric_row[monthly_columns["HEADQUARTER"]])
            team_key = text_key(metric_row[monthly_columns["TEAM"]])
            if not name_key or not hq_key or not team_key:
                continue
            monthly_metrics[(name_key, hq_key, team_key)] = {
                "budget": metric_row[monthly_columns["BUDGET"]] if monthly_columns.get("BUDGET") in monthly_df.columns else "",
                "order_count": metric_row[monthly_columns["ORDER_COUNT"]] if monthly_columns.get("ORDER_COUNT") in monthly_df.columns else "",
                "order_completion": metric_row[monthly_columns["ORDER_COMPLETION"]] if monthly_columns.get("ORDER_COMPLETION") in monthly_df.columns else "",
                "invoice_count": metric_row[monthly_columns["INVOICE_COUNT"]] if monthly_columns.get("INVOICE_COUNT") in monthly_df.columns else "",
                "invoice_completion": metric_row[monthly_columns["INVOICE_COMPLETION"]] if monthly_columns.get("INVOICE_COMPLETION") in monthly_df.columns else "",
            }

    records = []
    for _, row in df.iterrows():
        try:
            name = str(row[columns["NAME"]]).strip() if pd.notna(row[columns["NAME"]]) else ""
            hq = str(row[columns["HEADQUARTER"]]).strip() if pd.notna(row[columns["HEADQUARTER"]]) else ""
            team = str(row[team_col]).strip() if team_col and team_col in df.columns and pd.notna(row[team_col]) else ""
            mark_city = str(row[columns["MARK_CITY"]]).strip() if pd.notna(row[columns["MARK_CITY"]]) else ""
            if not name or not hq or not mark_city:
                continue
            metric = monthly_metrics.get((text_key(name), text_key(hq), text_key(team)), {})
            budget = metric.get("budget")
            if budget is None or pd.isna(budget) or str(budget).strip() == "":
                budget = row[columns["BUDGET"]]

            records.append({
                "name": name,
                "headquarter": hq,
                "team": team,
                "budget": str(budget).strip() if pd.notna(budget) else "",
                "completion": str(row[completion_col]).strip() if completion_col and completion_col in df.columns and pd.notna(row[completion_col]) else "",
                "order_count": str(metric.get("order_count", "")).strip() if pd.notna(metric.get("order_count", "")) else "",
                "order_completion": str(metric.get("order_completion", "")).strip() if pd.notna(metric.get("order_completion", "")) else "",
                "invoice_count": str(metric.get("invoice_count", "")).strip() if pd.notna(metric.get("invoice_count", "")) else "",
                "invoice_completion": str(metric.get("invoice_completion", "")).strip() if pd.notna(metric.get("invoice_completion", "")) else "",
                "mark_city": align_echarts_city_name(mark_city),
                "mark_city_key": city_match_key(mark_city),
                "area": str(row[columns["AREA"]]).strip() if pd.notna(row[columns["AREA"]]) else "",
            })
        except:
            continue
    return records


def load_region_mappings(file_path, config=AppConfig):
    """读取全国二级营销区划分表。"""
    df = read_csv_auto(file_path)
    df.columns = [str(col).strip() for col in df.columns]

    hq_col = config.REGION_COLUMNS.get("HEADQUARTER", "营部")
    city_col = config.REGION_COLUMNS.get("CITY", "城市")
    team_col = config.REGION_COLUMNS.get("TEAM", "连队")

    if hq_col not in df.columns:
        raise ValueError(f"营销区划分表缺少必要列: '{hq_col}'。")
    if city_col not in df.columns:
        raise ValueError(f"营销区划分表缺少必要列: '{city_col}'。")
    if team_col not in df.columns:
        fallback_cols = [col for col in df.columns if col not in [hq_col, city_col]]
        team_col = fallback_cols[0] if fallback_cols else None

    mappings = []
    for _, row in df.iterrows():
        hq = str(row[hq_col]).strip() if pd.notna(row[hq_col]) else ""
        city = str(row[city_col]).strip() if pd.notna(row[city_col]) else ""
        team = str(row[team_col]).strip() if team_col and pd.notna(row[team_col]) else ""
        if not hq or not city or hq in ["nan", "None"] or city in ["nan", "None"]:
            continue
        mappings.append({
            "headquarter": hq,
            "team": team,
            "city": align_echarts_city_name(city),
        })
    return mappings
