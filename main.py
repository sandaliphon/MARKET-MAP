# -*- coding: utf-8 -*-
import os
import sys
from types import SimpleNamespace

from builder import ChartFactory
from config import AppConfig
from generation_tasks import build_generation_tasks, render_generation_task, task_to_index_item
from site_builder import enhance_html, write_index
from utils import DataAdapter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def build_runtime_config(base_config, region):
    """为单张地图生成运行时配置，避免修改全局 AppConfig。"""
    return SimpleNamespace(
        BASE_DIR=base_config.BASE_DIR,
        THEME_STYLE=base_config.THEME_STYLE,
        TITLE=region.get("title") or base_config.TITLE,
        Market=base_config.Market,
        Team=base_config.Team,
        Salesperson=base_config.Salesperson,
    )


def main():
    print(AppConfig.Messages.BANNER)

    csv_path = AppConfig.DATA_PATH
    troop_path = AppConfig.TROOP_PATH
    troop_monthly_path = AppConfig.TROOP_MONTHLY_PATH
    salesperson_path = AppConfig.SALESPERSON_PATH
    if not os.path.exists(csv_path):
        print(f"❌ 报错：未在指定目录下找到数据文件 '{csv_path}'")
        print(f"💡 解决办法：请把 {AppConfig.Files.MARKET_DATA_DISPLAY} 放置在: {AppConfig.BASE_DIR} 目录下。")
        return
    if not os.path.exists(troop_path):
        print(f"❌ 报错：未在指定目录下找到兵力部署文件 '{troop_path}'")
        print(f"💡 解决办法：请把 {AppConfig.Files.TROOP_DATA_DISPLAY} 放置在: {AppConfig.BASE_DIR} 目录下。")
        return
    if not os.path.exists(troop_monthly_path):
        print(f"❌ 报错：未在指定目录下找到月度兵力部署文件 '{troop_monthly_path}'")
        print(f"💡 解决办法：请把 {AppConfig.Files.TROOP_MONTHLY_DATA_DISPLAY} 放置在: {AppConfig.BASE_DIR} 目录下。")
        return

    try:
        print(f"--> 正在读取市场热力数据: {AppConfig.Files.MARKET_DATA_DISPLAY}")
        market_records = DataAdapter.load_market_data(csv_path, AppConfig)
        print(f"--> 正在读取圆点兵力数据: {AppConfig.Files.TROOP_DATA_DISPLAY}")
        print(f"--> 正在读取月度兵力指标: {AppConfig.Files.TROOP_MONTHLY_DATA_DISPLAY}")
        troop_records = DataAdapter.load_troop_data(troop_path, AppConfig)
        clean_records = DataAdapter.merge_market_and_troop_data(market_records, troop_records)
        if os.path.exists(salesperson_path):
            print(f"--> 正在读取销售员标记点数据: {AppConfig.Files.SALESPERSON_DATA_DISPLAY}")
            if os.path.exists(AppConfig.SALESPERSON_MONTHLY_PATH):
                print(f"--> 正在读取销售员月度销量: {AppConfig.Files.SALESPERSON_MONTHLY_DATA_DISPLAY}")
            salesperson_records = DataAdapter.load_salesperson_data(salesperson_path, AppConfig)
        else:
            print(f"--> 未找到 {AppConfig.Files.SALESPERSON_DATA_DISPLAY}，跳过销售员地图。")
            salesperson_records = []
        mapping_path = DataAdapter.resolve_region_mapping_path(AppConfig)
        if mapping_path:
            print(f"--> 正在读取营销区划分表: {mapping_path}")
            region_mappings = DataAdapter.load_region_mappings(mapping_path, AppConfig)
            regions = DataAdapter.build_regions_from_mappings(region_mappings, AppConfig)
        else:
            print("--> 未找到营销区划分表，仅生成全国图。")
            regions = [AppConfig.NATIONAL_REGION]

        os.makedirs(AppConfig.OUTPUT_DIR, exist_ok=True)
        generated_items = []

        tasks = build_generation_tasks(
            regions,
            market_records,
            clean_records,
            salesperson_records,
            AppConfig,
            DataAdapter,
        )

        for task in tasks:
            print(f"--> 正在生成 {task.region['name']} {task.map_label}: {task.count_label}")
            render_generation_task(
                task,
                AppConfig,
                ChartFactory,
                enhance_html,
                DataAdapter,
                build_runtime_config,
            )
            generated_items.append(task_to_index_item(task))

        write_index(generated_items, AppConfig.OUTPUT_DIR)

        print(f"\n{AppConfig.Messages.SUCCESS}")
        print(f"👉 网站入口: {os.path.join(AppConfig.OUTPUT_DIR, AppConfig.Files.INDEX_HTML)}")
        print(f"👉 兼容旧入口: {AppConfig.OUTPUT_HTML}")

    except Exception as e:
        print(f"\n❌ 程序运行期间发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
