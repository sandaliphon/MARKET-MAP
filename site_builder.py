# -*- coding: utf-8 -*-
import json
import os
import shutil

from config import AppConfig


def enhance_html(output_html, enable_label_toggle=True):
    """给 pyecharts 生成的 HTML 注入全屏样式、气泡开关和自适应逻辑。"""
    with open(output_html, "r", encoding="utf-8") as f:
        html = f.read()

    full_width_style = (
        "<style>"
        "html,body{margin:0;padding:0;width:100vw;height:100vh;overflow:hidden;}"
        ".chart-container{width:100vw!important;height:100vh!important;max-width:100vw;max-height:100vh;}"
        ".label-toggle-panel{position:fixed;right:18px;top:18px;z-index:9999;"
        "display:flex;align-items:center;gap:8px;padding:8px 10px;"
        "background:rgba(255,255,255,0.92);border:1px solid #d8dde3;"
        "border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,0.12);"
        "font:12px/1.2 Arial,'Microsoft YaHei',sans-serif;color:#1f2933;}"
        ".label-toggle-panel input{margin:0;}"
        "</style>"
    )
    if full_width_style in html:
        return

    html = html.replace("</head>", f"{full_width_style}\n</head>")
    if enable_label_toggle:
        toggle_panel = (
            '<div class="label-toggle-panel">'
            '<input id="team-label-toggle" type="checkbox" checked>'
            f'<label for="team-label-toggle">{AppConfig.Site.LABEL_TOGGLE_TEXT}</label>'
            "</div>"
        )
        html = html.replace("<body >", f"<body >\n{toggle_panel}", 1)

    resize_script = (
        "<script>"
        "(function(){"
        "function getChart(){"
        "  for(var k in window){"
        "    if(k.indexOf('chart_')===0&&window[k]&&window[k].getOption){return window[k];}"
        "  }"
        "  return null;"
        "}"
        "function applyTeamLabelMode(alwaysShow){"
        "  var chart=getChart();"
        "  if(!chart){return;}"
        "  var option=chart.getOption();"
        "  var series=option.series||[];"
        "  for(var i=0;i<series.length;i++){"
        "    var s=series[i];"
        "    if(s.id==='team-label-layer'||s.id==='salesperson-label-layer'){"
        "      window.__labelDataCache=window.__labelDataCache||{};"
        "      if(!window.__labelDataCache[s.id]&&s.data&&s.data.length){window.__labelDataCache[s.id]=s.data;}"
        "      s.data=alwaysShow?(window.__labelDataCache[s.id]||s.data||[]):[];"
        "    }"
        "    if(s.id==='team-point-layer'){"
        "      s.label=s.label||{};"
        "      s.label.show=false;"
        "      s.emphasis=s.emphasis||{};"
        "      s.emphasis.disabled=false;"
        "      s.emphasis.label=s.emphasis.label||{};"
        "      s.emphasis.label.show=true;"
        "      var data=s.data||[];"
        "      for(var j=0;j<data.length;j++){"
        "        data[j].label=data[j].label||{};"
        "        data[j].label.show=false;"
        "      }"
        "    }"
        "  }"
        "  chart.setOption({series:series});"
        "}"
        "var toggle=document.getElementById('team-label-toggle');"
        "if(toggle){"
        "  toggle.addEventListener('change',function(){applyTeamLabelMode(this.checked);});"
        "}"
        "})();"
        "window.addEventListener('resize',function(){"
        "  for(var k in window){"
        "    if(k.indexOf('chart_')===0&&window[k]&&window[k].resize){window[k].resize();}"
        "  }"
        "});"
        "</script>"
    )
    html = html.replace("</body>", f"{resize_script}\n</body>")

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)


def write_index_legacy_two_pane(generated_items, output_dir):
    """生成一个静态入口页，便于整体浏览和按区域进入。"""
    grouped_items = {}
    for item in generated_items:
        grouped_items.setdefault(item["region_name"], []).append(item)

    cards = []
    for region_name, items in grouped_items.items():
        actions = []
        summaries = []
        for item in items:
            html_rel = os.path.relpath(item["html_path"], output_dir).replace("\\", "/")
            viewer_rel = f"{AppConfig.Files.VIEWER_HTML}?map={item['map_id']}"
            actions.append(
                f"<a href=\"{viewer_rel}\">{item['map_label']}轻量打开</a>"
                f"<a class=\"download-link\" href=\"{html_rel}\" download>{item['map_label']}完整HTML</a>"
            )
            summaries.append(f"{item['map_label']}：{item.get('count_label', '')}")
        cards.append(
            "      <article class=\"region-card\">"
            f"<h2>{region_name}</h2>"
            f"<p>{' / '.join(summaries)}</p>"
            f"<div class=\"map-actions\">{''.join(actions)}</div>"
            "</article>"
        )

    html = (
        "<!DOCTYPE html>\n"
        "<html lang=\"zh-CN\">\n"
        "<head>\n"
        "  <meta charset=\"UTF-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        f"  <title>{AppConfig.Site.TITLE}</title>\n"
        "  <style>\n"
        "    body{margin:0;font-family:Arial,'Microsoft YaHei',sans-serif;background:#f5f7fa;color:#1f2933;}\n"
        "    header{padding:28px 36px;background:#ffffff;border-bottom:1px solid #e1e5ea;}\n"
        "    h1{margin:0;font-size:24px;}\n"
        "    main{padding:28px 36px;display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;}\n"
        "    .region-card{background:#ffffff;border:1px solid #e1e5ea;border-radius:8px;padding:18px;}\n"
        "    .region-card h2{margin:0 0 8px;font-size:18px;}\n"
        "    .region-card p{margin:0 0 14px;color:#5b6673;font-size:13px;}\n"
        "    .map-actions{display:flex;gap:10px;flex-wrap:wrap;}\n"
        "    .region-card a{display:inline-flex;align-items:center;justify-content:center;min-width:86px;height:32px;padding:0 12px;background:#0b67c2;color:#ffffff;border-radius:6px;text-decoration:none;font-size:14px;}\n"
        "    .region-card a.download-link{background:#4b5563;}\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        f"  <header><h1>{AppConfig.Site.HEADER}</h1></header>\n"
        "  <main>\n"
        + "\n".join(cards)
        + "\n"
        "  </main>\n"
        "</body>\n"
        "</html>\n"
    )
    with open(os.path.join(output_dir, AppConfig.Files.INDEX_HTML), "w", encoding="utf-8") as f:
        f.write(html)


