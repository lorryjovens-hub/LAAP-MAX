"""
LAAP AGI — Comprehensive Test Runner

运行所有测试套件并生成详细报告：
- ConsciousnessHarness 完整集成测试
- UnifiedMemory 与 ConsciousnessHarness 集成测试
- 情感动力学引擎测试
- 元认知监控器测试
- 测试覆盖率统计
"""

import os
import sys
import time
import json
import subprocess
import traceback
from datetime import datetime
from pathlib import Path

TEST_FILES = [
    "test_conscience_harness_full.py",
    "test_memory_integration.py",
    "test_affective_dynamics.py",
    "test_meta_cognitive_full.py",
]

TEST_DIR = Path(__file__).parent
REPORTS_DIR = TEST_DIR / "reports"


def run_test(test_file: str) -> dict:
    """运行单个测试文件"""
    test_path = TEST_DIR / test_file
    if not test_path.exists():
        return {
            "test_file": test_file,
            "status": "not_found",
            "error": f"测试文件不存在: {test_path}",
            "duration": 0,
            "passed": 0,
            "failed": 0,
            "total": 0,
        }

    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_path), "-v", "--tb=short", "--no-cov", "-p", "no:quadrants"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        
        duration = round(time.time() - start_time, 2)
        
        passed = 0
        failed = 0
        total = 0
        
        for line in result.stdout.split("\n"):
            if " passed, " in line:
                parts = line.strip().split()
                for part in parts:
                    if part.isdigit():
                        passed = int(part)
                        break
            if " failed, " in line:
                parts = line.strip().split()
                for i, part in enumerate(parts):
                    if part == "failed," and i > 0 and parts[i-1].isdigit():
                        failed = int(parts[i-1])
                    elif part.isdigit() and i+1 < len(parts) and parts[i+1] == "failed":
                        failed = int(part)
            if "test_" in line and "::" in line and ("PASSED" in line or "FAILED" in line):
                total += 1
        
        if result.returncode == 0:
            status = "passed"
        else:
            status = "failed"
        
        return {
            "test_file": test_file,
            "status": status,
            "duration": duration,
            "passed": passed,
            "failed": failed,
            "total": max(passed + failed, total),
            "stdout": result.stdout[:2000],
            "stderr": result.stderr[:1000],
        }
    
    except subprocess.TimeoutExpired:
        return {
            "test_file": test_file,
            "status": "timeout",
            "error": "测试超时",
            "duration": round(time.time() - start_time, 2),
            "passed": 0,
            "failed": 0,
            "total": 0,
        }
    except Exception as e:
        return {
            "test_file": test_file,
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "duration": round(time.time() - start_time, 2),
            "passed": 0,
            "failed": 0,
            "total": 0,
        }


def generate_report(results: list) -> str:
    """生成测试报告"""
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    
    total_passed = sum(r["passed"] for r in results)
    total_failed = sum(r["failed"] for r in results)
    total_tests = sum(r["total"] for r in results)
    total_duration = sum(r["duration"] for r in results)
    
    pass_rate = round(total_passed / max(total_tests, 1) * 100, 2)
    
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("LAAP AGI 综合测试套件报告")
    report_lines.append("=" * 80)
    report_lines.append(f"测试时间: {timestamp}")
    report_lines.append("")
    
    report_lines.append("测试概述")
    report_lines.append("-" * 80)
    report_lines.append(f"总测试数: {total_tests}")
    report_lines.append(f"通过: {total_passed}")
    report_lines.append(f"失败: {total_failed}")
    report_lines.append(f"通过率: {pass_rate}%")
    report_lines.append(f"总耗时: {total_duration:.2f}秒")
    report_lines.append("")
    
    report_lines.append("详细测试结果")
    report_lines.append("-" * 80)
    
    for i, result in enumerate(results, 1):
        report_lines.append(f"\n{i}. {result['test_file']}")
        report_lines.append("-" * 60)
        report_lines.append(f"  状态: {result['status']}")
        report_lines.append(f"  耗时: {result['duration']:.2f}秒")
        report_lines.append(f"  结果: {result['passed']}/{result['total']} 通过")
        
        if result["failed"] > 0:
            report_lines.append(f"  失败详情:")
            for line in result.get("stdout", "").split("\n")[-10:]:
                if "FAILED" in line or "ERROR" in line or "AssertionError" in line:
                    report_lines.append(f"    {line.strip()}")
        
        if result["status"] == "error":
            report_lines.append(f"  错误: {result.get('error', '')}")
    
    report_lines.append("")
    report_lines.append("=" * 80)
    
    if total_failed == 0:
        report_lines.append("所有测试通过！✓")
    else:
        report_lines.append(f"有 {total_failed} 个测试失败，请检查失败详情。✗")
    
    report_lines.append("=" * 80)
    
    return "\n".join(report_lines)


