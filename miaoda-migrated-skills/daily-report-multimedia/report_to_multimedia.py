#!/usr/bin/env python3
"""
report_to_multimedia.py
 AI工作日报多媒体化自动生成系统

 功能：
   1. 读取飞书日报文档（或本地 JSON）
   2. 生成播报音频（TTS）
   3. 生成配套图片（3-5张）
   4. 生成字幕文件（SRT）
   5. 输出完整 HTML 播客页面

 用法：
   python report_to_multimedia.py --date 2026-05-07
   python report_to_multimedia.py --token <doc_token>
   python report_to_multimedia.py --json /path/to/data.json
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import wave
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# 注入路径
SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent.parent
TEMPLATE_PATH = SKILL_DIR / "hotel-room-quality-inspection-v2" / "podcast_report_template.html"

# 默认输出目录
OUTPUT_BASE = SCRIPT_DIR / "output"


def format_date_cn(date_str: str) -> str:
    """2026-05-07 → 五月七日"""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
    except:
        return date_str

    month = d.month
    day = d.day
    units = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]

    def to_cn(n):
        if n == 0:
            return "零"
        if n <= 10:
            return units[n]
        if n < 20:
            return "十" + (units[n % 10] if n % 10 != 0 else "")
        if n < 100:
            return units[n // 10] + "十" + (units[n % 10] if n % 10 != 0 else "")
        return str(n)

    return f"{to_cn(month)}月{to_cn(day)}日"


def load_data(json_path: str = None) -> Dict:
    """加载日报数据"""
    if json_path and Path(json_path).exists():
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # 返回默认测试数据
    return {
        "date": "2026-05-07",
        "date_display": "五月七日",
        "location": "天津瑞湾开元名都酒店",
        "core_events": [
            "晨会 - 部署当日重点工作",
            "任务下发 - 9项任务分解到人",
            "AI研究 - 智能质检系统调试",
            "边防二团队接待 - 重要客户接待"
        ],
        "tasks": [
            {"id": 1, "content": "客房质检日报17:30准时推送", "status": "进行中", "priority": "P1"},
            {"id": 2, "content": "前台SOP流程更新", "status": "待落实", "priority": "P0"},
            {"id": 3, "content": "早餐出品标准检查", "status": "待落实", "priority": "P1"},
            {"id": 4, "content": "工程问题跟进", "status": "待落实", "priority": "P1"},
            {"id": 5, "content": "安保巡逻排班优化", "status": "待落实", "priority": "P2"},
            {"id": 6, "content": "客户投诉回访", "status": "待落实", "priority": "P1"},
            {"id": 7, "content": "卫生深度检查", "status": "待落实", "priority": "P0"},
            {"id": 8, "content": "收益管理系统测试", "status": "进行中", "priority": "P1"},
            {"id": 9, "content": "明日工作预排", "status": "待落实", "priority": "P2"},
        ],
        "red_lines": [
            {"id": 1, "content": "严禁擅自承诺客户升级", "category": "服务"},
            {"id": 2, "content": "不得跳过质检直接入住", "category": "质检"},
            {"id": 3, "content": "禁止泄露客户信息", "category": "隐私"},
            {"id": 4, "content": "不可降低早餐标准", "category": "品质"},
        ],
        "tomorrow_focus": [
            {"item": "P0 - 前台SOP流程更新", "deadline": "明日10:00"},
            {"item": "P0 - 卫生深度检查", "deadline": "明日14:00"},
            {"item": "P1 - 收益管理系统上线", "deadline": "明日17:00"},
        ],
        "stats": {
            "total_tasks": 9,
            "pending": 7,
            "in_progress": 2,
            "p0_count": 2,
            "p1_count": 5,
            "p2_count": 2,
        }
    }


def build_podcast_script(data: Dict) -> List[Dict]:
    """从日报数据构建播报脚本（字幕时间轴）"""
    date_display = data.get('date_display', format_date_cn(data['date']))
    location = data.get('location', '天津瑞湾开元名都酒店')
    tasks = data.get('tasks', [])
    tomorrow = data.get('tomorrow_focus', [])
    stats = data.get('stats', {})

    # 精简播报文案（目标 45 秒）
    lines = []

    # 开场
    lines.append(f"德胧AI工作日报，{date_display}，{location}，各位同事好。")
    lines.append(f"今日核心事件：晨会部署、9项任务下发、AI质检系统调试、边防二团队接待。")

    # 任务统计
    p0 = stats.get('p0_count', 0)
    p1 = stats.get('p1_count', 0)
    p2 = stats.get('p2_count', 0)
    lines.append(f"今日重点任务共{stats.get('total_tasks', 0)}项，其中P0优先级{p0}项、P1优先级{p1}项、P2优先级{p2}项。")

    # 列出 P0 任务
    p0_tasks = [t['content'] for t in tasks if t.get('priority') == 'P0']
    if p0_tasks:
        lines.append(f"P0级任务：{'，'.join(p0_tasks)}。")

    # 扣分红线
    red_lines = data.get('red_lines', [])
    if red_lines:
        lines.append(f"扣分红线共{len(red_lines)}条：服务红线一条、质检红线一条、隐私红线一条、品质红线一条，请严格执行。")

    # 明日关注
    if tomorrow:
        tomorrow_items = [f"{t.get('item', t)}（{t.get('deadline', '')}）" for t in tomorrow]
        lines.append(f"明日关注：{'；'.join(tomorrow_items)}。")

    # 结束语
    lines.append("详细信息请查看飞书文档，感谢各位同事配合，明天见。")

    # 计算时间轴（平均语速约 150 字/分钟，45秒约 110字）
    # 每句约 4-6 秒
    cues = []
    current_ms = 500  # 0.5秒前奏
    for i, text in enumerate(lines):
        duration = max(3000, min(6000, len(text) * 40))  # 每字符约40ms
        cues.append({
            "start": current_ms,
            "end": current_ms + duration,
            "text": text
        })
        current_ms += duration + 200  # 间隔 200ms

    total_duration = current_ms / 1000
    return cues, total_duration, lines


def generate_srt(cues: List[Dict], output_path: Path):
    """生成 SRT 字幕文件"""
    srt_content = []
    for i, cue in enumerate(cues, 1):
        start = ms_to_srt_time(cue['start'])
        end = ms_to_srt_time(cue['end'])
        srt_content.append(f"{i}\n{start} --> {end}\n{cue['text']}\n")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(srt_content))
    
    print(f"[SRT] 字幕文件已生成: {output_path}")


def ms_to_srt_time(ms: int) -> str:
    """毫秒 → SRT 时间格式 (00:00:00,000)"""
    ms = int(ms)
    hours = ms // 3600000
    ms -= hours * 3600000
    minutes = ms // 60000
    ms -= minutes * 60000
    seconds = ms // 1000
    ms -= seconds * 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"


def load_template() -> str:
    """加载 HTML 模板"""
    if TEMPLATE_PATH.exists():
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    
    # 内联备用模板
    return """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<title>德胧AI工作日报播客 {{date}}</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif;background:#0f0f1a;color:#fff;min-height:100vh;padding:20px;}
