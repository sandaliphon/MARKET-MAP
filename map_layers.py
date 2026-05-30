# -*- coding: utf-8 -*-
import json
import os

from pyecharts.commons.utils import JsCode


def point_label_layout(city_name, index):
    city_layouts = {
        "成都市": {"position": "top", "offset": [0, -16]},
        "南宁市": {"position": "bottom", "offset": [0, 16]},
        "昆明市": {"position": "right", "offset": [18, 0]},
        "泸州市": {"position": "right", "offset": [18, -10]},
        "东莞市": {"position": "right", "offset": [18, 10]},
    }
    if city_name in city_layouts:
        layout = city_layouts[city_name].copy()
    else:
        fallback_layouts = [
            {"position": "right", "offset": [18, -10]},
            {"position": "right", "offset": [18, 10]},
            {"position": "top", "offset": [0, -16]},
            {"position": "bottom", "offset": [0, 16]},
            {"position": "left", "offset": [-18, 10]},
            {"position": "left", "offset": [-18, -10]},
        ]
        layout = fallback_layouts[index % len(fallback_layouts)].copy()
    layout["show"] = False
    layout["distance"] = 16
    return layout


def append_team_legend(geo, team_label_data, symbol_color):
    if not team_label_data:
        return

    bubble_width = 130
    bubble_height = 34
    children = [
        {
            "type": "rect",
            "shape": {"x": 0, "y": 0, "width": bubble_width, "height": bubble_height, "r": 4},
            "style": {
                "fill": "rgba(255,255,255,0.96)",
                "stroke": symbol_color,
                "lineWidth": 1,
            },
        },
        {
            "type": "text",
            "style": {
                "x": 6,
                "y": 4,
                "text": "xx连队\n1-4月销量/市占率",
                "fill": "#1f2933",
                "font": "bold 9px Microsoft YaHei, Arial",
                "textAlign": "left",
                "textVerticalAlign": "top",
                "lineHeight": 12,
            },
        },
    ]

    if not isinstance(geo.options.get("graphic"), list):
        geo.options["graphic"] = []
    geo.options["graphic"].append({
        "type": "group",
        "right": 22,
        "bottom": 24,
        "z": 120,
        "children": children,
    })


def append_vietnam_layers(geo):
    outline = vietnam_outline()
    geo.options["series"].append({
        "type": "custom",
        "name": "越南区域",
        "coordinateSystem": "geo",
        "data": [0],
        "silent": True,
        "z": 5,
        "zlevel": 1,
        "renderItem": JsCode(
            "function(params, api) {"
            "  var coords = " + json.dumps(outline) + ";"
            "  var points = [];"
            "  for (var i = 0; i < coords.length; i++) { points.push(api.coord(coords[i])); }"
            "  return {"
            "    type: 'polygon',"
            "    shape: { points: points },"
            "    style: api.style({ fill: 'rgba(248,249,250,0.92)', stroke: '#c6cbd1', lineWidth: 1 })"
            "  };"
            "}"
        ),
        "tooltip": {"show": False},
    })
    geo.options["series"].append({
        "type": "lines",
        "name": "越南边界",
        "coordinateSystem": "geo",
        "polyline": True,
        "data": [{"name": "越南", "coords": outline}],
        "silent": True,
        "symbol": "none",
        "z": 6,
        "animation": False,
        "lineStyle": {
            "color": "#aeb4bb",
            "width": 1,
            "opacity": 0.9,
            "type": "solid",
        },
        "tooltip": {"show": False},
    })
    geo.options["series"].append({
        "type": "scatter",
        "name": "越南标注",
        "coordinateSystem": "geo",
        "data": [{"name": "越南", "value": [106.0, 16.2]}],
        "symbolSize": 0,
        "silent": True,
        "z": 7,
        "zlevel": 1,
        "label": {
            "show": True,
            "formatter": "越南",
            "position": "inside",
            "color": "#6b7280",
            "fontSize": 13,
            "fontWeight": "bold",
        },
        "tooltip": {"show": False},
    })


def append_province_boundary_layer(geo, config):
    boundary_lines = load_province_boundary_lines(config)
    if not boundary_lines:
        return

    geo.options["series"].append({
        "type": "lines",
        "name": "省级边界",
        "coordinateSystem": "geo",
        "polyline": True,
        "data": boundary_lines,
        "silent": True,
        "symbol": "none",
        "z": 20,
        "animation": False,
        "lineStyle": {
            "color": "#d0d4d9",
            "width": 1.4,
            "opacity": 0.75,
            "type": "solid",
        },
        "tooltip": {"show": False},
    })


