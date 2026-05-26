# -*- coding: utf-8 -*-
import json
import os
import shutil
from dataclasses import dataclass
from typing import Optional


@dataclass
class MapGenerationTask:
    region: dict
    map_label: str
    records: list
    output_html: str
    output_data: str
    option_json: str
    count_unit: str
    export_kind: str
    salesperson_points: Optional[list] = None
    legacy_output_html: Optional[str] = None

    @property
    def record_count(self):
        if self.salesperson_points is not None:
            return len(self.salesperson_points)
        return len(self.records)

    @property
    def count_label(self):
        return f"{self.record_count} {self.count_unit}"


def build_generation_tasks(regions, market_records, team_records, salesperson_records, config, data_adapter):
    tasks = []
    option_dir = os.path.join(config.OUTPUT_DIR, config.Files.MAP_DATA_DIR)
    title_prefix = f"{config.CURRENT_MONTH} " if getattr(config, "CURRENT_MONTH", "") else ""

    for region in regions:
        team_region = dict(region)
        team_region["title"] = f"{title_prefix}{region['name']}{config.MapTypes.TEAM_DEPLOYMENT}"
        region_dir = os.path.join(config.OUTPUT_DIR, region["output_group"])
        region_records = data_adapter.filter_by_region(team_records, region)
        team_map_id = data_adapter.safe_filename(f"{region['name']}_{config.MapTypes.TEAM_DEPLOYMENT}")

        tasks.append(MapGenerationTask(
            region=team_region,
            map_label=config.MapTypes.TEAM_DEPLOYMENT,
            records=region_records,
            output_html=os.path.join(region_dir, region["html_name"]),
            output_data=os.path.join(region_dir, region["data_name"]),
            option_json=os.path.join(option_dir, f"{team_map_id}.json"),
            count_unit=config.MapTypes.TEAM_COUNT_UNIT,
            export_kind="team",
            legacy_output_html=config.OUTPUT_HTML if region.get("id") == "national" else None,
        ))

        if salesperson_records:
            salesperson_region = dict(region)
            salesperson_region["title"] = f"{title_prefix}{region['name']}{config.MapTypes.SALESPERSON_DEPLOYMENT}"
            region_salespersons = data_adapter.filter_salespersons_by_region(salesperson_records, region)
            salesperson_map_id = data_adapter.safe_filename(f"{region['name']}_{config.MapTypes.SALESPERSON_DEPLOYMENT}")

            tasks.append(MapGenerationTask(
                region=salesperson_region,
                map_label=config.MapTypes.SALESPERSON_DEPLOYMENT,
                records=data_adapter.filter_by_region(market_records, region),
                output_html=os.path.join(region_dir, f"{region['name']}{config.MapTypes.SALESPERSON_DEPLOYMENT}.html"),
                output_data=os.path.join(region_dir, f"{region['name']}{config.MapTypes.SALESPERSON_DEPLOYMENT}_数据.csv"),
                option_json=os.path.join(option_dir, f"{salesperson_map_id}.json"),
                count_unit=config.MapTypes.SALESPERSON_COUNT_UNIT,
                export_kind="salesperson",
                salesperson_points=region_salespersons,
            ))

    return tasks


def render_generation_task(task, config, chart_factory, html_enhancer, data_adapter, runtime_config_builder):
    os.makedirs(os.path.dirname(task.output_html), exist_ok=True)
    os.makedirs(os.path.dirname(task.option_json), exist_ok=True)

    runtime_config = runtime_config_builder(config, task.region)
    chart = chart_factory.build_china_city_map(
        task.records,
        runtime_config,
        salesperson_points=task.salesperson_points,
    )
    chart.render(task.output_html)
    html_enhancer(task.output_html)
    option = json.loads(chart.dump_options_with_quotes())
    _restore_js_newlines(option)
    _externalize_shared_layers(option, os.path.dirname(task.option_json))
    with open(task.option_json, "w", encoding="utf-8") as f:
        json.dump(option, f, ensure_ascii=False, separators=(",", ":"))

    if task.export_kind == "salesperson":
        data_adapter.export_salesperson_data(task.salesperson_points or [], task.output_data)
    else:
        data_adapter.export_region_data(task.records, task.output_data)

    if task.legacy_output_html:
        shutil.copyfile(task.output_html, task.legacy_output_html)


def _externalize_shared_layers(option, option_dir):
    shared_boundary_name = "province_boundaries.json"
    series = option.get("series") or []
    compact_series = []

    for item in series:
        if item.get("type") == "lines" and item.get("name") == "省级边界":
            boundary_path = os.path.join(option_dir, shared_boundary_name)
            if not os.path.exists(boundary_path):
                with open(boundary_path, "w", encoding="utf-8") as f:
                    json.dump(item.get("data", []), f, ensure_ascii=False, separators=(",", ":"))
            continue
        compact_series.append(item)

    option["series"] = compact_series


def _restore_js_newlines(value):
    """Repair JsCode newlines lost by dump_options_with_quotes for JSON viewer."""
    if isinstance(value, list):
        for item in value:
            _restore_js_newlines(item)
        return

    if isinstance(value, dict):
        for key, item in list(value.items()):
            if isinstance(item, str) and "function" in item:
                value[key] = (
                    item
                    .replace("lines.join('')", "lines.join('\\n')")
                    .replace("String(name) + '' + budgetLine", "String(name) + '\\n' + budgetLine")
                    .replace("String(name) + '' + orderLine", "String(name) + '\\n' + orderLine")
                    .replace("return (data.teamName || '') + ''       + sales", "return (data.teamName || '') + '\\n'       + sales")
                    .replace("return lines.join('          ');", "return lines.join('\\n          ');")
                )
            else:
                _restore_js_newlines(item)


def task_to_index_item(task):
    return {
        "region_name": task.region["name"],
        "map_label": task.map_label,
        "record_count": task.record_count,
        "count_label": task.count_label,
        "html_path": task.output_html,
        "data_path": task.output_data,
        "json_path": task.option_json,
        "map_id": os.path.splitext(os.path.basename(task.option_json))[0],
    }
