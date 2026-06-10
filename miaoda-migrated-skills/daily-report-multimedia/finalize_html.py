#!/usr/bin/env python3
"""
finalize_html.py
 将音频和图片注入 HTML，生成最终播客页面

 用法：
   python finalize_html.py --date 2026-05-07
"""

import argparse
import base64
import json
import os
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
TEMPLATE_PATH = SCRIPT_DIR / "daily_report_podcast_template.html"
OUTPUT_BASE = SCRIPT_DIR / "output"


def format_date_cn(date_str: str) -> str:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
    except:
        return date_str
    month = d.month
    day = d.day
    units = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    def to_cn(n):
        if n == 0: return "零"
        if n <= 10: return units[n]
        if n < 20: return "十" + (units[n % 10] if n % 10 != 0 else "")
        if n < 100: return units[n // 10] + "十" + (units[n % 10] if n % 10 != 0 else "")
        return str(n)
    return f"{to_cn(month)}月{to_cn(day)}日"


def image_to_base64(img_path: str) -> str:
    if not os.path.exists(img_path):
        return ""
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def audio_to_base64(audio_path: str) -> str:
    if not os.path.exists(audio_path):
        return ""
    with open(audio_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_mime_type(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
    }
    return mime_types.get(ext, "application/octet-stream")


def load_data():
    return {
        "date": "2026-05-07",
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
            {"content": "严禁擅自承诺客户升级"},
            {"content": "不得跳过质检直接入住"},
            {"content": "禁止泄露客户信息"},
            {"content": "不可降低早餐标准"},
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


def build_cues():
    return [
        {"start": 0, "end": 2500, "text": "德胧AI工作日报，五月七日，天津瑞湾开元名都酒店，各位同事好。"},
        {"start": 2500, "end": 5500, "text": "今日核心事件：晨会部署、9项任务下发、AI质检系统调试、边防二团队接待。"},
        {"start": 5500, "end": 9000, "text": "今日重点任务共9项，其中P0优先级2项、P1优先级5项、P2优先级2项。"},
        {"start": 9000, "end": 13000, "text": "P0级任务：前台SOP流程更新，卫生深度检查。"},
        {"start": 13000, "end": 18000, "text": "扣分红线共4条：服务红线一条、质检红线一条、隐私红线一条、品质红线一条，请严格执行。"},
        {"start": 18000, "end": 25000, "text": "明日关注：P0前台SOP流程更新明日10:00；P0卫生深度检查明日14:00；P1收益管理系统上线明日17:00。"},
        {"start": 25000, "end": 32000, "text": "详细信息请查看飞书文档，感谢各位同事配合，明天见。"},
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default="2026-05-07")
    args = parser.parse_args()

    date_str = args.date
    data = load_data()
    data['date_display'] = format_date_cn(date_str)

    out_dir = OUTPUT_BASE / date_str
    out_dir.mkdir(parents=True, exist_ok=True)

    # 加载模板
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    # 音频
    audio_path = out_dir / "podcast_audio.mp3"
    audio_base64 = audio_to_base64(str(audio_path))

    # 图片
    cover_img = out_dir / "cover.png"
    tasks_img = out_dir / "tasks.png"
    tomorrow_img = out_dir / "tomorrow.png"

    # 使用已生成的图片路径
    cover_b64 = image_to_base64(str(cover_img)) if cover_img.exists() else ""
    tasks_b64 = image_to_base64(str(tasks_img)) if tasks_img.exists() else ""
    tomorrow_b64 = image_to_base64(str(tomorrow_img)) if tomorrow_img.exists() else ""

    # 替换图片路径为 base64
    cover_src = f"data:image/png;base64,{cover_b64}" if cover_b64 else ""
    tasks_src = f"data:image/png;base64,{tasks_b64}" if tasks_b64 else ""
    tomorrow_src = f"data:image/png;base64,{tomorrow_b64}" if tomorrow_b64 else ""

    # 如果没有本地图片，使用生成的图片
    default_cover = "/home/gem/workspace/agent/media/tool-image-generation/generated---d1894aa4-43b9-4767-be27-7ac42385b6a8.png"
    default_tasks = "/home/gem/workspace/agent/media/tool-image-generation/generated---5ff4408a-d7ba-4aea-869f-aba71097553e.png"
    default_tomorrow = "/home/gem/workspace/agent/media/tool-image-generation/generated---94b17c5f-a085-4c92-9b5f-7db8c3222bce.png"

    if not cover_b64 and os.path.exists(default_cover):
        with open(default_cover, "rb") as f:
            cover_src = f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
    if not tasks_b64 and os.path.exists(default_tasks):
        with open(default_tasks, "rb") as f:
            tasks_src = f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
    if not tomorrow_b64 and os.path.exists(default_tomorrow):
        with open(default_tomorrow, "rb") as f:
            tomorrow_src = f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"

    cues = build_cues()
    stats = data['stats']
    duration = f"约{int(sum(c['end'] - c['start'] for c in cues) / 1000)}秒"

    # 渲染
    html = (template
        .replace('{{date}}', date_str)
        .replace('{{date_display}}', data['date_display'])
        .replace('{{location}}', data['location'])
        .replace('{{duration}}', duration)
        .replace('{{cover_image}}', cover_src)
        .replace('{{tasks_image}}', tasks_src)
        .replace('{{tomorrow_image}}', tomorrow_src)
        .replace('{{audio_base64}}', audio_base64)
        .replace('{{cues_json}}', json.dumps(cues, ensure_ascii=False))
        .replace('{{tasks_json}}', json.dumps(data['tasks'], ensure_ascii=False))
        .replace('{{redlines_json}}', json.dumps(data['red_lines'], ensure_ascii=False))
        .replace('{{tomorrow_json}}', json.dumps(data['tomorrow_focus'], ensure_ascii=False))
        .replace('{{total_tasks}}', str(stats['total_tasks']))
        .replace('{{p0_count}}', str(stats['p0_count']))
        .replace('{{p1_count}}', str(stats['p1_count']))
        .replace('{{p2_count}}', str(stats['p2_count']))
    )

    html_path = out_dir / "podcast_report_final.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = len(html) / 1024
    print(f"[完成] 最终播客页面: {html_path}")
    print(f"文件大小: {size_kb:.1f} KB")

    # 同时复制到 static 目录
    static_dir = SCRIPT_DIR.parent.parent / "daily-report-multimedia" / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    static_path = static_dir / f"podcast_{date_str}.html"
    with open(static_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[静态] 备份: {static_path}")

    return str(html_path)


if __name__ == "__main__":
    path = main()
    print(f"\n输出: {path}")