def append_salesperson_layer(geo, salesperson_points, config):
    salesperson_cfg = getattr(config, "Salesperson", None)
    symbol_color = getattr(salesperson_cfg, "SYMBOL_COLOR", "#e11d48")
    size_range = getattr(salesperson_cfg, "SIZE_RANGE", [8, 22])
    series_name = getattr(salesperson_cfg, "SERIES_NAME", "销售员")
    offsets = [
        [0, 0], [20, 0], [-20, 0], [0, -20], [0, 20],
        [15, -15], [-15, 15], [15, 15], [-15, -15],
    ]
    city_counts = {}
    data = []
    label_data = []
    budgets = []
    for point in salesperson_points:
        try:
            budget_value = float(str(point.get("budget", "")).replace(",", ""))
            if budget_value > 0:
                budgets.append(budget_value)
        except:
            continue
    min_budget = min(budgets) if budgets else 0
    max_budget = max(budgets) if budgets else 0
    min_size, max_size = size_range
    def metric_number(value):
        try:
            text = str(value).replace(",", "").strip()
            if not text or text in ["nan", "None", "#DIV/0!"]:
                return 0.0
            return float(text)
        except:
            return 0.0

    top_label_names = {
        str(point.get("name", "")).strip()
        for point in sorted(
            salesperson_points,
            key=lambda item: metric_number(item.get("order_count", "")),
            reverse=True,
        )[:30]
        if str(point.get("name", "")).strip()
    }

    for point in salesperson_points:
        city = str(point.get("mark_city", "")).strip()
        if not city:
            continue
        target_city = city
        coordinate = resolve_salesperson_coordinate(geo, target_city)
        if coordinate is None:
            short_city = target_city.replace("自治州", "").replace("蒙古", "").replace("哈萨克", "").replace("柯尔克孜", "").strip()
            coordinate = resolve_salesperson_coordinate(geo, short_city)
            if coordinate is None:
                continue
            target_city = short_city

        index = city_counts.get(target_city, 0)
        city_counts[target_city] = index + 1
        offset = offsets[index % len(offsets)]
        data.append({
            "name": point.get("name", ""),
            "value": [coordinate[0], coordinate[1], point.get("budget", "")],
            "symbolOffset": offset,
            "markCity": target_city,
            "budget": point.get("budget", ""),
            "completion": point.get("completion", ""),
            "orderCount": point.get("order_count", ""),
            "orderCompletion": point.get("order_completion", ""),
            "invoiceCount": point.get("invoice_count", ""),
            "invoiceCompletion": point.get("invoice_completion", ""),
            "area": point.get("area", ""),
            "team": point.get("team", ""),
            "itemStyle": {
                "color": symbol_color,
                "borderColor": "#ffffff",
                "borderWidth": 1,
            },
        })
        label_data.append([
            coordinate[0],
            coordinate[1],
            point.get("name", ""),
            point.get("order_count", ""),
            offset[0],
            offset[1],
            1 if str(point.get("name", "")).strip() in top_label_names else 0,
        ])

    geo.options["series"].append({
        "type": "scatter",
        "id": "salesperson-point-layer",
        "name": series_name,
        "coordinateSystem": "geo",
        "data": data,
        "symbol": "circle",
        "symbolSize": JsCode(
            "function(value) {"
            f"  var minValue = {float(min_budget)};"
            f"  var maxValue = {float(max_budget)};"
            f"  var minSize = {float(min_size)};"
            f"  var maxSize = {float(max_size)};"
            "  var budget = value && value.length > 2 ? Number(value[2]) : minValue;"
            "  if (!isFinite(budget)) { return minSize; }"
            "  if (maxValue <= minValue) { return (minSize + maxSize) / 2; }"
            "  var ratio = (budget - minValue) / (maxValue - minValue);"
            "  ratio = Math.max(0, Math.min(1, ratio));"
            "  return minSize + ratio * (maxSize - minSize);"
            "}"
        ),
        "z": 90,
        "zlevel": 9,
        "label": {"show": False},
        "tooltip": {
            "show": True,
            "trigger": "item",
            "backgroundColor": "rgba(255,255,255,0.97)",
            "borderColor": symbol_color,
            "borderWidth": 1,
            "textStyle": {
                "color": "#1f2933",
                "fontSize": 12,
                "fontFamily": "Microsoft YaHei, Arial",
            },
            "formatter": JsCode(
                "function(params) {"
                "  var data = params.data || {};"
                "  var lines = [];"
                "  lines.push('姓名: ' + (data.name || ''));"
                "  lines.push('年度目标: ' + (data.budget || ''));"
                "  lines.push('订单数: ' + (data.orderCount || ''));"
                "  lines.push('订单年度达成率: ' + (data.orderCompletion || data.completion || ''));"
                "  lines.push('开票数: ' + (data.invoiceCount || ''));"
                "  lines.push('开票达成度: ' + (data.invoiceCompletion || ''));"
                "  lines.push('负责区域: ' + (data.area || ''));"
                "  return lines.join('<br/>');"
                "}"
            ),
        },
    })
    geo.options["series"].append({
        "type": "custom",
        "id": "salesperson-label-layer",
        "name": "销售员姓名气泡",
        "coordinateSystem": "geo",
        "data": label_data,
        "silent": True,
        "z": 95,
        "zlevel": 10,
        "renderItem": salesperson_label_render_item(symbol_color),
        "tooltip": {"show": False},
    })


