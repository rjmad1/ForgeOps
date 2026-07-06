import sys
import os
import pytest
from unittest.mock import MagicMock, patch
from scripts.install import PreReqDetector, run_command

def test_detect_python():
    res = PreReqDetector.detect_python()
    assert res["installed"] is True
    assert "Python" in res["name"]
    assert res["version"] == f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

@patch("scripts.install.run_command")
def test_detect_git_success(mock_run):
    mock_run.return_value = "git version 2.40.1.windows.1"
    res = PreReqDetector.detect_git()
    assert res["installed"] is True
    assert res["version"] == "2.40.1.windows.1"

@patch("scripts.install.run_command")
def test_detect_git_fail(mock_run):
    mock_run.return_value = None
    res = PreReqDetector.detect_git()
    assert res["installed"] is False
    assert res["version"] is None

@patch("scripts.install.run_command")
def test_detect_docker_success(mock_run):
    mock_run.return_value = "Docker version 20.10.23, build 71552b5"
    res = PreReqDetector.detect_docker()
    assert res["installed"] is True
    assert res["version"] == "20.10.23"

@patch("scripts.install.run_command")
def test_detect_cuda_none(mock_run):
    mock_run.return_value = None
    with patch.dict(os.environ, {}, clear=True):
        res = PreReqDetector.detect_cuda()
        assert res["installed"] is False
        assert res["version"] is None

@patch("scripts.install.run_command")
def test_detect_cuda_env(mock_run):
    mock_run.return_value = None
    with patch.dict(os.environ, {"CUDA_PATH": "C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.1"}):
        res = PreReqDetector.detect_cuda()
        assert res["installed"] is True
        assert "v12.1" in res["details"]
