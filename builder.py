# -*- coding: utf-8 -*-
from pyecharts.charts import Geo
from pyecharts.commons.utils import JsCode
from pyecharts import options as opts
from pyecharts.globals import ThemeType, ChartType

import map_layers

class ChartFactory:
    """终极图表工厂：智能自适应数据格式，并通过底层原生扩展，100%强力渲染省界线"""

    @staticmethod
    def build_china_city_map(data_pairs, config, salesperson_points=None):
        """
        核心渲染方法：
        完美兼容新老配置，将省份边界直接注册在原生热力层，杜绝图层被覆盖、不显示的问题。
        """
        
        # 1. 🛡️ 智能解耦与动态极值计算
        map_values = []
        point_values = []
        
        if data_pairs:
            for v in data_pairs:
                try:
                    if isinstance(v, dict):
                        m_val = v.get("map_val", 0)
                        p_val = v.get("point_val", None)
                    else:
                        m_val = v[1] if len(v) > 1 else 0
                        p_val = v[2] if len(v) > 2 else None
                    
                    if m_val and float(m_val) > 0:
                        map_values.append(float(m_val))
                    if p_val is not None and float(p_val) > 0:
                        point_values.append(float(p_val))
                except:
                    continue

            max_map = max(map_values) if map_values else 10000
            min_map = min(map_values) if map_values else 0
            max_point = max(point_values) if point_values else 10000
            min_point = min(point_values) if point_values else 0
        else:
            max_map, min_map = 10000, 0
            max_point, min_point = 10000, 0

        # 安全获取主题
        theme_style = getattr(config, "THEME_STYLE", "white")
        theme_map = {
            "white": ThemeType.WHITE,
            "dark": ThemeType.DARK,
            "chalk": ThemeType.CHALK,
            "essos": ThemeType.ESSOS
        }
        selected_theme = theme_map.get(theme_style.lower(), ThemeType.WHITE)

        # 2. 初始化 Geo 容器
        # ⚡ 核心改动：把基础底图切换为具有天然省份轮廓基础的注册机制，同时给地级市描边为白色
        geo = (
            Geo(init_opts=opts.InitOpts(theme=selected_theme, width="100vw", height="100vh"))
            .add_schema(
                maptype="china-cities",
                is_roam=True,
                itemstyle_opts=opts.ItemStyleOpts(
                    area_color="#f8f9fa",       
                    border_color="#ffffff",     # 市级内部线条设为纯白
                    border_width=0.6,           
                    opacity=1                   
                ),
                emphasis_itemstyle_opts=opts.ItemStyleOpts(
                    area_color="#cce5ff",       
                    border_color="#333333",
                    border_width=1
                )
            )
        )

        # 3. 🗺️ 动态适配转换数据集
        safe_map_data = []    
        safe_point_data = []
        safe_point_meta = []

        for v in data_pairs:
            try:
                if isinstance(v, dict):
                    city = v.get("city")
                    m_val = v.get("map_val", 0)
                    p_val = v.get("point_val", None)
                    point_meta = {
                        "headquarter": v.get("troop_headquarter", v.get("headquarter", "")),
                        "team_name": v.get("team_name", ""),
                        "team_sales": v.get("team_sales", p_val),
                        "team_share": v.get("team_share", ""),
                        "deployment": v.get("deployment", ""),
                        "captain": v.get("captain", ""),
                        "members": v.get("members", ""),
                        "budget": v.get("budget", "")
                    }
                else:
                    city = v[0]
                    m_val = v[1] if len(v) > 1 else 0
                    p_val = v[2] if len(v) > 2 else None
                    point_meta = {
                        "headquarter": "",
                        "team_name": "",
                        "team_sales": p_val,
                        "team_share": "",
                        "deployment": "",
                        "captain": "",
                        "members": "",
                        "budget": ""
                    }

                if not city:
                    continue
                    
                target_city = str(city).strip()
                point_coordinate = map_layers.resolve_map_coordinate(geo, target_city)
                if point_coordinate is None:
                    short_city = target_city.replace("自治州", "").replace("蒙古", "").replace("哈萨克", "").replace("柯尔克孜", "").strip()
                    if map_layers.resolve_map_coordinate(geo, short_city) is not None:
                        target_city = short_city
                    else:
                        continue 
                if geo.get_coordinate(target_city) is None and point_coordinate is not None:
                    geo.add_coordinate(target_city, point_coordinate[0], point_coordinate[1])

                safe_map_data.append((target_city, float(m_val) if m_val else 0.0))
                
                if p_val is not None and float(p_val) >= 0:
                    safe_point_data.append((target_city, float(p_val)))
                    safe_point_meta.append(point_meta)
            except:
                continue

        # 配置项安全降级提取（完美融合新老 Config 结构）
        market_name = getattr(getattr(config, "Market", config), "SERIES_NAME", "市场容量")
        market_unit = getattr(getattr(config, "Market", config), "DATA_UNIT", "台")
        color_range = getattr(getattr(config, "Market", config), "COLOR_RANGE", ["#fff7bc", "#fec44f", "#d95f0e", "#990000"])
        
        team_name = getattr(getattr(config, "Team", config), "SERIES_NAME", "团队规模")
        symbol_color = getattr(getattr(config, "Team", config), "SYMBOL_COLOR", "#00aeff")
        size_range = getattr(getattr(config, "Team", config), "SIZE_RANGE", [6, 25])

        # -----------------------------------------------------------
        # 🗺️ 图层 0：原生地图色块图层（直接在此图层注入 Echarts 底层黑线省界控制）
        # -----------------------------------------------------------
        native_map_series = {
            "type": "map",
            "name": f"{market_name} ({market_unit})",
            "map": "china-cities",
            "geoIndex": 0, 
            "data": [{"name": k, "value": v} for k, v in safe_map_data], 
            "label": {"show": False},
            "roam": False,
            "animation": False,
            # ⚡⚡ 核心技术突破点：直接通过 Echarts 原生样式覆盖机制，强制在市级色块聚合的边缘描出深灰色粗线条（省界轮廓）
            "itemStyle": {
                "normal": {
                    "borderColor": "#555555",       # 强制省界/国界为深灰色
                    "borderWidth": 1.5,             # 边界加粗至 1.5
                    "borderType": "solid"
                }
            }
        }
        geo.options["series"].append(native_map_series)

        # -----------------------------------------------------------
        # 🎯 图层 1：散点图层（物理层级最高，确保营销团队圆点清晰可见）
        # -----------------------------------------------------------
        geo.add(
            series_name=team_name,
            data_pair=safe_point_data, 
            type_=ChartType.SCATTER, 
            label_opts=opts.LabelOpts(is_show=False)
        )
        scatter_series = geo.options["series"][-1]
        for index, (item, meta) in enumerate(zip(scatter_series.get("data", []), safe_point_meta)):
            item["headquarter"] = meta.get("headquarter", "")
            item["teamName"] = meta.get("team_name") or item.get("name", "")
            item["teamSales"] = meta.get("team_sales", "")
            item["teamShare"] = meta.get("team_share", "")
            item["deployment"] = meta.get("deployment", "")
            item["captain"] = meta.get("captain", "")
            item["members"] = meta.get("members", "")
            item["teamBudget"] = meta.get("budget", "")
            item["label"] = map_layers.point_label_layout(item.get("name", ""), index)

        min_symbol_size, max_symbol_size = size_range
        scatter_series.update({
            "id": "team-point-layer",
            "tooltip": {
                "show": True,
                "trigger": "item",
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "padding": 0,
                "textStyle": {
                    "color": "#1f2933",
                    "fontSize": 12,
                    "fontFamily": "Microsoft YaHei, Arial"
                },
                "formatter": JsCode(
                    "function(params) {"
                    "  var data = params.data || {};"
                    "  var lines = [];"
                    "  var sales = data.teamSales !== undefined && data.teamSales !== null ? data.teamSales : '';"
                    "  var share = data.teamShare || '';"
                    "  var budget = data.teamBudget || '';"
                    "  var hq = data.headquarter || '';"
                    "  var colors = {"
                    "    '西南大营': '#0052cc',"
                    "    '向西大营': '#ff7a00',"
                    "    '东南大营': '#00a651',"
                    "    '中原大营': '#7b2cbf',"
                    "    '泰山大营': '#d00000',"
                    "    '长江大营': '#111827'"
                    "  };"
                    "  var color = colors[hq] || '#0841eb';"
                    "  var esc = function(value) {"
                    "    return String(value === undefined || value === null ? '' : value)"
                    "      .replace(/&/g, '&amp;').replace(/</g, '&lt;')"
                    "      .replace(/>/g, '&gt;').replace(/\\\"/g, '&quot;').replace(/'/g, '&#39;');"
                    "  };"
                    "  lines.push(['连队', data.teamName || '']);"
                    "  lines.push(['26年预算目标', budget === '' ? '' : budget + '台']);"
                    "  lines.push(['连队销量', sales === '' ? '' : sales + '台']);"
                    "  lines.push(['市占率', share]);"
                    "  lines.push(['人数', data.deployment || '']);"
                    "  lines.push(['连长', data.captain || '']);"
                    "  lines.push(['团队成员', data.members || '']);"
                    "  var body = lines.map(function(row) {"
                    "    return '<div style=\"display:flex;gap:10px;align-items:flex-start;margin-top:5px;\">'"
                    "      + '<span style=\"flex:0 0 84px;color:#5b6673;\">' + esc(row[0]) + '</span>'"
                    "      + '<span style=\"max-width:280px;color:#1f2933;font-weight:600;white-space:normal;\">' + esc(row[1]) + '</span>'"
                    "      + '</div>';"
                    "  }).join('');"
                    "  return '<div style=\"min-width:210px;max-width:380px;background:rgba(255,255,255,0.98);'"
                    "    + 'border:3px solid ' + color + ';border-left-width:10px;border-radius:8px;'"
                    "    + 'box-shadow:0 8px 24px rgba(15,23,42,0.18);padding:10px 12px;'"
                    "    + 'font:12px/1.45 Microsoft YaHei,Arial,sans-serif;\">'"
                    "    + '<div style=\"display:flex;align-items:center;justify-content:space-between;gap:12px;'"
                    "    + 'margin-bottom:6px;padding-bottom:6px;border-bottom:1px solid #e5e7eb;\">'"
                    "    + '<span style=\"font-size:13px;font-weight:700;color:' + color + ';\">' + esc(hq || '连队信息') + '</span>'"
                    "    + '<span style=\"width:12px;height:12px;border-radius:999px;background:' + color + ';display:inline-block;\"></span>'"
                    "    + '</div>' + body + '</div>';"
                    "}"
                )
            },
            "z": 50,
            "zlevel": 5,
            "symbolSize": JsCode(
                "function(value) {"
                f"  var minValue = {float(min_point)};"
                f"  var maxValue = {float(max_point)};"
                f"  var minSize = {float(min_symbol_size)};"
                f"  var maxSize = {float(max_symbol_size)};"
                "  var sales = value && value.length > 2 ? Number(value[2]) : minValue;"
                "  if (!isFinite(sales)) { return minSize; }"
                "  if (maxValue <= minValue) { return (minSize + maxSize) / 2; }"
                "  var ratio = (sales - minValue) / (maxValue - minValue);"
                "  ratio = Math.max(0, Math.min(1, ratio));"
                "  return minSize + ratio * (maxSize - minSize);"
                "}"
            ),
            "label": {
                "show": False,
                "position": "right",
                "distance": 8,
                "formatter": JsCode(
                    "function(params) {"
                    "  var data = params.data || {};"
                    "  var sales = data.teamSales !== undefined && data.teamSales !== null ? data.teamSales : '';"
                    "  var share = data.teamShare || '';"
                    "  var deployment = data.deployment || '';"
                    "  var wrap = function(text) {"
                    "    if (!text) { return ''; }"
                    "    var parts = String(text).split(/、|,|，/);"
                    "    var lines = [];"
                    "    var line = '';"
                    "    for (var i = 0; i < parts.length; i++) {"
                    "      var part = parts[i];"
                    "      var next = line ? line + '、' + part : part;"
                    "      if (next.length > 10 && line) { lines.push(line); line = part; }"
                    "      else { line = next; }"
                    "    }"
                    "    if (line) { lines.push(line); }"
                    "    return lines.join('\\n          ');"
                    "  };"
                    "  return (data.teamName || '') + '\\n'"
                    "       + sales + '台/' + share;"
                    "}"
                ),
                "backgroundColor": "rgba(255,255,255,0.96)",
                "borderColor": symbol_color,
                "borderWidth": 1,
                "borderRadius": 4,
                "padding": [3, 5],
                "color": "#1f2933",
                "fontSize": 9,
                "fontWeight": "bold",
                "lineHeight": 12,
                "align": "left"
            },
            "labelLayout": {
                "hideOverlap": False
            },
            "emphasis": {
                "disabled": False,
                "label": {
                    "show": True
                }
            }
        })

        team_label_data = []
        for item in scatter_series.get("data", []):
            point_value = item.get("value", [])
            if len(point_value) < 2:
                continue
            team_label_data.append([
                point_value[0],
                point_value[1],
                item.get("teamSales", ""),
                item.get("teamName", ""),
                item.get("teamShare", ""),
                item.get("deployment", ""),
                item.get("headquarter", "")
            ])
        geo.options["series"].append({
            "type": "custom",
            "id": "team-label-layer",
            "name": "连队气泡标签",
            "coordinateSystem": "geo",
            "data": team_label_data,
            "silent": True,
            "z": 80,
            "zlevel": 8,
            "renderItem": map_layers.team_label_render_item(symbol_color),
            "tooltip": {"show": False}
        })
        if salesperson_points:
            map_layers.append_salesperson_layer(geo, salesperson_points, config)

        map_layers.append_vietnam_layers(geo)
        map_layers.append_province_boundary_layer(geo, config)

        # 4. 全局交互与标题配置
        geo.set_global_opts(
            title_opts=opts.TitleOpts(
                is_show=False,
                title=getattr(config, "TITLE", "地图展示大盘"),
                pos_left="center",
                pos_top="20px",
                title_textstyle_opts=opts.TextStyleOpts(font_size=22, font_weight="bold")
            ),
            tooltip_opts=opts.TooltipOpts(
                trigger="item",
                formatter=f"{{b}}<br/>{market_name}: {{c}} {market_unit}"
            )
        )

        # 5. 独立双通道视觉映射（精准对齐新的图层索引：0为色块，1为散点）
        geo.options["visualMap"] = [
            {
                "type": "continuous",
                "min": min_map,
                "max": max_map,
                "seriesIndex": 0,          # 联动图层 0：带有省界渲染的市级色块
                "calculable": True,
                "left": "5%",
                "bottom": "5%",
                "inRange": {
                    "color": color_range
                }
            },
            {
                "type": "continuous",
                "min": min_point,
                "max": max_point,
                "seriesIndex": 1,          # 联动图层 1：核心散点
                "show": False,             
                "inRange": {
                    "color": [symbol_color, symbol_color] 
                }
            }
        ]
        if team_label_data:
            map_layers.append_team_legend(geo, team_label_data, symbol_color)

        return geo

