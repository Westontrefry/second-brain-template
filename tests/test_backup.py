"""brain backup — PLAN-UX U4: opt-in, explicit, local until pushed."""
from __future__ import annotations

import subprocess

import pytest

from brain import backup


def _git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True,
                   capture_output=True, text=True)


@pytest.fixture()
def git_sandbox(sandbox):
    _git(sandbox, "init", "-q", "-b", "main")
    _git(sandbox, "config", "user.email", "test@example.com")
    _git(sandbox, "config", "user.name", "Test")
    _git(sandbox, "add", "config.yaml")
    _git(sandbox, "commit", "-q", "-m", "seed")
    return sandbox


def test_setup_without_git_repo_says_git_init(sandbox):
    text = backup.setup_text()
    assert "git init" in text
    assert "nothing is pushed" in text


def test_setup_without_remote_manual_path(git_sandbox, monkeypatch):
    monkeypatch.setattr(backup.shutil, "which",
                        lambda name: "/usr/bin/git" if name == "git" else None)
    text = backup.setup_text()
    assert "PRIVATE" in text
    assert "git remote add origin" in text
    assert "only command that ever sends" in text


def test_setup_with_gh_offers_private_create(git_sandbox, monkeypatch):
    monkeypatch.setattr(backup.shutil, "which", lambda name: f"/usr/bin/{name}")
    text = backup.setup_text()
    assert "gh repo create" in text
    assert "--private" in text
    assert "gh auth status" in text


def test_push_without_remote_points_at_setup(git_sandbox):
    ok, message = backup.push()
    assert not ok
    assert "--setup" in message


def test_push_to_local_bare_remote(git_sandbox, tmp_path_factory):
    bare = tmp_path_factory.mktemp("remote")
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    _git(git_sandbox, "remote", "add", "origin", str(bare))
    ok, message = backup.push()
    assert ok, message
    assert "backed up: main" in message
    heads = subprocess.run(["git", "-C", str(bare), "branch"],
                           capture_output=True, text=True).stdout
    assert "main" in heads
