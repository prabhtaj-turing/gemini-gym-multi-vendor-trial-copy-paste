"""Run pytest suite with FC checkers enabled and emit a markdown report.

This script enables the FC checker compliance layer globally before invoking
pytest. The goal is to surface schema mismatches that may otherwise be
suppressed when the FC checkers are disabled by default.

The script mirrors the repository's existing tooling patterns (for example
`run_tool_spec_model_check.py`) so it can be invoked locally or from CI.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Sequence
import pytest
from io import StringIO
from tabulate import tabulate


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

APIS_DIR = REPO_ROOT / "APIs"
if str(APIS_DIR) not in sys.path:
    sys.path.insert(0, str(APIS_DIR))

# Reduce overhead from extra logging during FC checker runs by disabling
# LOG_RECORDS_FETCHED dynamically for this process (affects init_utils logic)
try:
    import importlib
    _common_utils = importlib.import_module("common_utils")
    if hasattr(_common_utils, "LOG_RECORDS_FETCHED"):
        _common_utils.LOG_RECORDS_FETCHED = False
except Exception:
    pass


def _run_pytest_with_fc_checkers(
    pytest_args: List[str],
    log_to_csv: bool,
    csv_path: Optional[str],
    raise_errors: bool,
) -> tuple[int, str, str]:
    """Run pytest programmatically with FC checkers enabled."""

    # Import and configure FC checkers
    try:
        from common_utils.fc_checkers_manager import (  # type: ignore[import]
            reset_fc_checkers_manager,
            get_fc_checkers_manager,
        )
    except ImportError:
        from APIs.common_utils.fc_checkers_manager import (  # type: ignore
            reset_fc_checkers_manager,
            get_fc_checkers_manager,
        )

    reset_fc_checkers_manager()
    manager = get_fc_checkers_manager()
    manager.set_global_validation(True)
    manager.set_global_raise_errors(raise_errors)

    if log_to_csv:
        manager.set_global_logging(True, csv_path=csv_path)
    else:
        manager.set_global_logging(False)

    # Enable skip_negative_tests to avoid logging validation errors from negative test cases
    manager.set_skip_negative_tests(True)
    
    print("✅ FC checkers enabled globally for test run.")
    print("➡️  Running: pytest", " ".join(pytest_args))

    # Run pytest - output will be shown live, we don't capture it
    # The CSV will contain all validation data we need for reporting
    exit_code = pytest.main(pytest_args)
    
    # Return empty strings for stdout/stderr - we don't need them
    # The report will be generated from CSV data and exit code only
    return exit_code, "", ""


def _tail(text: str, limit: int = 4000) -> str:
    """Return the last ``limit`` characters of ``text`` (useful for reports)."""

    if len(text) <= limit:
        return text
    return text[-limit:]


def _extract_test_stats(stdout: str) -> Dict[str, str]:
    """Extract test statistics from pytest output."""
    stats = {
        "total": "0",
        "passed": "0", 
        "failed": "0",
        "skipped": "0",
        "errors": "0",
        "collected": "0",
    }
    
    # Look for pytest summary line like "== 1 failed, 343 passed in 4.07s =="
    import re
    
    # Check for collected items first
    collected_match = re.search(r"collected (\d+) items?", stdout)
    if collected_match:
        stats["collected"] = collected_match.group(1)
    
    summary_match = re.search(r"=+\s*(.*?)\s*in\s*[\d.]+s\s*=+", stdout)
    if summary_match:
        summary_text = summary_match.group(1)
        for part in summary_text.split(","):
            part = part.strip()
            if "passed" in part:
                stats["passed"] = part.split()[0]
            elif "failed" in part:
                stats["failed"] = part.split()[0]
            elif "skipped" in part:
                stats["skipped"] = part.split()[0]
            elif "error" in part:
                stats["errors"] = part.split()[0]
    
    # If no summary (e.g., no tests collected), total remains 0
    if stats["collected"] != "0":
        stats["total"] = str(
            int(stats["passed"]) + int(stats["failed"]) + 
            int(stats["skipped"]) + int(stats["errors"])
        )
    return stats


def _write_report(
    exit_code: int,
    stdout: str,
    stderr: str,
    pytest_args: List[str],
    report_path: Path,
    csv_rows: Optional[List[Dict[str, str]]] = None,
    csv_headers: Optional[Sequence[str]] = None,
) -> None:
    """Persist a markdown summary for GitHub workflow comments."""

    # Extract test stats from stdout if available, otherwise rely on exit code
    test_stats = _extract_test_stats(stdout) if stdout else {"total": "0", "passed": "0", "failed": "0", "skipped": "0", "errors": "0", "collected": "0"}
    
    report_lines = []

    # Check test execution status based on pytest exit codes
    test_execution_failed = False
    
    if exit_code == 2:
        report_lines.extend([
            f"❌ **Test collection errors occurred**",
            "_Tests failed during collection phase. Please fix import/syntax errors before schema compliance can be checked._",
            ""
        ])
        test_execution_failed = True
    elif exit_code == 3:
        report_lines.extend([
            f"❌ **Internal error during test execution**",
            "_An internal pytest error occurred. Check the output above for details._",
            ""
        ])
        test_execution_failed = True
    elif exit_code == 4:
        report_lines.extend([
            f"❌ **Invalid pytest usage**",
            "_Command line usage error. Check pytest arguments._",
            ""
        ])
        test_execution_failed = True
    elif exit_code == 5:
        report_lines.extend([
            f"⚠️ **No tests collected**",
            "_No tests were found. Check test path and file patterns._",
            ""
        ])
        test_execution_failed = True
    elif exit_code > 1 and exit_code not in [0, 1]:
        report_lines.extend([
            f"❌ **Test execution error** (exit code: {exit_code})", 
            "_Unexpected test failure. Please check the test output above._",
            ""
        ])
        test_execution_failed = True
    
    # If exit code is 0 or 1 (tests passed/failed normally), show FC validation results
    # Don't show detailed test stats since we don't have stdout

    # Only show schema validation section if tests actually ran
    if not test_execution_failed:
        # Add a simple status line
        if exit_code == 0:
            report_lines.append("✅ **Tests executed successfully**\n")
        elif exit_code == 1:
            report_lines.append("⚠️ **Tests executed (some test failures occurred)**\n")
    
    if not test_execution_failed and csv_rows:
        # Count unique issues by error_id
        unique_errors: dict[str, list[dict[str, str]]] = {}
        for row in csv_rows:
            error_id = row.get("error_id", "")
            if error_id:
                if error_id not in unique_errors:
                    unique_errors[error_id] = []
                unique_errors[error_id].append(row)
        
        report_lines.extend([
            "",
            "### 🔍 Schema Compliance Issues Found",
            f"- **Unique issue types**: {len(unique_errors)}",
            f"- **Total occurrences**: {len(csv_rows)}",
            "",
            "_These are schema vs tool request/response data compliance issues detected by FC Checkers, not test failures._",
        ])
        
        # Only show specific columns
        headers = [
            "error_id",
            "service_name", 
            "function_name",
            "validation_type",
            "data_type",
            "error_path",
            "error_message"
        ]
        
        report_lines.extend([
            "### Issue Details",
            "",
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ])
        
        # Show one example per unique error_id
        for error_id, error_instances in unique_errors.items():
            row = error_instances[0]  # Take first instance
            report_lines.append(
                "| "
                + " | ".join(
                    (row.get(col, "") or "").replace("\n", " ").replace("|", "\\|")
                    for col in headers
                )
                + " |"
            )
            if len(error_instances) > 1:
                report_lines[-1] += f" *(+{len(error_instances)-1} more)*"
        
        # Add collapsed section with all results
        if len(csv_rows) > 0:
            report_lines.extend([
                "",
                "<details>",
                "<summary><b>📋 All Validation Results</b> (click to expand)</summary>",
                "",
                "| error_id | service_name | function_name | data_type | error_path | error_message |",
                "| --- | --- | --- | --- | --- | --- |",
            ])
            
            # Limit to prevent huge comments
            max_rows = 200
            display_rows = csv_rows[:max_rows]
            
            for row in display_rows:
                report_lines.append(
                    "| " + " | ".join(
                        (row.get(col, "") or "").replace("\n", " ").replace("|", "\\|")
                        for col in ["error_id", "service_name", "function_name", "data_type", "error_path", "error_message"]
                    ) + " |"
                )
            
            if len(csv_rows) > max_rows:
                report_lines.extend([
                    "",
                    f"*... and {len(csv_rows) - max_rows} more results*"
                ])
            
            report_lines.extend([
                "",
                "</details>"
            ])
    elif not test_execution_failed:
        # Only show "no issues" if tests actually ran
        report_lines.extend([
            "",
            "### ✅ No Schema compliance Issues",
            "_No schema compliance errors detected by FC Checkers._"
        ])
    
    # Add instructions for running locally if not a test execution failure
    if not test_execution_failed:
        report_lines.extend([
            "",
            "---",
            "### 📝 Results Reproduction",
            "_To see full logs and debug locally, run:_",
            "```bash",
            "python Scripts/run_fc_checker_tests.py -- <test_path>",
            "# Add --csv-path <file> to save all errors to CSV",
            "```"
        ])
        
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"📝 Report written to {report_path}")


def _print_csv_results_to_log(csv_rows: List[Dict[str, str]], columns: List[str], title: str) -> None:
    """Pretty-print CSV rows to stdout for GitHub Actions logs.
    Uses collapsible group markers and tabulate for human-readable tables.
    Always emits a group, even when there are no rows.
    """
    print(f"::group::{title}")
    if not csv_rows:
        print("No schema compliance issues (0 rows).")
        print("::endgroup::")
        return
    # Build rows in the requested order; coerce None to empty strings
    rows: List[List[str]] = []
    for row in csv_rows:
        rows.append([(row.get(col, "") or "") for col in columns])
    try:
        print(tabulate(rows, headers=columns, tablefmt="grid", stralign="left", maxcolwidths=[40]*len(columns)))
    except Exception:
        # Fallback simple rendering
        print("| " + " | ".join(columns) + " |")
        print("| " + " | ".join(["---"]*len(columns)) + " |")
        for r in rows:
            print("| " + " | ".join(r) + " |")
    print("::endgroup::")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run pytest with FC checkers enabled and emit a markdown report."
    )
    parser.add_argument(
        "--log-to-csv",
        dest="log_to_csv",
        action="store_true",
        help="Enable CSV logging while FC checkers run (default)",
    )
    parser.add_argument(
        "--no-log-to-csv",
        dest="log_to_csv",
        action="store_false",
        help="Disable CSV logging during the run",
    )
    parser.set_defaults(log_to_csv=True)
    parser.add_argument(
        "--csv-path",
        default="fc_checker_errors.csv",
        help="CSV path for logged validation errors.",
    )
    parser.add_argument(
        "--raise-errors",
        dest="raise_errors",
        action="store_true",
        help="Force FC checkers to raise on validation failures (default).",
    )
    parser.add_argument(
        "--no-raise-errors",
        dest="raise_errors",
        action="store_false",
        help="Allow validation failures without raising exceptions.",
    )
    parser.set_defaults(raise_errors=True)
    parser.add_argument(
        "--report-file",
        default="fc_checker_test_report.md",
        help="Where to write the markdown summary (default: fc_checker_test_report.md).",
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed directly to pytest (prefix with '--').",
    )
    return parser.parse_args()


def _get_service_directories() -> List[str]:
    """Get all service directories in APIs/ (excluding common_utils)."""
    apis_dir = REPO_ROOT / "APIs"
    services = []
    for path in apis_dir.iterdir():
        if path.is_dir() and path.name not in ["common_utils", "__pycache__"]:
            # Check if it has tests
            test_dir = path / "tests"
            if test_dir.exists():
                services.append(f"APIs/{path.name}")
    return sorted(services)


def main() -> int:
    args = parse_args()

    pytest_args = [arg for arg in args.pytest_args if arg != "--"]
    
    # Determine if we should run per-service or as specified
    if not pytest_args or pytest_args == ["APIs"]:
        # Run per service to avoid conflicts
        services = _get_service_directories()
        print(f"📦 Found {len(services)} services to test individually")
        return _run_all_services(services, args)
    else:
        # Run as specified
        return _run_single_target(pytest_args, args)


def _run_single_target(pytest_args: List[str], args: argparse.Namespace) -> int:
    """Run tests for a single target (service or custom path)."""
    csv_path: Optional[Path] = None
    if args.log_to_csv:
        csv_path = Path(args.csv_path).resolve()
        if csv_path.exists():
            csv_path.unlink()

    exit_code, stdout, stderr = _run_pytest_with_fc_checkers(
        pytest_args,
        log_to_csv=args.log_to_csv,
        csv_path=str(csv_path) if csv_path is not None else None,
        raise_errors=args.raise_errors,
    )
    
    # Output was already shown live during pytest execution
    # No need to print anything here

    report_path = (Path(os.getcwd()) / args.report_file).resolve()
    csv_rows: Optional[List[Dict[str, str]]] = None
    csv_headers: Optional[Sequence[str]] = None
    if args.log_to_csv and csv_path and csv_path.exists():
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            csv_rows = list(reader)
            csv_headers = reader.fieldnames

    _write_report(
        exit_code,
        stdout,
        stderr,
        pytest_args,
        report_path,
        csv_rows=csv_rows,
        csv_headers=csv_headers,
    )

    # Pretty print full CSV results to the log for easy human inspection
    _print_csv_results_to_log(
        csv_rows or [],
        [
            "error_id",
            "service_name",
            "function_name",
            "validation_type",
            "data_type",
            "error_path",
            "error_message",
        ],
        title="FC Checker Results (all rows)"
    )

    # Exit code 4 means no tests collected - treat as success with warning
    if exit_code == 4:
        print("⚠️  No tests were collected - treating as success with warning")
        return 0
    return exit_code


def _run_all_services(services: List[str], args: argparse.Namespace) -> int:
    """Run tests for each service individually and aggregate results."""
    all_csv_rows = []
    service_results = {}
    overall_exit_code = 0
    
    # Clear main CSV if it exists
    main_csv_path = Path(args.csv_path).resolve()
    if main_csv_path.exists():
        main_csv_path.unlink()
    
    for service in services:
        service_name = service.split("/")[1]
        print(f"\n{'='*60}")
        print(f"🧪 Testing service: {service_name}")
        print('='*60)
        
        # Create temporary CSV for this service
        temp_csv = Path(f"fc_checker_{service_name}.csv")
        if temp_csv.exists():
            temp_csv.unlink()
        
        exit_code, stdout, stderr = _run_pytest_with_fc_checkers(
            [service],
            log_to_csv=args.log_to_csv,
            csv_path=str(temp_csv) if args.log_to_csv else None,
            raise_errors=args.raise_errors,
        )
        
        # Collect results
        service_csv_rows = []
        if args.log_to_csv and temp_csv.exists():
            with temp_csv.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                service_csv_rows = list(reader)
                all_csv_rows.extend(service_csv_rows)
            temp_csv.unlink()  # Clean up temp file
        
        service_results[service_name] = {
            "exit_code": exit_code,
            "csv_rows": service_csv_rows,
        }
        
        if exit_code not in [0, 4]:  # 4 = no tests collected
            overall_exit_code = 1
    
    # Write aggregated CSV
    if args.log_to_csv and all_csv_rows:
        with main_csv_path.open("w", encoding="utf-8", newline="") as handle:
            if all_csv_rows:
                fieldnames = all_csv_rows[0].keys()
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_csv_rows)
    
    # Generate aggregated report
    report_path = (Path(os.getcwd()) / args.report_file).resolve()
    _write_aggregated_report(service_results, all_csv_rows, report_path)

    # Also print aggregated full CSV to the log
    _print_csv_results_to_log(
        all_csv_rows or [],
        [
            "error_id",
            "service_name",
            "function_name",
            "validation_type",
            "data_type",
            "error_path",
            "error_message",
        ],
        title="FC Checker Results (aggregated across services)"
    )

    return overall_exit_code


def _write_aggregated_report(
    service_results: Dict[str, Dict],
    all_csv_rows: List[Dict[str, str]],
    report_path: Path
) -> None:
    """Write an aggregated report for all services."""
    report_lines = []
    
    # Overall FC Checker compliance summary first
    if all_csv_rows:
        unique_errors: dict[str, list[dict[str, str]]] = {}
        for row in all_csv_rows:
            error_id = row.get("error_id", "")
            if error_id:
                if error_id not in unique_errors:
                    unique_errors[error_id] = []
                unique_errors[error_id].append(row)
        
        report_lines.extend([
            "## 🔍 Compliance Issues Summary",
            f"- **Total services with issues**: {len(set(r['service_name'] for r in all_csv_rows if 'service_name' in r))}",
            f"- **Unique issue types**: {len(unique_errors)}",
            f"- **Total occurrences**: {len(all_csv_rows)}",
            "",
        ])
    else:
        report_lines.extend([
            "## ✅ No Schema Compliance Issues",
            "_No schema compliance errors detected across all services._",
            "",
        ])
    
    # Service-level summary table - only show services with issues
    report_lines.extend([
        "## 📊 Service Wise Summary",
        "_Showing only services with test failures or FC compliance issues_",
        "",
        "| Service | Status | FC Issues |",
        "| --- | --- | --- |"
    ])
    
    passing_services = []
    
    for service_name, results in sorted(service_results.items()):
        csv_rows = results["csv_rows"]
        exit_code = results["exit_code"]
        
        fc_issues = len(csv_rows)
        
        if exit_code == 2:
            status = "❌ Collection Error"
        elif exit_code == 4:
            status = "⚠️ No Tests"
        elif exit_code == 5:
            status = "⚠️ No Tests"
        elif exit_code == 0:
            # Check if there are FC issues even though tests passed
            if fc_issues > 0:
                status = "⚠️ FC Issues"
            else:
                status = "✅ Passed"
        elif exit_code == 1:
            # Some tests failed
            if fc_issues > 0:
                status = "❌ Failed + FC Issues"
            else:
                status = "❌ Test Failed"
        else:
            status = "❌ Error"
        
        # Only add to table if there are issues
        if status != "✅ Passed":
            report_lines.append(f"| {service_name} | {status} | {fc_issues} |")
        else:
            passing_services.append(service_name)
    
    # Add a note about passing services with names
    if passing_services:
        report_lines.append("")
        if len(passing_services) <= 10:
            report_lines.append(f"_✅ Passed with no FC issues: {', '.join(passing_services)}_")
        else:
            report_lines.append(f"_✅ {len(passing_services)} services passed with no FC issues: {', '.join(passing_services)}_")
    
    # Show per-service issues details in a collapsible section
    if all_csv_rows:
        report_lines.extend([
            "",
            "<details>",
            "<summary><b>📋 Per-Service Issue Details</b> (click to expand)</summary>",
            "",
        ])
        
        services_with_issues: dict[str, list[dict[str, str]]] = {}
        for row in all_csv_rows:
            service = row.get("service_name", "unknown")
            if service not in services_with_issues:
                services_with_issues[service] = []
            services_with_issues[service].append(row)
        
        for service_name in sorted(services_with_issues.keys()):
            issues = services_with_issues[service_name]
            report_lines.extend([
                f"### {service_name} ({len(issues)} issues)",
                "",
                "| error_id | function_name | path | type | error_message |",
                "| --- | --- | --- | --- | --- |"
            ])
            
            # Show unique issues for this service
            shown_errors = set()
            for row in issues[:15]:  # Limit per service
                error_id = row.get("error_id", "")
                if error_id not in shown_errors:
                    shown_errors.add(error_id)
                    # Determine type (input/output) from data_type field
                    data_type = row.get('data_type', '')
                    type_label = 'input' if 'input' in data_type.lower() else 'output' if 'output' in data_type.lower() else data_type
                    report_lines.append(
                        f"| {error_id[:8]} | {row.get('function_name', '')} | "
                        f"{row.get('error_path', '')} | {type_label} | "
                        f"{(row.get('error_message', '')[:180] + '...') if len(row.get('error_message', '')) > 180 else row.get('error_message', '')} |"
                    )
            
            if len(issues) > 15:
                report_lines.append(f"*... and {len(issues) - 15} more issues*")
            report_lines.append("")
        
        report_lines.append("</details>")
    
    # Add instructions for running locally
    report_lines.extend([
        "",
        "## 📝 Results Reproduction",
        "_To see full logs and debug locally, run:_",
        "```bash",
        "# Test all services:",
        "python Scripts/run_fc_checker_tests.py",
        "",
        "# Test specific service:",
        "python Scripts/run_fc_checker_tests.py -- APIs/<service_name>",
        "",
        "# Generate CSV with all validation errors:",
        "python Scripts/run_fc_checker_tests.py --csv-path fc_checker_errors.csv",
        "```"
    ])
    
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\n📝 Aggregated report written to {report_path}")


if __name__ == "__main__":
    sys.exit(main())

