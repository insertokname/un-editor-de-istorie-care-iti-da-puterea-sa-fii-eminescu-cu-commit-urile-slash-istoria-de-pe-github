import argparse
from datetime import datetime, time
from html.parser import HTMLParser
from http.cookiejar import CookieJar
import shutil
import stat
import subprocess
import os
from urllib.request import HTTPCookieProcessor, Request, build_opener, urlopen
from datetime import datetime, timezone, timedelta


class UEDICIDPSFECCUSIDPGFormatException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def parse_uedicidpsfeccusidpg(filename: str) -> list[list[int]]:
    with open(filename, "r") as file:
        lines = file.readlines()
        if not (len(lines) == 7 or (len(lines) == 8 and lines[-1].isspace())):
            raise UEDICIDPSFECCUSIDPGFormatException(
                f"Invalid number of lines in uedicidpsfeccusidpg file. Expected 7, got: {len(lines)}"
            )
        lines = lines[0:7]
        out = []
        i = 1
        for line in lines:
            stripped_line = line.strip()
            if len(stripped_line) != 51:
                raise UEDICIDPSFECCUSIDPGFormatException(
                    f"Invalid line lenght for in uedicidpsfeccusidpg file. Line must have exactly 51 characters. Instead line {i} has {len(stripped_line)} characters (line: {stripped_line})"
                )

            row = []
            for j in stripped_line:
                if not j.isdigit():
                    raise UEDICIDPSFECCUSIDPGFormatException(
                        f"Invalid character specified in uedicidpsfeccusidpg file.\nAll characters must be digits!\nCharacter {j} from line {stripped_line} is not a digit!"
                    )
                row.append(int(j))
            out.append(row)
            i += 1
        return out


def uedicidpsfeccusidpg_total_days(uedicidpsfeccusidpg) -> int:
    out = 0
    for i in uedicidpsfeccusidpg:
        for j in i:
            out += j
    return out


def is_git_root(path: str) -> bool:
    return os.path.isdir(os.path.join(path, ".git"))


def get_github_user_commits(user: str) -> int:
    class Parser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.capture = False
            self.result = ""

        def handle_starttag(self, tag, attrs):
            if dict(attrs).get("id") == "js-contribution-activity-description":
                self.capture = True

        def handle_data(self, data):
            if self.capture:
                self.result = data.strip()
                self.capture = False

    opener = build_opener(HTTPCookieProcessor(CookieJar()))

    opener.open(
        Request(f"https://github.com/{user}", headers={"User-Agent": "Mozilla/5.0"})
    )
    html = (
        opener.open(
            Request(
                f"https://github.com/{user}?action=show&controller=profiles&tab=contributions&user_id={user}",
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "X-Requested-With": "XMLHttpRequest",
                },
            )
        )
        .read()
        .decode()
    )

    p = Parser()
    p.feed(html)
    return int(p.result.split()[0])


