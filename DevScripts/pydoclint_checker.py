import subprocess
import re
import csv
import sys
import argparse
import ast
from pathlib import Path

def run_pydoclint_and_filter_csv(
    output_csv_path: str = "pydoclint_report.csv",
    pydoclint_args: list | None = None,
) -> None:
    """Run pydoclint and export a filtered CSV report.

    Filters out DOC503 violations where the only difference in exception names
    is a module prefix (e.g., 'custom_errors.TicketNotFoundError' vs 'TicketNotFoundError').

    Args:
        output_csv_path: Path to write the filtered CSV report.
        pydoclint_args: Arguments to pass to pydoclint. If None, sensible defaults are used.
    """
    if pydoclint_args is None:
        current_file_dir = Path(__file__).parent
        api_gen_dir = current_file_dir.parent / "APIs"
        print(api_gen_dir)
        pydoclint_args = _build_default_args()

    # Build command using module invocation to avoid PATH issues
    cmd = ["pydoclint"] + [str(arg) for arg in pydoclint_args]
    # Print the exact command being executed for debug purposes
    print("Executing command:", " ".join(f'"{c}"' if " " in str(c) else str(c) for c in cmd))

    # Run pydoclint and capture output
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            check=False,
        )
    except FileNotFoundError:
        print(
            "pydoclint is not installed or not found in PATH. Install it with: pip install pydoclint",
            file=sys.stderr,
        )
        sys.exit(1)
    output = proc.stdout

    # For debugging, print stderr if stdout is empty
    if not output and proc.stderr:
        print("--- pydoclint stderr ---", file=sys.stderr)
        print(proc.stderr, file=sys.stderr)
        print("------------------------", file=sys.stderr)

    output = proc.stderr

    # Parse output into rows
    # Each violation is a line like:
    # APIs/zendesk/Comments.py:6: DOC503: Function `list_ticket_comments` exceptions in the "Raises" section in the docstring do not match those in the function body. Raised exceptions in the docstring: ['TicketNotFoundError', 'TypeError']. Raised exceptions in the body: ['TypeError', 'custom_errors.TicketNotFoundError'].
    violation_pattern = re.compile(
        r"^(?P<file>.+?):(?P<line>\d+): (?P<code>DOC\d+): (?P<message>.+)$"
    )

    filtered_rows = []
    skipped_due_to_prefix_only = 0
    
    def _parse_exception_list(list_literal: str) -> list[str] | None:
        """Parse a Python list literal of exception names safely.

        Falls back to regex tokenization if literal parsing fails.
        """
        try:
            parsed = ast.literal_eval(list_literal)
            if isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
                return parsed
        except Exception:
            pass

        # Fallback: extract quoted strings (both single and double quotes)
        # Example: ['A', "B.C"] -> ["A", "B.C"]
        tokens = re.findall(r"'([^']+)'|\"([^\"]+)\"", list_literal)
        flat = [a or b for a, b in tokens]
        return flat if flat else None
    for line in output.splitlines():
        m = violation_pattern.match(line)
        if not m:
            continue
        file = m.group("file")
        # Remove everything before and including 'APIs/' in the file path, if present
        file = re.sub(r'^.*?APIs/', '', file)
        line_num = m.group("line")
        code = m.group("code")
        message = m.group("message")

        # Special handling for DOC503 (raises mismatch)
        if code == "DOC503":
            # Try to extract the two lists of exceptions
            docstring_excs = None
            body_excs = None
            docstring_match = re.search(
                r"Raised exceptions in the docstring: (\[.*?\])", message
            )
            body_match = re.search(
                r"Raised exceptions in the body: (\[.*?\])", message
            )
            if docstring_match and body_match:
                docstring_excs = _parse_exception_list(docstring_match.group(1))
                body_excs = _parse_exception_list(body_match.group(1))

            if docstring_excs is not None and body_excs is not None:
                # Remove any module prefixes from exception names for comparison
                def strip_prefix(exc: str) -> str:
                    return exc.split(".")[-1]

                docstring_set = {strip_prefix(e) for e in docstring_excs}
                body_set = {strip_prefix(e) for e in body_excs}
                if docstring_set == body_set:
                    # Only difference is prefix, so skip this violation
                    skipped_due_to_prefix_only += 1
                    continue

            # Remove 'custom_errors.' prefix from the message for output
            message = re.sub(r'custom_errors\.', '', message)

        # Otherwise, keep the violation
        filtered_rows.append([file, line_num, code, message])

    # Write to CSV
    with open(output_csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["file", "line", "code", "message"])
        for row in filtered_rows:
            writer.writerow(row)

    print(
        f"Filtered pydoclint report written to {output_csv_path} (skipped {skipped_due_to_prefix_only} DOC503 with prefix-only diffs)"
    )

def _build_default_args() -> list:
    current_file_dir = Path(__file__).parent
    api_gen_dir = current_file_dir.parent / "APIs"
    print(api_gen_dir)
    return [
        api_gen_dir,
        "--style=google",
        "--check-return-types=false",
        "--skip-checking-raises=false",
        "--exclude=SimulationEngine|tests|mutations|common_utils",
        "--show-filenames-in-every-violation-message=true",
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Run pydoclint and export a filtered CSV report that ignores DOC503 "
            "violations differing only by module prefixes."
        )
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_csv_path",
        default="pydoclint_report.log.csv",
        help="Path to write the filtered CSV report (default: pydoclint_report.log.csv)",
    )

    # Parse known args, pass the rest through to pydoclint
    args, passthrough = parser.parse_known_args()

    # Remove a leading "--" separator if present (common pattern)
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]

    pydoclint_args = passthrough if passthrough else _build_default_args()

    run_pydoclint_and_filter_csv(
        output_csv_path=args.output_csv_path,
        pydoclint_args=pydoclint_args,
    )
