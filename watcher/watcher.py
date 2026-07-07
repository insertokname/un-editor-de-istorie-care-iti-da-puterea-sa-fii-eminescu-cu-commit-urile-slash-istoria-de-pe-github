import json
import os
import pathlib
import shutil
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone

PATTERN_FILE = "/app/pattern.uedicidpsfeccusidpg"
SCRIPT_FILE = "/app/un-editor-de-istorie-care-iti-da-puterea-sa-fii-eminescu-cu-commit-urile-slash-istoria-de-pe-github.py"

REQUIRED_VARS = [
    "GITHUB_TOKEN",
    "GITHUB_USER",
    "TARGET_COMMIT_COUNT",
    "GIT_USER_NAME",
    "GIT_USER_EMAIL",
]


def delete_repo(repo_path: str):
    subprocess.run(["gh", "repo", "delete", "--yes"], cwd=repo_path, check=True)


def create_repo(repo_path: str) -> None:
    subprocess.run(
        [
            "gh",
            "repo",
            "create",
            "--private",
            "--push",
            "--source=.",
        ],
        cwd=repo_path,
        check=True,
    )


def get_commit_count(user: str) -> int:
    try:
        out = subprocess.run(
            [
                sys.executable,
                SCRIPT_FILE,
                "--get-commit-count",
                "--user",
                user,
            ],
            check=True,
            text=True,
            capture_output=True,
        )

    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}", flush=True)
        print("STDOUT:", e.stdout, flush=True)
        print("STDERR:", e.stderr, flush=True)
        raise
    return int(out.stdout.strip().split("\n")[-1].strip())


def generate_history(repo_path: str, target: int, user: str, message: str) -> None:
    subprocess.run(
        [
            sys.executable,
            SCRIPT_FILE,
            PATTERN_FILE,
            "-o",
            repo_path,
            "--total-commit-count",
            str(target),
            "--user",
            user,
            "-m",
            message,
        ],
        check=True,
    )


def main():
    missing = []
    for var in REQUIRED_VARS:
        if not os.environ.get(var):
            missing.append(var)
    if len(missing) > 0:
        print(f"Error: missing required environment variable(s): {', '.join(missing)}", flush=True)
        return

    user_name = os.environ["GIT_USER_NAME"]
    user_email = os.environ["GIT_USER_EMAIL"]

    subprocess.run(["git", "config", "--global", "user.name", user_name], check=True)
    subprocess.run(["git", "config", "--global", "user.email", user_email], check=True)
    subprocess.run(
        ["git", "config", "--global", "init.defaultBranch", "main"], check=True
    )
    subprocess.run(
        ["git", "config", "--global", "--add", "safe.directory", "*"], check=True
    )

    while True:
        user = os.environ["GITHUB_USER"]
        target = int(os.environ["TARGET_COMMIT_COUNT"])
        message = os.environ.get("COMMIT_MESSAGE", "uedicidpsfeccusidpg")

        current = get_commit_count(user)
        print(f"current contributions:{current}\ntarget contributions: {target}", flush=True)

        if current != target:
            data_dir = pathlib.Path("/data").iterdir()

            for dir in data_dir:
                if not dir.is_dir() and not dir.name.startswith("github-history-art-"):
                    continue
                resolved_dir = str(dir.resolve())
                try:
                    print(f"deleting repo: {resolved_dir}", flush=True)
                    delete_repo(resolved_dir)
                except Exception as e:
                    print(
                        f'Error: couldn\'t delete repository: {dir.name}!\nGot error: {e}\nDeleting the physical directory "{resolved_dir}" anyway!', flush=True
                    )
                finally:

                    def remove_readonly(func, path, _):
                        os.chmod(path, stat.S_IWRITE)
                        func(path)

                    shutil.rmtree(resolved_dir, onerror=remove_readonly)
                    print(f"deleted: {resolved_dir}", flush=True)

            print("waiting 15 seconds so that the deletion propagates and graphql will return an ok answer", flush=True)
            time.sleep(15)

            new_name = f"github-history-art-{datetime.now(timezone.utc):%Y-%m-%d-%H-%M-%S}"
            repo_path = os.path.join("/data", new_name)

            print(f"generating commit history in {repo_path}", flush=True)
            generate_history(repo_path, target, user, message)

            print(f"creating and uploading the new private repo: {new_name}", flush=True)
            create_repo(repo_path)


        interval = int(os.environ.get("INTERVAL_SECONDS", "1800"))
        print("repo should be up", flush=True)
        print(f"waiting for {interval} seconds", flush=True)
        time.sleep(interval)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"!!!Got an error while running a subcommand!!!\nError was: {e}\n\n!!!This container will automatically restart!!!\n\n", flush=True)