def main():
    parser = argparse.ArgumentParser(
        prog="un-editor-de-istorie-care-iti-da-puterea-sa-fii-eminescu-cu-commit-urile-slash-istoria-de-pe-github",
        description="citeste titlu bro",
    )
    parser.add_argument(
        "pattern_filename",
        help=".uedicidpsfeccusidpg file containing the pattern to be drawn.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=".",
        help="Location where to generate the git repository. (by default .)",
    )
    parser.add_argument(
        "-O",
        "--overwrite",
        help="If the location specified by --output already contains a .git repo delete it and make a new one",
        action="store_true",
    )
    parser.add_argument(
        "-c",
        "--total-commit-count",
        help="The total number of commits in the repository that will be eavenly be split across days. (also takes the user commits into account if set)",
        type=int,
    )
    parser.add_argument(
        "-p",
        "--commits-per-pixel",
        help="The total number of commits per 1 pixel (per day). (If both this and total-commit-count are unset, this defaults to 5)",
        type=int,
    )
    parser.add_argument(
        "-m",
        "--message",
        help="The message to be used for all of the generated commits. (by default uedicidpsfeccusidpg)",
        default="uedicidpsfeccusidpg",
    )
    parser.add_argument(
        "-u",
        "--user",
        help="The username that will be used to achieve the exact number of commits targeted via the -c flag. Eg: --user insertokname",
    )
    args = parser.parse_args()

    if is_git_root(args.output) and not args.overwrite:
        print(
            f"The output directory is already a git root.\nIf you want to COMPLETLEY DELETE the git repo inside the output, use the --overwrite flag.\nThis will DELETE {os.path.join(args.output, ".git")}"
        )
        return

    if args.commits_per_pixel != None and args.total_commit_count != None:
        print(
            "Error: You can't set both commits-per-pixel and total-commit-count simultaniously!\n - commits-per-pixel: always have each pixel be exactly N commits\n - total-commit-count: automatically balance out commits per day while reaching N as the total commit count (also take the user commits inco account if set)"
        )
        return
    if args.commits_per_pixel == None and args.total_commit_count == None:
        args.commits_per_pixel = 5

    uedicidpsfeccusidpg = None
    try:
        uedicidpsfeccusidpg = parse_uedicidpsfeccusidpg(args.pattern_filename)
        if not os.path.exists(args.output):
            os.makedirs(args.output)
    except Exception as e:
        print(f"Got error while parsing pattern file: {e}")
        return

    commits_per_day = 0
    extra_commits = 0

    if args.total_commit_count != None:
        if (
            uedicidpsfeccusidpg_total_days(uedicidpsfeccusidpg)
            > args.total_commit_count
        ):
            print(
                f"Error: total-commit-count must be bigger than or equal to the amount of pixels in the pattern plus 1 (for the repo initialisation commit)!\n{args.total_commit_count} must be bigger than or equal to {uedicidpsfeccusidpg_total_days(uedicidpsfeccusidpg) + 1}"
            )
            return

    if args.total_commit_count != None:
        user_commits = 0
        if args.user != None:
            try:
                print("Getting user commits...")
                user_commits = get_github_user_commits(args.user)
                print(f"For user {args.user} got total commits: {user_commits}")
                if args.total_commit_count < user_commits:
                    print(
                        f"Error: can't achieve total-commit-count since the user already has a higher ammount of commits!\nThe user has: {user_commits} commits, while the targeted ammount is: {args.total_commit_count}.\nYou must increase the total-commit-count!"
                    )
                    return
            except Exception as e:
                print(
                    f"Got error while fetching commits for user: {args.user}.\nError was: {e}"
                )
        # subtract 1 to account for the repo initialisation commit that GitHub counts as a contribution
        leftover = args.total_commit_count - user_commits - 1
        total_days = uedicidpsfeccusidpg_total_days(uedicidpsfeccusidpg)
        commits_per_day = leftover // total_days
        if commits_per_day == 0:
            print(
                f"Error: can't draw pattern since the total-commit-count: {args.total_commit_count} is too close to the user commit count: {user_commits}, so there aren't enough commits to draw each day.\nNote: 1 commit is reserved for the repo initialisation.\nYou must have a total-commit-count of at least: {user_commits + uedicidpsfeccusidpg_total_days(uedicidpsfeccusidpg)+ 1} "
            )
            return
        extra_commits = leftover % total_days
    else:
        commits_per_day = args.commits_per_pixel
        extra_commits = 0

    print(f"commits_per_day: {commits_per_day}")
    print(f"extra_commits: {extra_commits}")

    # saturdays are completley screwed for users in different timezones, for example while the us is on a saturday and can see -52 weeks in the past, japan already reached sunday so they don't see weeek -52 but instead only -51, that's why the uedicidpsfeccusidpg format only takes 51 characters per row
    UTC_12 = timezone(timedelta(hours=-12))
    today = datetime.now(UTC_12).date()
    start_of_week = today - timedelta(days=(today.weekday() + 1) % 7)
    # again, 51 weeks, not the full 52
    start_last_year = start_of_week - timedelta(days=51 * 7)

    print(f"adding commits from date: {start_last_year}")
    cur_day = start_last_year
    commits_dates = []
    for j in range(0, 51):
        for i in range(0, 7):
            if uedicidpsfeccusidpg[i][j] != 0:
                add_extra_commit = 0
                if extra_commits > 0:
                    extra_commits -= 1
                    add_extra_commit = 1
                for _ in range(0, commits_per_day + add_extra_commit):
                    commits_dates.append(datetime.combine(cur_day, time(0, 0, 0)))
            cur_day += timedelta(days=1)

    if is_git_root(args.output) and args.overwrite:
        print(f"OVERWRITE: Deleting {os.path.join(args.output,".git")}")

        def remove_readonly(func, path, _):
            os.chmod(path, stat.S_IWRITE)
            func(path)

        shutil.rmtree(
            os.path.abspath(os.path.join(args.output, ".git")),
            onerror=remove_readonly,
        )
    try:
        print(f"Creating git repo in folder: {args.output}")
        subprocess.run(
            ["git", "init", os.path.abspath(args.output)],
            capture_output=True,
            text=True,
            check=True,
        )
        default_branch = subprocess.run(
            ["git", "-C", os.path.abspath(args.output), "symbolic-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception as e:
        print(
            f"Got error while creating git repository at location: {os.path.abspath(args.output)}.\nError was: {e}"
        )
        return

    try:
        author_name = subprocess.run(
            ["git", "-C", os.path.abspath(args.output), "config", "user.name"],
            capture_output=True,
            text=True,
        ).stdout.strip()
        if not author_name:
            raise Exception(
                'No user.name was set!\nUse: git config --global user.name "Your Name"\nTo set your username!'
            )
        author_email = subprocess.run(
            ["git", "-C", os.path.abspath(args.output), "config", "user.email"],
            capture_output=True,
            text=True,
        ).stdout.strip()
        if not author_email:
            raise Exception(
                'No user.email was set!\nUse: git config --global user.email "you@example.com"\nTo set your email!'
            )
    except Exception as e:
        print(f"Got error reading git config: {e}")
        return

    try:
        msg_bytes = args.message.encode("utf-8")
        msg_len = len(msg_bytes)

        stream_parts = []
        for idx, commit_dt in enumerate(commits_dates):
            timestamp = int(commit_dt.replace(tzinfo=timezone.utc).timestamp())
            mark = idx + 1
            stream_parts.append(f"commit {default_branch}\n")
            stream_parts.append(f"mark :{mark}\n")
            stream_parts.append(
                f"author {author_name} <{author_email}> {timestamp} +0000\n"
            )
            stream_parts.append(
                f"committer {author_name} <{author_email}> {timestamp} +0000\n"
            )
            stream_parts.append(f"data {msg_len}\n")
            stream_parts.append(f"{args.message}\n")
            if idx > 0:
                stream_parts.append(f"from :{mark - 1}\n")
            stream_parts.append("\n")

        subprocess.run(
            ["git", "-C", os.path.abspath(args.output), "fast-import", "--quiet"],
            input="".join(stream_parts).encode("utf-8"),
            check=True,
        )
    except Exception as e:
        print(f"Got an error while committing to repository: {e}")


if __name__ == "__main__":
    main()