def resolve_salesperson_coordinate(geo, city):
    return resolve_map_coordinate(geo, city)


def resolve_map_coordinate(geo, city):
    if city in ["越南", "河内", "海防"]:
        return [106.0, 21.4]
    return geo.get_coordinate(city)


def salesperson_label_render_item(symbol_color):
    return JsCode(
        "function(params, api) {"
        "  var ctx = params.context;"
        "  if (!ctx.salespersonRects) { ctx.salespersonRects = []; }"
        "  if (!ctx.salespersonPointRects) {"
        "    ctx.salespersonPointRects = [];"
        "    var fullData = params.seriesData || [];"
        "    for (var pi = 0; pi < fullData.length; pi++) {"
        "      var p = fullData[pi];"
        "      if (!p || !p.value) { continue; }"
        "      var pointCoord = api.coord([p.value[0], p.value[1]]);"
        "      if (!pointCoord || !isFinite(pointCoord[0]) || !isFinite(pointCoord[1])) { continue; }"
        "      var pointOffsetX = Number(p.value[4] || 0);"
        "      var pointOffsetY = Number(p.value[5] || 0);"
        "      var safeX = pointCoord[0] + pointOffsetX;"
        "      var safeY = pointCoord[1] + pointOffsetY;"
        "      ctx.salespersonPointRects.push({x:safeX - 17, y:safeY - 17, width:34, height:34});"
        "    }"
        "  }"
        "  var lon = api.value(0);"
        "  var lat = api.value(1);"
        "  var name = api.value(2) || '';"
        "  var orderCount = api.value(3) || '';"
        "  var offsetX = Number(api.value(4) || 0);"
        "  var offsetY = Number(api.value(5) || 0);"
        "  var point = api.coord([lon, lat]);"
        "  if (!point || !isFinite(point[0]) || !isFinite(point[1]) || !name) { return; }"
        "  var fontSize = 9;"
        "  var lineHeight = 12;"
        "  var paddingX = 5;"
        "  var paddingY = 3;"
        "  var orderLine = '订单：' + orderCount + '台';"
        "  var width = Math.max(50, Math.max(String(name).length, String(orderLine).length) * fontSize + paddingX * 2);"
        "  var height = lineHeight * 2 + paddingY * 2;"
        "  var anchorX = point[0] + offsetX;"
        "  var anchorY = point[1] + offsetY;"
        "  var distances = [18, 34, 52, 72, 96];"
        "  var dirs = [[1,0],[-1,0],[0,-1],[0,1],[1,-1],[1,1],[-1,-1],[-1,1]];"
        "  var overlap = function(a, b) {"
        "    return !(a.x + a.width < b.x || b.x + b.width < a.x || a.y + a.height < b.y || b.y + b.height < a.y);"
        "  };"
        "  var best = null;"
        "  for (var r = 0; r < distances.length && !best; r++) {"
        "    for (var di = 0; di < dirs.length; di++) {"
        "      var dx = dirs[di][0] * distances[r];"
        "      var dy = dirs[di][1] * distances[r];"
        "      var x = anchorX + dx;"
        "      var y = anchorY + dy;"
        "      if (dirs[di][0] < 0) { x -= width; }"
        "      else if (dirs[di][0] === 0) { x -= width / 2; }"
        "      if (dirs[di][1] < 0) { y -= height; }"
        "      else if (dirs[di][1] === 0) { y -= height / 2; }"
        "      var rect = {x:x, y:y, width:width, height:height};"
        "      var blocked = false;"
        "      for (var pri = 0; pri < ctx.salespersonPointRects.length; pri++) {"
        "        if (overlap(rect, ctx.salespersonPointRects[pri])) { blocked = true; break; }"
        "      }"
        "      for (var ri = 0; !blocked && ri < ctx.salespersonRects.length; ri++) {"
        "        if (overlap(rect, ctx.salespersonRects[ri])) { blocked = true; break; }"
        "      }"
        "      if (!blocked) { best = rect; break; }"
        "    }"
        "  }"
        "  if (!best) { best = {x: anchorX + 10, y: anchorY - height / 2, width: width, height: height}; }"
        "  ctx.salespersonRects.push(best);"
        "  var endX = Math.max(best.x, Math.min(anchorX, best.x + best.width));"
        "  var endY = Math.max(best.y, Math.min(anchorY, best.y + best.height));"
        "  return {"
        "    type: 'group',"
        "    children: ["
        "      {type:'line', shape:{x1:anchorX, y1:anchorY, x2:endX, y2:endY}, style:{stroke:'" + symbol_color + "', lineWidth:1, opacity:0.6}},"
        "      {type:'rect', shape:{x:best.x, y:best.y, width:best.width, height:best.height, r:4}, style:{fill:'rgba(255,255,255,0.96)', stroke:'" + symbol_color + "', lineWidth:1}},"
        "      {type:'text', style:{x:best.x + paddingX, y:best.y + paddingY, text:String(name) + '\\n' + orderLine, fill:'#1f2933', font:'bold 9px Microsoft YaHei, Arial', textAlign:'left', textVerticalAlign:'top', lineHeight:lineHeight}}"
        "    ]"
        "  };"
        "}"
    )


