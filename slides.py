# -*- coding: utf-8 -*-
"""
# How to use


"""
import os
import shutil
import subprocess as sub
import sys
from datetime import datetime, timedelta

from colored import attr, bg, fg


def time_color(
    now,
    end,
    rules,
    ok=fg("green"),
    passed=fg("white") + bg("red"),
    fmt="{color}{sign}{duration}",
):
    def duration2str(duration):
        return f"{duration.seconds // 60:02d}:{duration.seconds % 60:02d}"

    if now > end:
        return fmt.format(sign="+", color=passed, duration=duration2str(now - end))

    duration = end - now
    for rule_duration, rule_color in rules:
        if duration < rule_duration:
            return fmt.format(
                color=rule_color, sign="-", duration=duration2str(duration)
            )

    return fmt.format(color=ok, sign="-", duration=duration2str(duration))


class Presentation:
    def __init__(
        self,
        total=20,
        conclusion=3,
        goodby=1,
        ok_color=fg("green"),
        half_color=fg("cyan"),
        conclusion_color=fg("yellow"),
        goodby_color=fg("red"),
        passed_color=fg("white") + bg("red"),
        cmd_color=fg("white") + bg("blue"),
        fmt_time="{color}{sign}{duration}",
        cwd=".",
    ):
        self.duration = timedelta(minutes=total)
        self.time_rules = [
            (timedelta(minutes=goodby), goodby_color),
            (timedelta(minutes=conclusion), conclusion_color),
            (timedelta(minutes=total // 2), half_color),
        ]
        self.ok_color = ok_color
        self.passed_color = passed_color
        self.cmd_color = cmd_color
        self.fmt_time = fmt_time
        self.cwd = cwd

        self._start = None
        self._end = None
        self.index = None
        self._slides = []

    def add(self, action, *args, **kwargs):
        self._slides.append((getattr(self, action), args, kwargs))

    def prompt(self, topic=None):
        time = time_color(
            datetime.now(),
            self._end,
            self.time_rules,
            ok=self.ok_color,
            passed=self.passed_color,
            fmt=self.fmt_time,
        )
        if topic:
            return f"{self.index}) {time} – {topic}{attr(0)} » "
        return f"{self.index}) {time}{attr(0)} » "

    def start(self):
        self._start = datetime.now()
        self._end = self._start + self.duration

        for index, (action, args, kwargs) in enumerate(self._slides):
            self.index = index
            action(*args, **kwargs)
        print("Done!")

    def cd(self, path, topic=None):
        input(f"\n{self.prompt(topic)}{self.cmd_color}cd {path}{attr(0)}")
        os.chdir(path)

    def interactive(self, cmd, topic=None):
        cmdx = input(f"\n{self.prompt(topic)}{self.cmd_color}{cmd}{attr(0)}")
        # TODO: handle cmd from terminal
        sub.call(cmd, shell=True)

    def hide(self, cmd, topic=None, debug=False):
        if debug:
            print(f"\n{self.prompt(topic)}{self.cmd_color}{cmd}{attr(0)}")
            sub.call(cmd, shell=True)
        else:
            sub.call(cmd, shell=True, stdout=sub.PIPE, stderr=sub.PIPE)

    def change(self, src, dst, topic=None):
        cmdx = input(f"\n{self.prompt(topic)}{self.cmd_color}vim {dst}{attr(0)}")
        # TODO: handle cmd from terminal
        sub.call(f"vim -d {dst} {src}", shell=True)
        shutil.copyfile(src, dst)

    def cmd(self, cmd, topic=None, stream=False):
        cmdx = input(f"\n{self.prompt(topic)}{self.cmd_color}{cmd}{attr(0)}")
        # TODO: handle cmd from terminal

        sub.call(cmd, shell=True)


def pr_setup(pr):
    ## Setup
    pr.add("cmd", "mkdir -p mycm", topic="Create a directory")
    pr.add("cd", "mycm", topic="Enter in the new directory")
    pr.add("cmd", "git init", topic="Init an empty git repository")
    pr.add(
        "cmd",
        "git remote add upstream https://github.com/HotMaps/base_calculation_module.git",
        topic="Add an upstream repository",
        stream=True,
    )
    pr.add("cmd", "git pull upstream master", topic="Pull from the remote", stream=True)

    # fix the formatting of the base calculation module
    pr.add("hide", "black .")
    # pr.add("hide", "isort -rc -y")
    
    pr.add("cmd", "docker-compose -f docker-compose.tests.yml -p hotmaps up --build", topic="Test the code")

    pr.add("cmd", "git add .", topic="Add the files")
    pr.add("cmd", "git commit -m 'first commit'", topic="Commit the changes")


def pr_dev(pr):
    ## Start develop
    pr.add("cmd", "git checkout -b develop", topic="Develop")

    # directory overview
    pr.add("cmd", "tree", topic="Develop")

    pr.add("cmd", "bat  cm/requirements.txt", topic="Develop")
    pr.add("cmd", "bat  cm/app/api_v1/transactions.py", topic="Develop")
    pr.add("cmd", "bat  cm/app/constant.py", topic="Develop")
    pr.add("cmd", "bat  cm/app/api_v1/calculation_module.py", topic="Develop")

    pr.add(
        "change",
        src="../changes/00_constant.py",
        dst="cm/app/constant.py",
        topic="Develop",
    )


def get_pr():
    pr = Presentation(total=2)
    pr_setup(pr)
    pr_dev(pr)
    return pr


pr = get_pr()
pr.start()