def write_index(generated_items, output_dir):
    """Write the main two-pane map matrix UI with a left-side view mode switch."""
    write_map_manifest(generated_items, output_dir)
    write_viewer(output_dir)

    maps = []
    grouped_items = {}
    mode_labels = []
    title_prefix = f"{AppConfig.CURRENT_MONTH} " if getattr(AppConfig, "CURRENT_MONTH", "") else ""
    for item in generated_items:
        meta = {
            "id": item["map_id"],
            "title": f"{title_prefix}{item['region_name']}{item['map_label']}",
            "regionName": item["region_name"],
            "mapLabel": item["map_label"],
            "countLabel": item.get("count_label", ""),
            "optionPath": os.path.relpath(item["json_path"], output_dir).replace("\\", "/"),
            "htmlPath": os.path.relpath(item["html_path"], output_dir).replace("\\", "/"),
        }
        maps.append(meta)
        grouped_items.setdefault(item["region_name"], []).append(meta)
        if item["map_label"] not in mode_labels:
            mode_labels.append(item["map_label"])

    default_map_id = maps[0]["id"] if maps else ""
    for item in maps:
        if item["regionName"] == "全国" and item["mapLabel"] == AppConfig.MapTypes.TEAM_DEPLOYMENT:
            default_map_id = item["id"]
            break

    default_mode = AppConfig.MapTypes.TEAM_DEPLOYMENT if AppConfig.MapTypes.TEAM_DEPLOYMENT in mode_labels else (mode_labels[0] if mode_labels else "")
    mode_buttons = "".join(
        f'<button class="mode-item" type="button" data-mode="{mode}">{mode.replace("兵力部署-", "")}</button>'
        for mode in mode_labels
    )

    nav_sections = []
    for region_name, items in grouped_items.items():
        buttons = []
        for item in items:
            buttons.append(
                f'<button class="map-item" type="button" data-map-id="{item["id"]}" '
                f'data-region-name="{item["regionName"]}" data-map-label="{item["mapLabel"]}">'
                f'<span>{item["regionName"]}</span>'
                f'<small>{item["countLabel"]}</small>'
                "</button>"
            )
        nav_sections.append(
            '<section class="nav-group">'
            + "".join(buttons)
            + "</section>"
        )

    maps_json = json.dumps(maps, ensure_ascii=False)
    modes_json = json.dumps(mode_labels, ensure_ascii=False)
    nav_html = "".join(nav_sections)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <title>{AppConfig.Site.TITLE}</title>
  <script src="https://assets.pyecharts.org/assets/v6/echarts.min.js"></script>
  <script src="assets/china-cities.js"></script>
  <style>
    *{{box-sizing:border-box;}}
    html,body{{margin:0;width:100vw;height:100vh;overflow:hidden;font-family:Inter,Arial,'Microsoft YaHei',sans-serif;background:#edf1f6;color:#172033;}}
    .app{{display:grid;grid-template-columns:332px minmax(0,1fr);width:100vw;height:100vh;}}
    aside{{background:#fbfcfe;border-right:1px solid #d9e0ea;box-shadow:12px 0 32px rgba(15,23,42,0.06);display:flex;flex-direction:column;min-height:0;z-index:30;}}
    .brand{{padding:20px 18px 16px;border-bottom:1px solid #e4e9f0;background:#ffffff;}}
    .brand h1{{margin:0;color:#111827;font-size:18px;font-weight:800;line-height:1.28;}}
    .brand p{{margin:9px 0 0;color:#6b7280;font-size:12px;line-height:1.45;}}
    .mode-panel{{padding:14px 14px 12px;border-bottom:1px solid #e4e9f0;background:#f6f8fb;}}
    .mode-title{{margin:0 0 9px;padding:0 2px;color:#64748b;font-size:11px;font-weight:800;line-height:1.2;text-transform:uppercase;}}
    .mode-switch{{display:grid;grid-template-columns:repeat(auto-fit,minmax(86px,1fr));gap:8px;padding:3px;border:1px solid #dce3ec;border-radius:8px;background:#ffffff;}}
    .mode-item{{height:34px;border:0;border-radius:6px;background:transparent;color:#475569;font-size:13px;font-weight:800;cursor:pointer;transition:background .16s ease,color .16s ease,box-shadow .16s ease;}}
    .mode-item:hover{{background:#eef4fb;color:#1d4ed8;}}
    .mode-item.active{{background:#135bb8;color:#ffffff;box-shadow:0 5px 14px rgba(19,91,184,0.25);}}
    .nav-scroll{{padding:14px;overflow:auto;min-height:0;}}
    .nav-scroll::-webkit-scrollbar{{width:8px;}}
    .nav-scroll::-webkit-scrollbar-thumb{{background:#c9d3df;border-radius:8px;}}
    .nav-group{{margin-bottom:9px;}}
    .nav-group h2{{margin:0 0 7px;padding:0 4px;color:#334155;font-size:13px;line-height:1.4;}}
    .nav-group.is-empty{{display:none;}}
    .map-item{{width:100%;min-height:54px;margin:0;padding:10px 12px;border:1px solid #dde4ee;border-radius:8px;background:#ffffff;color:#172033;text-align:left;cursor:pointer;box-shadow:0 1px 2px rgba(15,23,42,0.04);transition:border-color .16s ease,background .16s ease,box-shadow .16s ease,transform .16s ease,opacity .16s ease;}}
    .map-item span{{display:block;font-size:14px;font-weight:800;line-height:1.25;}}
    .map-item small{{display:block;margin-top:5px;color:#64748b;font-size:11px;line-height:1.3;}}
    .map-item:hover{{border-color:#aebdd0;background:#fbfdff;box-shadow:0 7px 18px rgba(15,23,42,0.08);transform:translateY(-1px);}}
    .map-item.active{{border-color:#135bb8;background:#eef5ff;box-shadow:inset 4px 0 0 #135bb8,0 7px 18px rgba(19,91,184,0.12);}}
    main{{position:relative;min-width:0;min-height:0;background:#f6f8fb;}}
    main::before{{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(180deg,rgba(255,255,255,0.82),rgba(255,255,255,0) 26%);z-index:1;}}
    #chart{{width:100%;height:100%;position:relative;z-index:0;opacity:1;transform:scale(1);transition:opacity .2s ease,transform .2s ease,filter .2s ease;}}
    main.is-switching #chart{{opacity:.34;transform:scale(.995);filter:saturate(.92);}}
    main.is-ready #chart{{animation:chartIn .24s ease both;}}
    .toolbar{{position:absolute;left:20px;right:20px;top:18px;z-index:20;display:flex;align-items:center;justify-content:space-between;gap:12px;pointer-events:none;}}
    .map-title{{min-width:0;padding:10px 14px;background:rgba(255,255,255,0.92);border:1px solid rgba(211,219,230,0.92);border-radius:8px;box-shadow:0 12px 30px rgba(15,23,42,0.12);backdrop-filter:blur(12px);transition:opacity .18s ease,transform .18s ease;}}
    .map-title strong{{display:block;color:#111827;font-size:16px;font-weight:800;line-height:1.25;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
    .map-title span{{display:block;margin-top:3px;color:#64748b;font-size:12px;}}
    .actions{{display:flex;align-items:center;gap:8px;pointer-events:auto;}}
    .actions label,.actions a{{height:34px;padding:0 12px;border:1px solid rgba(211,219,230,0.96);border-radius:8px;background:rgba(255,255,255,0.92);box-shadow:0 12px 30px rgba(15,23,42,0.10);backdrop-filter:blur(12px);display:inline-flex;align-items:center;gap:7px;color:#172033;font-size:12px;font-weight:700;text-decoration:none;white-space:nowrap;transition:background .16s ease,border-color .16s ease,color .16s ease,transform .16s ease;}}
    .bubble-control{{height:34px;padding:3px;border:1px solid rgba(211,219,230,0.96);border-radius:8px;background:rgba(255,255,255,0.92);box-shadow:0 12px 30px rgba(15,23,42,0.10);backdrop-filter:blur(12px);display:inline-flex;align-items:center;gap:3px;}}
    .bubble-control span{{padding:0 7px;color:#64748b;font-size:12px;font-weight:800;white-space:nowrap;}}
    .bubble-mode{{height:26px;padding:0 8px;border:0;border-radius:6px;background:transparent;color:#475569;font-size:12px;font-weight:800;cursor:pointer;transition:background .16s ease,color .16s ease;}}
    .bubble-mode:hover{{background:#eef4fb;color:#135bb8;}}
    .bubble-mode.active{{background:#135bb8;color:#ffffff;}}
    .actions label:hover,.actions a:hover{{transform:translateY(-1px);}}
    .actions a{{background:#172033;border-color:#172033;color:#fff;}}
    .actions a:hover{{background:#135bb8;border-color:#135bb8;}}
    #status{{position:absolute;left:50%;top:50%;transform:translate(-50%,-48%);z-index:10;padding:10px 14px;border:1px solid #dce3ec;border-radius:8px;background:rgba(255,255,255,0.86);box-shadow:0 10px 24px rgba(15,23,42,0.10);color:#64748b;font-size:14px;opacity:0;pointer-events:none;transition:opacity .16s ease,transform .16s ease;}}
    #status.is-visible{{opacity:1;transform:translate(-50%,-50%);}}
    main.is-switching .map-title{{opacity:.72;transform:translateY(-2px);}}
    @keyframes chartIn{{from{{opacity:.48;transform:scale(.995);}}to{{opacity:1;transform:scale(1);}}}}
    @media (prefers-reduced-motion: reduce){{
      #chart,.map-item,.mode-item,.bubble-mode,.map-title,.actions label,.actions a,#status{{animation:none!important;transition:none!important;}}
    }}
    @media (max-width: 820px){{
      .app{{grid-template-columns:1fr;grid-template-rows:276px minmax(0,1fr);}}
      aside{{border-right:0;border-bottom:1px solid #d8dde3;}}
      .brand{{padding:12px 14px;}}
      .mode-panel{{padding:10px 12px;}}
      .nav-scroll{{display:flex;gap:12px;overflow:auto;padding:10px 12px;}}
      .nav-group{{min-width:190px;margin:0;}}
      .toolbar{{left:10px;right:10px;top:10px;align-items:flex-start;}}
      .actions{{flex-wrap:wrap;justify-content:flex-end;}}
    }}
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <div class="brand">
        <h1>{AppConfig.Site.HEADER}</h1>
        <p>选择视图模式和地图矩阵，右侧地图实时切换</p>
      </div>
      <div class="mode-panel">
        <div class="mode-title">视图模式</div>
        <div class="mode-switch">{mode_buttons}</div>
      </div>
      <div class="nav-scroll">{nav_html}</div>
    </aside>
    <main>
      <div class="toolbar">
        <div class="map-title"><strong id="map-title"></strong><span id="map-subtitle"></span></div>
        <div class="actions">
          <div class="bubble-control" aria-label="气泡模式">
            <span>气泡</span>
            <button class="bubble-mode" type="button" data-bubble-mode="off">关闭</button>
            <button class="bubble-mode" type="button" data-bubble-mode="top">全国Top30</button>
            <button class="bubble-mode" type="button" data-bubble-mode="all">全部</button>
          </div>
          <a id="download-html" href="#" download>下载完整HTML</a>
        </div>
      </div>
      <div id="status"></div>
      <div id="chart"></div>
    </main>
  </div>
  <script>
    const maps = {maps_json};
    const viewModes = {modes_json};
    const defaultMapId = "{default_map_id}";
    const defaultMode = "{default_mode}";
    const provinceBoundaryPath = "{AppConfig.Files.MAP_DATA_DIR}/province_boundaries.json";
    const chart = echarts.init(document.getElementById("chart"), "white", {{renderer: "canvas", locale: "ZH"}});
    let labelDataCache = {{}};
    let activeMapId = null;
    let activeMode = defaultMode;
    let activeRegionName = "全国";
    let activeBubbleMode = "all";

    function withCacheBuster(path) {{
      const joiner = path.indexOf("?") >= 0 ? "&" : "?";
      return path + joiner + "v=" + Date.now();
    }}

    function wait(ms) {{
      return new Promise(resolve => window.setTimeout(resolve, ms));
    }}

    function setLoading(loading) {{
      const main = document.querySelector("main");
      const status = document.getElementById("status");
      main.classList.toggle("is-switching", loading);
      if (loading) {{
        main.classList.remove("is-ready");
        status.classList.remove("is-visible");
        status.textContent = "";
      }} else {{
        status.classList.remove("is-visible");
        status.textContent = "";
        main.classList.add("is-ready");
        window.setTimeout(function() {{ main.classList.remove("is-ready"); }}, 260);
      }}
    }}

    function reviveFunctions(value) {{
      if (Array.isArray(value)) {{
        return value.map(reviveFunctions);
      }}
      if (value && typeof value === "object") {{
        Object.keys(value).forEach(function(key) {{
          value[key] = reviveFunctions(value[key]);
        }});
        return value;
      }}
      if (typeof value === "string" && /^function\\s*\\(/.test(value.trim())) {{
        return Function("return (" + value + ");")();
      }}
      return value;
    }}

    function setBubbleModeButton(mode) {{
      document.querySelectorAll(".bubble-mode").forEach(function(button) {{
        button.classList.toggle("active", button.dataset.bubbleMode === mode);
      }});
    }}

    function applyBubbleMode(mode) {{
      activeBubbleMode = mode;
      const option = chart.getOption();
      const series = option.series || [];
      const updates = [];
      for (let i = 0; i < series.length; i++) {{
        const s = series[i];
        if (s.id === "team-label-layer" || s.id === "salesperson-label-layer") {{
          if (!labelDataCache[s.id] && s.data && s.data.length) {{
            labelDataCache[s.id] = s.data;
          }}
          const source = labelDataCache[s.id] || s.data || [];
          if (mode === "off") {{
            s.data = [];
          }} else if (mode === "top" && s.id === "salesperson-label-layer") {{
            s.data = source.filter(function(item) {{
              const value = item && item.value ? item.value : item;
              return value && Number(value[6] || 0) === 1;
            }});
          }} else {{
            s.data = source;
          }}
          updates.push({{id: s.id, data: s.data}});
        }}
        if (s.id === "team-point-layer") {{
          s.label = s.label || {{}};
          s.label.show = false;
          s.emphasis = s.emphasis || {{}};
          s.emphasis.disabled = false;
          s.emphasis.label = s.emphasis.label || {{}};
          s.emphasis.label.show = true;
          const data = s.data || [];
          for (let j = 0; j < data.length; j++) {{
            data[j].label = data[j].label || {{}};
            data[j].label.show = false;
          }}
          updates.push({{
            id: s.id,
            label: s.label,
            emphasis: s.emphasis,
            data: data
          }});
        }}
      }}
      if (updates.length) {{
        chart.setOption({{series: updates}}, false, true);
      }}
    }}

    function defaultBubbleMode(meta) {{
      return meta && meta.mapLabel === "{AppConfig.MapTypes.SALESPERSON_DEPLOYMENT}" ? "top" : "all";
    }}

    async function appendSharedProvinceBoundary(option) {{
      try {{
        const data = await fetch(withCacheBuster(provinceBoundaryPath)).then(r => r.ok ? r.json() : null);
        if (!data || !Array.isArray(data)) {{
          return option;
        }}
        option.series = option.series || [];
        option.series.push({{
          type: "lines",
          name: "省级边界",
          coordinateSystem: "geo",
          polyline: true,
          data: data,
          silent: true,
          symbol: "none",
          z: 20,
          animation: false,
          lineStyle: {{color: "#d0d4d9", width: 1.4, opacity: 0.75, type: "solid"}},
          tooltip: {{show: false}}
        }});
      }} catch (error) {{
        console.warn("省级边界加载失败", error);
      }}
      return option;
    }}

    function findMap(regionName, mapLabel) {{
      return maps.find(item => item.regionName === regionName && item.mapLabel === mapLabel);
    }}

    function setActiveButton(mapId) {{
      document.querySelectorAll(".map-item").forEach(function(button) {{
        button.classList.toggle("active", button.dataset.mapId === mapId);
      }});
    }}

    function setActiveModeButton(mode) {{
      document.querySelectorAll(".mode-item").forEach(function(button) {{
        button.classList.toggle("active", button.dataset.mode === mode);
      }});
    }}

    function filterMapMatrix(mode) {{
      document.querySelectorAll(".nav-group").forEach(function(group) {{
        let visibleCount = 0;
        group.querySelectorAll(".map-item").forEach(function(button) {{
          const visible = button.dataset.mapLabel === mode;
          button.style.display = visible ? "" : "none";
          if (visible) {{
            visibleCount += 1;
          }}
        }});
        group.classList.toggle("is-empty", visibleCount === 0);
      }});
    }}

    function syncLeftPanel(meta) {{
      activeMode = meta.mapLabel;
      activeRegionName = meta.regionName;
      setActiveModeButton(activeMode);
      filterMapMatrix(activeMode);
      setActiveButton(meta.id);
    }}

    async function loadMap(mapId) {{
      const meta = maps.find(item => item.id === mapId) || maps.find(item => item.id === defaultMapId) || maps[0];
      if (!meta || activeMapId === meta.id) {{
        return;
      }}
      activeMapId = meta.id;
      labelDataCache = {{}};
      syncLeftPanel(meta);
      setLoading(true);
      document.getElementById("map-title").textContent = meta.title;
      document.getElementById("map-subtitle").textContent = meta.countLabel || "";
      const download = document.getElementById("download-html");
      download.href = meta.htmlPath;
      download.download = meta.title + ".html";
      await wait(120);
      const option = await fetch(withCacheBuster(meta.optionPath)).then(r => r.json()).then(reviveFunctions).then(appendSharedProvinceBoundary);
      chart.clear();
      chart.setOption(option, true);
      setLoading(false);
      const bubbleMode = defaultBubbleMode(meta);
      setBubbleModeButton(bubbleMode);
      applyBubbleMode(bubbleMode);
      const url = new URL(window.location.href);
      url.searchParams.set("map", meta.id);
      window.history.replaceState(null, "", url);
    }}

    function showError(error) {{
      const status = document.getElementById("status");
      document.querySelector("main").classList.remove("is-switching");
      status.classList.add("is-visible");
      status.textContent = "地图加载失败：" + error.message;
      console.error(error);
    }}

    document.querySelectorAll(".map-item").forEach(function(button) {{
      button.addEventListener("click", function() {{
        loadMap(this.dataset.mapId).catch(showError);
      }});
    }});
    document.querySelectorAll(".mode-item").forEach(function(button) {{
      button.addEventListener("click", function() {{
        const nextMode = this.dataset.mode;
        const nextMap = findMap(activeRegionName, nextMode) || findMap("全国", nextMode) || maps.find(item => item.mapLabel === nextMode);
        if (nextMap) {{
          loadMap(nextMap.id).catch(showError);
        }}
      }});
    }});
    document.querySelectorAll(".bubble-mode").forEach(function(button) {{
      button.addEventListener("click", function() {{
        const mode = this.dataset.bubbleMode;
        setBubbleModeButton(mode);
        applyBubbleMode(mode);
      }});
    }});
    window.addEventListener("resize", function() {{ chart.resize(); }});

    const params = new URLSearchParams(window.location.search);
    const initialMap = maps.find(item => item.id === params.get("map")) || maps.find(item => item.id === defaultMapId) || maps[0];
    setActiveModeButton(initialMap ? initialMap.mapLabel : defaultMode);
    filterMapMatrix(initialMap ? initialMap.mapLabel : defaultMode);
    loadMap(initialMap ? initialMap.id : defaultMapId).catch(showError);
  </script>
</body>
</html>
"""
    with open(os.path.join(output_dir, AppConfig.Files.INDEX_HTML), "w", encoding="utf-8") as f:
        f.write(html)
    write_map_manifest(generated_items, output_dir)
    write_viewer(output_dir)


def write_map_manifest(generated_items, output_dir):
    """Write the map list consumed by the lightweight viewer."""
    data_dir = os.path.join(output_dir, AppConfig.Files.MAP_DATA_DIR)
    asset_dir = os.path.join(output_dir, "assets")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(asset_dir, exist_ok=True)
    source_city_map = os.path.join(AppConfig.BASE_DIR, "assets", "china-cities.js")
    target_city_map = os.path.join(asset_dir, "china-cities.js")
    if os.path.exists(source_city_map):
        shutil.copyfile(source_city_map, target_city_map)
    source_geojson = os.path.join(AppConfig.BASE_DIR, "china_cities_boundaries.json")
    target_geojson = os.path.join(data_dir, "china_cities_boundaries.json")
    if os.path.exists(source_geojson):
        shutil.copyfile(source_geojson, target_geojson)

    maps = []
    for item in generated_items:
        maps.append({
            "id": item["map_id"],
            "title": f"{item['region_name']}{item['map_label']}",
            "regionName": item["region_name"],
            "mapLabel": item["map_label"],
            "countLabel": item.get("count_label", ""),
            "optionPath": os.path.relpath(item["json_path"], output_dir).replace("\\", "/"),
            "htmlPath": os.path.relpath(item["html_path"], output_dir).replace("\\", "/"),
        })

    with open(os.path.join(data_dir, AppConfig.Files.MAP_MANIFEST), "w", encoding="utf-8") as f:
        json.dump({"maps": maps}, f, ensure_ascii=False, indent=2)


def write_viewer(output_dir):
    """Create the shared lightweight online viewer."""
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <title>{AppConfig.Site.TITLE}</title>
  <script src="https://assets.pyecharts.org/assets/v6/echarts.min.js"></script>
  <script src="assets/china-cities.js"></script>
  <style>
    html,body{{margin:0;padding:0;width:100vw;height:100vh;overflow:hidden;font-family:Arial,'Microsoft YaHei',sans-serif;}}
    #chart{{width:100vw;height:100vh;}}
    .viewer-toolbar{{position:fixed;right:18px;top:18px;z-index:9999;display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:8px 10px;background:rgba(255,255,255,0.94);border:1px solid #d8dde3;border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,0.12);font-size:12px;color:#1f2933;}}
    .viewer-toolbar a{{height:28px;border:0;border-radius:5px;padding:0 10px;background:#0b67c2;color:#fff;text-decoration:none;display:inline-flex;align-items:center;font:12px Arial,'Microsoft YaHei',sans-serif;}}
    .viewer-toolbar a.download{{background:#4b5563;}}
    .viewer-toolbar label{{display:inline-flex;align-items:center;gap:5px;}}
    #status{{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);font:14px Arial,'Microsoft YaHei',sans-serif;color:#4b5563;}}
  </style>
</head>
<body>
  <div class="viewer-toolbar">
    <label><input id="team-label-toggle" type="checkbox" checked>{AppConfig.Site.LABEL_TOGGLE_TEXT}</label>
    <a id="download-html" class="download" href="#" download>下载本地文件</a>
    <a href="{AppConfig.Files.INDEX_HTML}">返回首页</a>
  </div>
  <div id="status">地图加载中...</div>
  <div id="chart"></div>
  <script>
    const manifestPath = "{AppConfig.Files.MAP_DATA_DIR}/{AppConfig.Files.MAP_MANIFEST}";
    const provinceBoundaryPath = "{AppConfig.Files.MAP_DATA_DIR}/province_boundaries.json";
    const chart = echarts.init(document.getElementById("chart"), "white", {{renderer: "canvas", locale: "ZH"}});
    let labelDataCache = {{}};

    function withCacheBuster(path) {{
      const joiner = path.indexOf("?") >= 0 ? "&" : "?";
      return path + joiner + "v=" + Date.now();
    }}

    function reviveFunctions(value) {{
      if (Array.isArray(value)) {{
        return value.map(reviveFunctions);
      }}
      if (value && typeof value === "object") {{
        Object.keys(value).forEach(function(key) {{
          value[key] = reviveFunctions(value[key]);
        }});
        return value;
      }}
      if (typeof value === "string" && /^function\\s*\\(/.test(value.trim())) {{
        return Function("return (" + value + ");")();
      }}
      return value;
    }}

    function applyTeamLabelMode(alwaysShow) {{
      const option = chart.getOption();
      const series = option.series || [];
      for (let i = 0; i < series.length; i++) {{
        const s = series[i];
        if (s.id === "team-label-layer" || s.id === "salesperson-label-layer") {{
          if (!labelDataCache[s.id] && s.data && s.data.length) {{
            labelDataCache[s.id] = s.data;
          }}
          s.data = alwaysShow ? (labelDataCache[s.id] || s.data || []) : [];
        }}
        if (s.id === "team-point-layer") {{
          s.label = s.label || {{}};
          s.label.show = false;
          s.emphasis = s.emphasis || {{}};
          s.emphasis.disabled = false;
          s.emphasis.label = s.emphasis.label || {{}};
          s.emphasis.label.show = true;
          const data = s.data || [];
          for (let j = 0; j < data.length; j++) {{
            data[j].label = data[j].label || {{}};
            data[j].label.show = false;
          }}
        }}
      }}
      chart.setOption({{series}});
    }}

    async function appendSharedProvinceBoundary(option) {{
      try {{
        const data = await fetch(withCacheBuster(provinceBoundaryPath)).then(r => r.ok ? r.json() : null);
        if (!data || !Array.isArray(data)) {{
          return option;
        }}
        option.series = option.series || [];
        option.series.push({{
          type: "lines",
          name: "省级边界",
          coordinateSystem: "geo",
          polyline: true,
          data: data,
          silent: true,
          symbol: "none",
          z: 20,
          animation: false,
          lineStyle: {{
            color: "#d0d4d9",
            width: 1.4,
            opacity: 0.75,
            type: "solid"
          }},
          tooltip: {{show: false}}
        }});
      }} catch (error) {{
        console.warn("省级边界加载失败", error);
      }}
      return option;
    }}

    async function loadMap() {{
      const params = new URLSearchParams(window.location.search);
      const mapId = params.get("map");
      const manifest = await fetch(withCacheBuster(manifestPath)).then(r => r.json());
      const meta = manifest.maps.find(item => item.id === mapId) || manifest.maps[0];
      if (!meta) {{
        throw new Error("未找到地图清单");
      }}
      document.title = meta.title;
      const download = document.getElementById("download-html");
      download.href = meta.htmlPath;
      download.download = meta.title + ".html";

      const option = await fetch(withCacheBuster(meta.optionPath)).then(r => r.json()).then(reviveFunctions).then(appendSharedProvinceBoundary);
      chart.setOption(option, true);
      document.getElementById("status").style.display = "none";
      applyTeamLabelMode(document.getElementById("team-label-toggle").checked);
    }}

    document.getElementById("team-label-toggle").addEventListener("change", function() {{
      applyTeamLabelMode(this.checked);
    }});
    window.addEventListener("resize", function() {{ chart.resize(); }});
    loadMap().catch(function(error) {{
      document.getElementById("status").textContent = "地图加载失败：" + error.message;
      console.error(error);
    }});
  </script>
</body>
</html>
"""
    with open(os.path.join(output_dir, AppConfig.Files.VIEWER_HTML), "w", encoding="utf-8") as f:
        f.write(html)


def write_index_legacy_two_pane_plain(generated_items, output_dir):
    """Write the main two-pane map matrix UI."""
    write_map_manifest(generated_items, output_dir)
    write_viewer(output_dir)

    maps = []
    grouped_items = {}
    for item in generated_items:
        meta = {
            "id": item["map_id"],
            "title": f"{item['region_name']}{item['map_label']}",
            "regionName": item["region_name"],
            "mapLabel": item["map_label"],
            "countLabel": item.get("count_label", ""),
            "optionPath": os.path.relpath(item["json_path"], output_dir).replace("\\", "/"),
            "htmlPath": os.path.relpath(item["html_path"], output_dir).replace("\\", "/"),
        }
        maps.append(meta)
        grouped_items.setdefault(item["region_name"], []).append(meta)

    default_map_id = maps[0]["id"] if maps else ""
    for item in maps:
        if item["regionName"] == "全国" and item["mapLabel"] == AppConfig.MapTypes.TEAM_DEPLOYMENT:
            default_map_id = item["id"]
            break

    nav_sections = []
    for region_name, items in grouped_items.items():
        buttons = []
        for item in items:
            buttons.append(
                f'<button class="map-item" type="button" data-map-id="{item["id"]}">'
                f'<span>{item["mapLabel"]}</span>'
                f'<small>{item["countLabel"]}</small>'
                "</button>"
            )
        nav_sections.append(
            '<section class="nav-group">'
            f"<h2>{region_name}</h2>"
            + "".join(buttons)
            + "</section>"
        )

    maps_json = json.dumps(maps, ensure_ascii=False)
    nav_html = "".join(nav_sections)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{AppConfig.Site.TITLE}</title>
  <script src="https://assets.pyecharts.org/assets/v6/echarts.min.js"></script>
  <script src="assets/china-cities.js"></script>
  <style>
    *{{box-sizing:border-box;}}
    html,body{{margin:0;width:100vw;height:100vh;overflow:hidden;font-family:Arial,'Microsoft YaHei',sans-serif;background:#eef2f7;color:#1f2933;}}
    .app{{display:grid;grid-template-columns:320px minmax(0,1fr);width:100vw;height:100vh;}}
    aside{{background:#ffffff;border-right:1px solid #d8dde3;display:flex;flex-direction:column;min-height:0;}}
    .brand{{padding:18px 18px 14px;border-bottom:1px solid #e5e7eb;}}
    .brand h1{{margin:0;font-size:18px;line-height:1.25;}}
    .brand p{{margin:8px 0 0;color:#64748b;font-size:12px;}}
    .nav-scroll{{padding:12px;overflow:auto;min-height:0;}}
    .nav-group{{margin-bottom:14px;}}
    .nav-group h2{{margin:0 0 7px;padding:0 4px;color:#334155;font-size:13px;line-height:1.4;}}
    .map-item{{width:100%;min-height:46px;margin:0 0 7px;padding:8px 10px;border:1px solid #d7dce3;border-radius:6px;background:#f8fafc;color:#1f2933;text-align:left;cursor:pointer;}}
    .map-item span{{display:block;font-size:13px;font-weight:700;line-height:1.25;}}
    .map-item small{{display:block;margin-top:4px;color:#64748b;font-size:11px;line-height:1.25;}}
    .map-item:hover{{border-color:#94a3b8;background:#ffffff;}}
    .map-item.active{{border-color:#0b67c2;background:#e8f2ff;box-shadow:inset 3px 0 0 #0b67c2;}}
    main{{position:relative;min-width:0;min-height:0;background:#f8f9fa;}}
    #chart{{width:100%;height:100%;}}
    .toolbar{{position:absolute;left:18px;right:18px;top:14px;z-index:20;display:flex;align-items:center;justify-content:space-between;gap:12px;pointer-events:none;}}
    .map-title{{min-width:0;padding:8px 12px;background:rgba(255,255,255,0.94);border:1px solid #d8dde3;border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,0.10);}}
    .map-title strong{{display:block;font-size:15px;line-height:1.25;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
    .map-title span{{display:block;margin-top:2px;color:#64748b;font-size:12px;}}
    .actions{{display:flex;align-items:center;gap:8px;pointer-events:auto;}}
    .actions label,.actions a{{height:30px;padding:0 10px;border:1px solid #d8dde3;border-radius:6px;background:rgba(255,255,255,0.94);box-shadow:0 2px 8px rgba(0,0,0,0.10);display:inline-flex;align-items:center;gap:6px;color:#1f2933;font-size:12px;text-decoration:none;white-space:nowrap;}}
    .actions a{{background:#4b5563;border-color:#4b5563;color:#fff;}}
    #status{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);z-index:10;color:#64748b;font-size:14px;}}
    @media (max-width: 820px){{
      .app{{grid-template-columns:1fr;grid-template-rows:220px minmax(0,1fr);}}
      aside{{border-right:0;border-bottom:1px solid #d8dde3;}}
      .brand{{padding:12px 14px;}}
      .nav-scroll{{display:flex;gap:12px;overflow:auto;padding:10px 12px;}}
      .nav-group{{min-width:190px;margin:0;}}
      .toolbar{{left:10px;right:10px;top:10px;align-items:flex-start;}}
      .actions{{flex-wrap:wrap;justify-content:flex-end;}}
    }}
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <div class="brand">
        <h1>{AppConfig.Site.HEADER}</h1>
        <p>选择左侧矩阵，右侧地图实时切换</p>
      </div>
      <div class="nav-scroll">{nav_html}</div>
    </aside>
    <main>
      <div class="toolbar">
        <div class="map-title"><strong id="map-title">地图加载中</strong><span id="map-subtitle"></span></div>
        <div class="actions">
          <label><input id="team-label-toggle" type="checkbox" checked>{AppConfig.Site.LABEL_TOGGLE_TEXT}</label>
          <a id="download-html" href="#" download>下载完整HTML</a>
        </div>
      </div>
      <div id="status">地图加载中...</div>
      <div id="chart"></div>
    </main>
  </div>
  <script>
    const maps = {maps_json};
    const defaultMapId = "{default_map_id}";
    const provinceBoundaryPath = "{AppConfig.Files.MAP_DATA_DIR}/province_boundaries.json";
    const chart = echarts.init(document.getElementById("chart"), "white", {{renderer: "canvas", locale: "ZH"}});
    let labelDataCache = {{}};
    let activeMapId = null;

    function withCacheBuster(path) {{
      const joiner = path.indexOf("?") >= 0 ? "&" : "?";
      return path + joiner + "v=" + Date.now();
    }}

    function reviveFunctions(value) {{
      if (Array.isArray(value)) {{
        return value.map(reviveFunctions);
      }}
      if (value && typeof value === "object") {{
        Object.keys(value).forEach(function(key) {{
          value[key] = reviveFunctions(value[key]);
        }});
        return value;
      }}
      if (typeof value === "string" && /^function\\s*\\(/.test(value.trim())) {{
        return Function("return (" + value + ");")();
      }}
      return value;
    }}

    function applyTeamLabelMode(alwaysShow) {{
      const option = chart.getOption();
      const series = option.series || [];
      for (let i = 0; i < series.length; i++) {{
        const s = series[i];
        if (s.id === "team-label-layer" || s.id === "salesperson-label-layer") {{
          if (!labelDataCache[s.id] && s.data && s.data.length) {{
            labelDataCache[s.id] = s.data;
          }}
          s.data = alwaysShow ? (labelDataCache[s.id] || s.data || []) : [];
        }}
        if (s.id === "team-point-layer") {{
          s.label = s.label || {{}};
          s.label.show = false;
          s.emphasis = s.emphasis || {{}};
          s.emphasis.disabled = false;
          s.emphasis.label = s.emphasis.label || {{}};
          s.emphasis.label.show = true;
          const data = s.data || [];
          for (let j = 0; j < data.length; j++) {{
            data[j].label = data[j].label || {{}};
            data[j].label.show = false;
          }}
        }}
      }}
      chart.setOption({{series}});
    }}

    async function appendSharedProvinceBoundary(option) {{
      try {{
        const data = await fetch(withCacheBuster(provinceBoundaryPath)).then(r => r.ok ? r.json() : null);
        if (!data || !Array.isArray(data)) {{
          return option;
        }}
        option.series = option.series || [];
        option.series.push({{
          type: "lines",
          name: "省级边界",
          coordinateSystem: "geo",
          polyline: true,
          data: data,
          silent: true,
          symbol: "none",
          z: 20,
          animation: false,
          lineStyle: {{color: "#d0d4d9", width: 1.4, opacity: 0.75, type: "solid"}},
          tooltip: {{show: false}}
        }});
      }} catch (error) {{
        console.warn("省级边界加载失败", error);
      }}
      return option;
    }}

    function setActiveButton(mapId) {{
      document.querySelectorAll(".map-item").forEach(function(button) {{
        button.classList.toggle("active", button.dataset.mapId === mapId);
      }});
    }}

    async function loadMap(mapId) {{
      const meta = maps.find(item => item.id === mapId) || maps.find(item => item.id === defaultMapId) || maps[0];
      if (!meta || activeMapId === meta.id) {{
        return;
      }}
      activeMapId = meta.id;
      labelDataCache = {{}};
      setActiveButton(meta.id);
      document.getElementById("status").style.display = "block";
      document.getElementById("map-title").textContent = meta.title;
      document.getElementById("map-subtitle").textContent = meta.countLabel || "";
      const download = document.getElementById("download-html");
      download.href = meta.htmlPath;
      download.download = meta.title + ".html";
      const option = await fetch(withCacheBuster(meta.optionPath)).then(r => r.json()).then(reviveFunctions).then(appendSharedProvinceBoundary);
      chart.clear();
      chart.setOption(option, true);
      document.getElementById("status").style.display = "none";
      applyTeamLabelMode(document.getElementById("team-label-toggle").checked);
      const url = new URL(window.location.href);
      url.searchParams.set("map", meta.id);
      window.history.replaceState(null, "", url);
    }}

    function showError(error) {{
      document.getElementById("status").style.display = "block";
      document.getElementById("status").textContent = "地图加载失败：" + error.message;
      console.error(error);
    }}

    document.querySelectorAll(".map-item").forEach(function(button) {{
      button.addEventListener("click", function() {{
        loadMap(this.dataset.mapId).catch(showError);
      }});
    }});
    document.getElementById("team-label-toggle").addEventListener("change", function() {{
      applyTeamLabelMode(this.checked);
    }});
    window.addEventListener("resize", function() {{ chart.resize(); }});

    const params = new URLSearchParams(window.location.search);
    loadMap(params.get("map") || defaultMapId).catch(showError);
  </script>
</body>
</html>
"""
    with open(os.path.join(output_dir, AppConfig.Files.INDEX_HTML), "w", encoding="utf-8") as f:
        f.write(html)
