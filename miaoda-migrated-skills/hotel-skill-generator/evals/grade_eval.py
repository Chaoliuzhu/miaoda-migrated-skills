#!/usr/bin/env python3
"""Grading script for hotel-skill-generator evals — 主agent手动grading版"""
import json, sys, re, os

def extract_frontmatter(content):
    m = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not m: return {}
    lines = m.group(1).split('\n')
    fm = {}
    current_key = None
    for line in lines:
        if ':' in line and not line.startswith(' '):
            key, val = line.split(':', 1)
            current_key = key.strip()
            fm[current_key] = val.strip().strip('"').strip("'")
        elif line.startswith('  - ') and current_key:
            val = line.strip()[3:]
            if isinstance(fm[current_key], list):
                fm[current_key].append(val)
            else:
                fm[current_key] = [fm[current_key], val]
    return fm

def check_hyphen_case(s):
    return bool(re.match(r'^[a-z0-9-]+$', s))

def run():
    base = '/home/gem/workspace/agent/workspace/skills/hotel-skill-generator/eval_runs/run-001/outputs'
    grades = {}

    # ── EVAL 1 ──
    content1 = open(f'{base}/shanghai-jinmao-junyue/SKILL.md').read()
    fm1 = extract_frontmatter(content1)
    grades[1] = {
        'name hyphencase': check_hyphen_case(fm1.get('name','')),
        'name exists': bool(fm1.get('name')),
        'desc len OK': 50 <= len(fm1.get('description','')) <= 500,
        'has 基础信息': '基础信息' in content1 or '🏨' in content1,
        'has 预订': '预订' in content1 and ('https://' in content1 or 'http://' in content1),
        'not delonix→官网': 'bidawu' not in fm1.get('booking_url',''),
        'no < in desc': '<' not in fm1.get('description',''),
    }

    # ── EVAL 2 ──
    content2 = open(f'{base}/beijing-wangfujia-peninsula/SKILL.md').read()
    fm2 = extract_frontmatter(content2)
    grades[2] = {
        'is_delonix false': str(fm2.get('is_delonix','')).lower() == 'false',
        'not bidawu': 'bidawu' not in fm2.get('booking_url',''),
        'has official site': 'peninsula.com' in content2 or 'https://' in content2,
    }

    # ── EVAL 3 ──
    files3 = ['guangzhou-whiteswan-hotel/SKILL.md', 'shenzhen-intercontinental/SKILL.md', 'chengdu-diaoyutai/SKILL.md']
    grades[3] = {'3 dirs exist': all(os.path.exists(f'{base}/{f}') for f in files3)}
    for f in files3:
        c = open(f'{base}/{f}').read()
        grades[3][f'desc not empty'] = len(c) > 200
        grades[3][f'has content'] = 'SKILL' in c or '🏨' in c

    # ── EVAL 4 ──
    content4 = open(f'{base}/check-existing/SKILL.md').read()
    fm4 = extract_frontmatter(content4)
    grades[4] = {
        'name hyphencase': check_hyphen_case(fm4.get('name','')),
        'desc len OK': 50 <= len(fm4.get('description','')) <= 500,
        'no < in desc': '<' not in fm4.get('description',''),
        'has publish info': 'GitHub' in content4 or 'ClawHub' in content4 or 'Coze' in content4,
        'has dual hotel适配': '德胧' in content4 and ('非德胧' in content4 or '非德胧' in content4),
    }

    # 输出
    for eval_id, checks in grades.items():
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        print(f'\n═══ EVAL {eval_id} ═══')
        for k, v in checks.items():
            print(f'  {"✅" if v else "❌"} {k}')
        print(f'  📊 {passed}/{total} PASSED')

if __name__ == '__main__':
    run()