def team_label_render_item(symbol_color):
    return JsCode(
        "function(params, api) {"
        "  var ctx = params.context;"
        "  if (!ctx.rects) { ctx.rects = []; }"
        "  var lon = api.value(0);"
        "  var lat = api.value(1);"
        "  var sales = api.value(2);"
        "  var teamName = api.value(3) || '';"
        "  var teamShare = api.value(4) || '';"
        "  var hq = api.value(6) || '';"
        "  var colors = {"
        "    '西南大营': '#0052cc',"
        "    '向西大营': '#ff7a00',"
        "    '东南大营': '#00a651',"
        "    '中原大营': '#7b2cbf',"
        "    '泰山大营': '#d00000',"
        "    '长江大营': '#111827'"
        "  };"
        "  var color = colors[hq] || '" + symbol_color + "';"
        "  var point = api.coord([lon, lat]);"
        "  if (!point || !isFinite(point[0]) || !isFinite(point[1])) { return; }"
        "  var fontSize = 9;"
        "  var lineHeight = 12;"
        "  var paddingX = 6;"
        "  var paddingY = 3;"
        "  var measureTextWidth = function(text) {"
        "    text = String(text || '');"
        "    var width = 0;"
        "    for (var i = 0; i < text.length; i++) {"
        "      var code = text.charCodeAt(i);"
        "      if (code > 255) { width += fontSize; }"
        "      else if (/[A-Z0-9]/.test(text.charAt(i))) { width += fontSize * 0.68; }"
        "      else if (text.charAt(i) === ' ') { width += fontSize * 0.36; }"
        "      else { width += fontSize * 0.56; }"
        "    }"
        "    return width;"
        "  };"
        "  var wrap = function(text, maxWidth) {"
        "    if (!text) { return []; }"
        "    var parts = String(text).split(/、|,|，/);"
        "    var lines = [];"
        "    var line = '';"
        "    for (var i = 0; i < parts.length; i++) {"
        "      var part = parts[i];"
        "      var next = line ? line + '、' + part : part;"
        "      if (measureTextWidth(next) > maxWidth && line) { lines.push(line); line = part; }"
        "      else { line = next; }"
        "    }"
        "    if (line) { lines.push(line); }"
        "    return lines;"
        "  };"
        "  var lines = [];"
        "  if (teamName) { lines.push(String(teamName)); }"
        "  lines.push((sales == null ? '' : sales) + '台/' + teamShare);"
        "  var maxTextWidth = 0;"
        "  for (var m = 0; m < lines.length; m++) { maxTextWidth = Math.max(maxTextWidth, measureTextWidth(lines[m])); }"
        "  var width = Math.max(76, maxTextWidth + paddingX * 2 + 2);"
        "  var height = lines.length * lineHeight + paddingY * 2;"
        "  var distances = [18, 38, 62, 88, 116];"
        "  var dirs = [[1,0],[-1,0],[0,-1],[0,1],[1,-1],[1,1],[-1,-1],[-1,1]];"
        "  var best = null;"
        "  var overlap = function(a, b) {"
        "    return !(a.x + a.width < b.x || b.x + b.width < a.x || a.y + a.height < b.y || b.y + b.height < a.y);"
        "  };"
        "  for (var r = 0; r < distances.length && !best; r++) {"
        "    for (var di = 0; di < dirs.length; di++) {"
        "      var dx = dirs[di][0] * distances[r];"
        "      var dy = dirs[di][1] * distances[r];"
        "      var x = point[0] + dx;"
        "      var y = point[1] + dy;"
        "      if (dirs[di][0] < 0) { x -= width; }"
        "      else if (dirs[di][0] === 0) { x -= width / 2; }"
        "      if (dirs[di][1] < 0) { y -= height; }"
        "      else if (dirs[di][1] === 0) { y -= height / 2; }"
        "      var rect = {x:x, y:y, width:width, height:height};"
        "      var blocked = false;"
        "      for (var ri = 0; ri < ctx.rects.length; ri++) {"
        "        if (overlap(rect, ctx.rects[ri])) { blocked = true; break; }"
        "      }"
        "      if (!blocked) { best = rect; break; }"
        "    }"
        "  }"
        "  if (!best) {"
        "    best = {x: point[0] + 24, y: point[1] - height / 2, width: width, height: height};"
        "  }"
        "  ctx.rects.push(best);"
        "  var endX = Math.max(best.x, Math.min(point[0], best.x + best.width));"
        "  var endY = Math.max(best.y, Math.min(point[1], best.y + best.height));"
        "  return {"
        "    type: 'group',"
        "    children: ["
        "      {type:'line', shape:{x1:point[0], y1:point[1], x2:endX, y2:endY}, style:{stroke:color, lineWidth:1.4, opacity:0.78}},"
        "      {type:'rect', shape:{x:best.x, y:best.y, width:best.width, height:best.height, r:4}, style:{fill:'rgba(255,255,255,0.96)', stroke:color, lineWidth:2}},"
        "      {type:'rect', shape:{x:best.x, y:best.y, width:5, height:best.height, r:4}, style:{fill:color, stroke:color, lineWidth:0}},"
        "      {type:'text', style:{x:best.x + paddingX + 4, y:best.y + paddingY, text:lines.join('\\n'), fill:'#1f2933', font:'bold 9px Microsoft YaHei, Arial', textAlign:'left', textVerticalAlign:'top', lineHeight:lineHeight}}"
        "    ]"
        "  };"
        "}"
    )


