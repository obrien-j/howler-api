import shlex
import subprocess


def prep_command(cmd: str):
    print(">", cmd)
    return shlex.split(cmd)


def main():
    print("Removing existing coverage files")
    result = subprocess.check_output(prep_command('find howler -type f -name "*.py"')).decode().strip().split("\n")

    subprocess.check_call(prep_command(f'python -m mypy {" ".join(result)}'))


if __name__ == "__main__":
    main()
