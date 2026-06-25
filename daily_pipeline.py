#!/usr/bin/env python3
"""
花轮股票池 · 每日自动流水线
触发时间: 交易日 15:05
步骤: TDX数据刷新 → 初筛 → 二轮 → 生成报告 → 发送飞书/微信
"""

import subprocess, sys, os, time
from datetime import datetime

PYTHON = r"C:/Users/Clarence/AppData/Local/Programs/Python/Python313/python.exe"
BASE = r"D:/Trading Workflow/Stock_lab_system"
SCRIPTS = f"{BASE}/scripts"
TDX_DIR = r"D:\Trade\new_tdx64"

def run(step_name, script, *args):
    """Run a Python script, print progress, fail fast."""
    print(f"\n{'='*60}")
    print(f"  [{step_name}] {os.path.basename(script)}")
    print(f"{'='*60}")
    cmd = [PYTHON, script] + list(args)
    result = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True, encoding='gbk', errors='replace')
    if result.stdout:
        # Print last 10 lines
        lines = result.stdout.strip().split('\n')
        for line in lines[-10:]:
            print(f"  {line}")
    if result.returncode != 0:
        print(f"  ERROR (exit {result.returncode})")
        if result.stderr:
            print(f"  STDERR: {result.stderr[-500:]}")
        return False
    print(f"  ✅ DONE")
    return True

def main():
    now = datetime.now()
    print(f"Pipeline start: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: TDX refresh (incremental)
    if not run("Step 1/5", f"{SCRIPTS}/tdx_refresh.py"):
        return 1

    # Step 2: First pass screen
    if not run("Step 2/5", f"{SCRIPTS}/first_pass_screen.py"):
        return 1

    # Step 3: Second pass screen + JRX
    if not run("Step 3/5", f"{SCRIPTS}/second_pass_screen.py", "--delay", "0.2"):
        return 1

    # Step 4: Generate 8-section report
    if not run("Step 4/5", f"{TDX_DIR}/gen_8section_report.py"):
        return 1

    # Step 5: Send to Feishu + WeChat
    if not run("Step 5/5", f"{SCRIPTS}/send_report.py"):
        return 1

    elapsed = (datetime.now() - now).total_seconds()
    print(f"\nPipeline complete: {elapsed/60:.1f} min")
    return 0

if __name__ == "__main__":
    sys.exit(main())