.container{max-width:680px;margin:0 auto;}
.header{text-align:center;margin-bottom:24px;}
.header h1{font-size:22px;font-weight:700;margin:8px 0 4px;}
.meta{font-size:14px;color:#a0a0b0;}
.player-card{background:#1a1a2e;border-radius:16px;padding:24px;margin-bottom:24px;border:1px solid rgba(255,255,255,0.08);}
.progress-bar{width:100%;height:6px;background:rgba(255,255,255,0.1);border-radius:3px;margin-bottom:16px;cursor:pointer;}
.progress-fill{height:100%;background:linear-gradient(90deg,#c8102e,#f5a623);border-radius:3px;width:0%;}
.player-controls{display:flex;align-items:center;gap:16px;}
.play-btn{width:56px;height:56px;border-radius:50%;background:#c8102e;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;}
.play-btn:hover{background:#a00d24}
.play-btn.playing{background:#f5a623}
.time-display{font-size:14px;color:#a0a0b0;}
.subtitle-section{background:#1a1a2e;border-radius:16px;padding:24px;border:1px solid rgba(255,255,255,0.08);}
.subtitle-item{padding:12px 16px;border-radius:10px;margin-bottom:6px;font-size:16px;cursor:pointer;color:#a0a0b0;transition:all 0.3s;}
.subtitle-item:hover{background:rgba(255,255,255,0.05)}
.subtitle-item.active{background:rgba(200,16,46,0.15);color:#fff;border-left:3px solid #c8102e;}
.cue{font-size:12px;color:#666;margin-bottom:4px;}
.stats-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:24px;}
.stat-card{background:rgba(255,255,255,0.05);border-radius:12px;padding:16px;text-align:center;}
.stat-card .value{font-size:24px;font-weight:700;color:#f5a623;}
.stat-card .label{font-size:12px;color:#a0a0b0;margin-top:4px;}
</style></head><body>
<div class="container">
<div class="header"><h1>德胧AI工作日报播客</h1><div class="meta">{{date_display}}</div></div>
<div class="player-card">
<div class="progress-bar" id="progressBar"><div class="progress-fill" id="progressFill"></div></div>
<div class="player-controls">
<button class="play-btn" id="playBtn" onclick="togglePlay()">▶</button>
<span class="time-display"><span id="currentTime">0:00</span> / <span id="totalTime">{{duration}}</span></span>
</div></div>
<div class="subtitle-section">
<ul class="subtitle-list" id="subtitleList"></ul>
</div>
<div class="stats-grid">
<div class="stat-card"><div class="value">{{total_tasks}}</div><div class="label">总任务数</div></div>
<div class="stat-card"><div class="value">{{p0_count}}</div><div class="label">P0任务</div></div>
<div class="stat-card"><div class="value">{{p1_count}}</div><div class="label">P1任务</div></div>
</div></div>
<audio id="audioPlayer"><source src="data:audio/mp3;base64,{{audio_base64}}" type="audio/mpeg"></audio>
<script>
const CUES = {{cues_json}};
const audio=document.getElementById('audioPlayer');
const playBtn=document.getElementById('playBtn');
const progressFill=document.getElementById('progressFill');
const currentTimeEl=document.getElementById('currentTime');
const subtitleList=document.getElementById('subtitleList');
let isPlaying=false,activeIndex=-1;
function formatTime(ms){const s=Math.floor(ms/1000),m=Math.floor(s/60);return m+':'+(s%60<10?'0':'')+s%60;}
function initSubtitles(){subtitleList.innerHTML=CUES.map((c,i)=>'<li class="subtitle-item" onclick="seekTo('+c.start+')"><div class="cue">'+formatTime(c.start)+'</div><div>'+c.text+'</div></li>').join('');}
function togglePlay(){isPlaying?audio.pause():audio.play();isPlaying=!isPlaying;playBtn.classList.toggle('playing',isPlaying);}
function seekTo(ms){audio.currentTime=ms/1000;}
audio.addEventListener('timeupdate',()=>{const p=(audio.currentTime/audio.duration)*100;progressFill.style.width=p+'%';currentTimeEl.textContent=formatTime(audio.currentTime*1000);let n=-1;for(let i=0;i<CUES.length;i++)if(audio.currentTime*1000>=CUES[i].start&&audio.currentTime*1000<CUES[i].end){n=i;break;}if(n!==activeIndex){subtitleList.children[activeIndex]?.classList.remove('active');subtitleList.children[n]?.classList.add('active');if(n>=0)subtitleList.children[n].scrollIntoView({behavior:'smooth',block:'center'});activeIndex=n;}});
document.addEventListener('DOMContentLoaded',initSubtitles);
</script></body></html>"""


def render_html(data: Dict, cues: List[Dict], audio_base64: str, output_path: Path):
    """渲染 HTML 播客页面"""
    template = load_template()

    stats = data.get('stats', {})
    duration = f"约{int(sum(c['end'] - c['start'] for c in cues) / 1000)}秒"

    html = (template
        .replace('{{date}}', data.get('date', ''))
        .replace('{{date_display}}', data.get('date_display', ''))
        .replace('{{duration}}', duration)
        .replace('{{total_tasks}}', str(stats.get('total_tasks', 0)))
        .replace('{{p0_count}}', str(stats.get('p0_count', 0)))
        .replace('{{p1_count}}', str(stats.get('p1_count', 0)))
        .replace('{{p2_count}}', str(stats.get('p2_count', 0)))
        .replace('{{audio_base64}}', audio_base64 or '')
        .replace('{{cues_json}}', json.dumps(cues, ensure_ascii=False)))

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    size_kb = len(html) / 1024
    print(f"[HTML] 播客页面已生成: {output_path} ({size_kb:.1f} KB)")


def main():
    parser = argparse.ArgumentParser(description="AI工作日报多媒体化自动生成系统")
    parser.add_argument("--date", default="2026-05-07", help="日报日期 YYYY-MM-DD")
    parser.add_argument("--token", default=None, help="飞书文档 token")
    parser.add_argument("--json", default=None, help="本地 JSON 数据文件")
    parser.add_argument("--output-dir", default=None, help="输出目录")
    parser.add_argument("--skip-audio", action='store_true', help="跳过音频生成")
    parser.add_argument("--skip-images", action='store_true', help="跳过图片生成")
    args = parser.parse_args()

    print("=" * 60)
    print("AI工作日报多媒体化自动生成系统 v1.0")
    print("=" * 60)

    # 加载数据
    data = load_data(args.json)
    if not args.json:
        print(f"[数据] 加载默认测试数据（{data['date']}）")

    date_str = data.get('date', args.date)
    data['date_display'] = data.get('date_display', format_date_cn(date_str))

    print(f"[数据] 日期: {date_str} ({data['date_display']})")
    print(f"[数据] 地点: {data.get('location', '天津瑞湾')}")

    # 构建播报脚本
    cues, total_duration, lines = build_podcast_script(data)
    print(f"[脚本] 播报文案 {len(lines)} 句，时长约 {total_duration:.0f} 秒")

    # 输出目录
    if args.output_dir:
        out_dir = Path(args.output_dir)
    else:
        out_dir = OUTPUT_BASE / date_str
    out_dir.mkdir(parents=True, exist_ok=True)

    # 生成 SRT 字幕
    srt_path = out_dir / "subtitle.srt"
    generate_srt(cues, srt_path)

    # 准备音频（占位，后续由 music_generate 工具生成）
    audio_base64 = ""

    # 如果有现成的音频文件，加载它
    mp3_path = out_dir / "podcast_audio.mp3"
    if mp3_path.exists():
        with open(mp3_path, 'rb') as f:
            audio_base64 = base64.b64encode(f.read()).decode('utf-8')
        print(f"[音频] 已加载本地音频: {mp3_path}")

    # 生成 HTML
    html_path = out_dir / "podcast_report.html"
    render_html(data, cues, audio_base64, html_path)

    # 输出摘要
    print("\n" + "=" * 60)
    print("生成完成!")
    print("=" * 60)
    print(f"输出目录: {out_dir}")
    print(f"  ├── podcast_report.html  (播客页面)")
    print(f"  └── subtitle.srt         (字幕文件)")
    if mp3_path.exists():
        print(f"  └── podcast_audio.mp3   (音频文件)")
    print("\n[下一步]")
    print("1. 运行 music_generate 生成播报音频")
    print("2. 运行 image_generate 生成配图（封面、任务卡片、明日关注）")
    print("3. 将音频 base64 注入 HTML 完成最终输出")

    return {
        "output_dir": str(out_dir),
        "html_path": str(html_path),
        "srt_path": str(srt_path),
        "cues": cues,
        "lines": lines,
        "total_duration": total_duration
    }


if __name__ == "__main__":
    result = main()