def save_report(report: str, results: list):
    """保存测试报告"""
    REPORTS_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    text_report_path = REPORTS_DIR / f"test_report_{timestamp}.txt"
    with open(text_report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    json_report_path = REPORTS_DIR / f"test_results_{timestamp}.json"
    with open(json_report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    latest_report_path = REPORTS_DIR / "latest_report.txt"
    with open(latest_report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    return text_report_path, json_report_path


def calculate_coverage():
    """计算测试覆盖率（基于测试文件和源文件）"""
    source_dir = TEST_DIR.parent / "laap" / "agi"
    test_dir = TEST_DIR
    
    source_files = list(source_dir.glob("*.py"))
    test_files = list(test_dir.glob("test_*.py"))
    
    source_lines = 0
    test_lines = 0
    
    for sf in source_files:
        try:
            source_lines += sum(1 for _ in open(sf, "r", encoding="utf-8") if _.strip())
        except:
            pass
    
    for tf in test_files:
        try:
            test_lines += sum(1 for _ in open(tf, "r", encoding="utf-8") if _.strip())
        except:
            pass
    
    return {
        "source_files": len(source_files),
        "test_files": len(test_files),
        "source_lines": source_lines,
        "test_lines": test_lines,
        "coverage_ratio": round(test_lines / max(source_lines, 1) * 100, 2),
    }


def main():
    """主函数：运行所有测试并生成报告"""
    print("=" * 80)
    print("LAAP AGI 综合测试套件")
    print("=" * 80)
    print()
    
    coverage_info = calculate_coverage()
    print("代码覆盖率概览")
    print("-" * 60)
    print(f"源文件数: {coverage_info['source_files']}")
    print(f"测试文件数: {coverage_info['test_files']}")
    print(f"源代码行数: {coverage_info['source_lines']}")
    print(f"测试代码行数: {coverage_info['test_lines']}")
    print(f"测试覆盖率: {coverage_info['coverage_ratio']}%")
    print()
    
    print("开始运行测试套件...")
    print("-" * 60)
    print()
    
    results = []
    for test_file in TEST_FILES:
        print(f"正在运行: {test_file}")
        result = run_test(test_file)
        results.append(result)
        
        status_icon = "✓" if result["status"] == "passed" else "✗"
        print(f"  {status_icon} 状态: {result['status']}")
        print(f"  结果: {result['passed']}/{result['total']} 通过")
        print(f"  耗时: {result['duration']:.2f}秒")
        print()
    
    print("测试完成！")
    print("-" * 60)
    print()
    
    report = generate_report(results)
    print(report)
    print()
    
    text_path, json_path = save_report(report, results)
    print(f"测试报告已保存:")
    print(f"  文本报告: {text_path}")
    print(f"  JSON结果: {json_path}")
    print(f"  最新报告: {REPORTS_DIR / 'latest_report.txt'}")
    
    total_failed = sum(r["failed"] for r in results)
    sys.exit(1 if total_failed > 0 else 0)


if __name__ == "__main__":
    main()