def vietnam_outline():
    return [
        [105.30, 23.35],
        [106.20, 22.95],
        [107.50, 22.55],
        [108.25, 21.65],
        [107.80, 20.70],
        [106.95, 20.25],
        [106.55, 19.60],
        [106.20, 18.45],
        [106.60, 17.55],
        [107.35, 16.45],
        [108.20, 15.40],
        [109.20, 13.95],
        [109.30, 12.50],
        [109.05, 11.25],
        [107.80, 10.35],
        [106.85, 9.55],
        [105.65, 8.65],
        [104.75, 8.55],
        [104.55, 9.75],
        [105.10, 10.95],
        [105.75, 12.10],
        [106.05, 13.40],
        [107.05, 14.65],
        [107.50, 15.80],
        [107.15, 16.75],
        [106.50, 17.90],
        [105.75, 18.85],
        [105.05, 19.70],
        [104.50, 20.55],
        [103.65, 21.30],
        [102.75, 22.20],
        [103.40, 22.75],
        [104.35, 22.85],
        [105.30, 23.35],
    ]


def load_province_boundary_lines(config):
    boundary_file = getattr(config, "PROVINCE_BOUNDARY_JSON", None)
    if not boundary_file:
        base_dir = getattr(config, "BASE_DIR", os.getcwd())
        boundary_file = os.path.join(base_dir, "china_cities_boundaries.json")

    if not os.path.exists(boundary_file):
        return []

    try:
        with open(boundary_file, "r", encoding="utf-8") as f:
            geojson = json.load(f)
    except Exception:
        return []

    lines = []
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        if props.get("level") != "province":
            continue

        geometry = feature.get("geometry", {})
        coordinates = geometry.get("coordinates", [])
        if geometry.get("type") == "Polygon":
            polygons = [coordinates]
        elif geometry.get("type") == "MultiPolygon":
            polygons = coordinates
        else:
            continue

        for polygon in polygons:
            if not polygon:
                continue
            exterior_ring = polygon[0]
            if len(exterior_ring) < 2:
                continue
            lines.append({
                "name": props.get("name", ""),
                "coords": exterior_ring
            })

    return lines
