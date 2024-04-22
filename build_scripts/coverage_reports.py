import os
import re
import shlex
import subprocess
import sys
import textwrap


def get_color(percentage):
    if percentage < 50:
        return "red"
    elif percentage < 70:
        return "yellow"
    else:
        return "green"


def generate_badge(title, percentage, color):
    return f"![Static Badge](https://img.shields.io/badge/{title.replace(' ', '_')}-{percentage}25-{color}?style=flat&logo=azuredevops&logoColor=%230078D7)"


def main():
    print(f"Running on branch {os.environ.get('GIT_BRANCH', 'unknown')}")

    develop = "develop" in os.environ.get("GIT_BRANCH", "unknown")
    rc_or_main = any(x in os.environ.get("GIT_BRANCH", "unknown") for x in ["patch", "rc", "main", "master"])
    pr_branch = "origin/" + os.environ.get("PR_BRANCH", "develop")

    try:
        report_result = subprocess.check_output(shlex.split("coverage report --data-file=.coverage")).decode()
        subprocess.check_output(shlex.split("coverage xml --data-file=.coverage"))
        subprocess.check_output(shlex.split("coverage html --data-file=.coverage"))

        print(report_result)

        if not develop and not rc_or_main:
            diff_report_result = subprocess.check_output(
                shlex.split(
                    f"diff-cover coverage.xml --compare-branch={pr_branch} --markdown-report diff-cover-report.md"
                )
            ).decode()
            print(diff_report_result)

        total_percentage = report_result.splitlines().pop().split(" ").pop()
        total_percentage_int = int(total_percentage.replace("%", ""))
        total_color = get_color(total_percentage_int)

        if not develop and not rc_or_main:
            try:
                diff_percentage = (
                    [line for line in diff_report_result.splitlines() if "Coverage:" in line].pop().split(" ").pop()
                )
                diff_percentage_int = int(diff_percentage.replace("%", ""))
            except IndexError:
                diff_percentage = "NA%"
                diff_percentage_int = 0

            diff_color = get_color(diff_percentage_int)

            with open("diff-cover-report.md") as diff_report:
                diff_result = diff_report.read().replace("# ", "## ").replace("__init__.py", "\\_\\_init\\_\\_.py")

                diff_result = re.sub(r"### (.+py)", r"<details>\n<summary>\1</summary>\n", diff_result)
                diff_result = re.sub(r"\n---(\n+<details>)", r"\n</details>\1", diff_result)

                diff_result += "\n</details>"

        newline = "\n"
        markdown_output = textwrap.dedent(
            f"""
        ![Static Badge](https://img.shields.io/badge/build-passing-brightgreen)

        # Coverage Results
        {generate_badge('Total Coverage', total_percentage, total_color)} {generate_badge('Diff Coverage', diff_percentage, diff_color) if (not develop and not rc_or_main) else ''}

{newline.join([(' ' * 8) + line for line in diff_result.splitlines()]) if (not develop and not rc_or_main) else ''}

        ## Full Coverage Report
        <details>
            <summary>Expand</summary>

{newline.join([(' ' * 12) + line for line in report_result.splitlines()])}
        </details>
        """
        ).strip()

        print("Markdown result:")
        print(markdown_output)

        if os.environ.get("TF_BUILD", None):
            print("##vso[task.setvariable variable=coverage_result]" + markdown_output.replace("\n", "%0D%0A") + "\n\n")
    except subprocess.CalledProcessError as e:
        print(" ".join(e.cmd), "failed.")

        if e.output:
            print(e.output.decode())

        sys.exit(e.returncode)


if __name__ == "__main__":
    main()
