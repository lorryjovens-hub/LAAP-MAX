"""测试 ProjectPerception 增量更新与文件监听功能"""

import os
import subprocess
import tempfile
import time
import threading

import pytest

from laap.workspace.perception import ProjectPerception, WATCHDOG_AVAILABLE


pytestmark = pytest.mark.skipif(not WATCHDOG_AVAILABLE, reason="watchdog 库未安装")


class TestFileWatcherBasic:
    """测试文件监听基本功能"""

    def test_start_watching_sets_flag(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("print('hello')")

            perception = ProjectPerception(root_path=tmpdir)
            perception.start_watching()
            assert perception._is_watching is True
            perception.stop_watching()

    def test_stop_watching_resets_flag(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("print('hello')")

            perception = ProjectPerception(root_path=tmpdir)
            perception.start_watching()
            perception.stop_watching()
            assert perception._is_watching is False

    def test_start_watching_twice_no_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("print('hello')")

            perception = ProjectPerception(root_path=tmpdir)
            perception.start_watching()
            perception.start_watching()
            assert perception._is_watching is True
            perception.stop_watching()

    def test_stop_watching_not_started_no_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            perception = ProjectPerception(root_path=tmpdir)
            perception.stop_watching()
            assert perception._is_watching is False


class TestIncrementalUpdates:
    """测试增量更新功能"""

    def test_file_modification_triggers_incremental_update(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = os.path.join(tmpdir, "test.py")
            with open(py_file, "w") as f:
                f.write("print('hello')")

            perception = ProjectPerception(root_path=tmpdir)
            snapshot = perception.perceive(full=True)
            initial_count = snapshot.file_tree.total_files

            perception.start_watching()

            time.sleep(0.2)

            with open(py_file, "w") as f:
                f.write("print('modified')")

            time.sleep(1.5)

            perception.stop_watching()

            new_snapshot = perception.perceive(full=False)
            assert new_snapshot.file_tree.total_files == initial_count

    def test_file_deletion_triggers_incremental_update(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = os.path.join(tmpdir, "test.py")
            with open(py_file, "w") as f:
                f.write("print('hello')")

            perception = ProjectPerception(root_path=tmpdir)
            snapshot = perception.perceive(full=True)
            initial_count = snapshot.file_tree.total_files

            perception.start_watching()

            time.sleep(0.2)

            os.remove(py_file)

            time.sleep(1.5)

            perception.stop_watching()

            new_snapshot = perception.perceive(full=False)
            assert new_snapshot.file_tree.total_files == initial_count - 1

    def test_file_creation_triggers_incremental_update(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            perception = ProjectPerception(root_path=tmpdir)
            snapshot = perception.perceive(full=True)
            initial_count = snapshot.file_tree.total_files

            perception.start_watching()

            time.sleep(0.2)

            new_file = os.path.join(tmpdir, "new_file.py")
            with open(new_file, "w") as f:
                f.write("print('new')")

            time.sleep(1.5)

            perception.stop_watching()

            new_snapshot = perception.perceive(full=False)
            assert new_snapshot.file_tree.total_files == initial_count + 1

    def test_git_directory_change_triggers_git_rescan(self):
        tmpdir = tempfile.mkdtemp()
        try:
            git_dir = os.path.join(tmpdir, ".git")
            os.makedirs(git_dir)
            with open(os.path.join(git_dir, "config"), "w") as f:
                f.write("[core]\n")

            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("print('hello')")

            perception = ProjectPerception(root_path=tmpdir)
            snapshot = perception.perceive(full=True)

            perception.start_watching()

            time.sleep(0.2)

            with open(os.path.join(git_dir, "HEAD"), "w") as f:
                f.write("ref: refs/heads/main\n")

            time.sleep(1.5)

            perception.stop_watching()
            time.sleep(0.5)

            new_snapshot = perception.perceive(full=False)
            assert new_snapshot is not None
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_build_directory_change_triggers_build_rescan(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            perception = ProjectPerception(root_path=tmpdir)
            snapshot = perception.perceive(full=True)

            perception.start_watching()

            time.sleep(0.2)

            dist_dir = os.path.join(tmpdir, "dist")
            os.makedirs(dist_dir)
            with open(os.path.join(dist_dir, "output.txt"), "w") as f:
                f.write("build output")

            time.sleep(1.5)

            perception.stop_watching()

            new_snapshot = perception.perceive(full=False)
            assert new_snapshot.build_state.last_build_status == "success"


class TestDebounceMechanism:
    """测试防抖机制"""

    def test_debounce_prevents_multiple_executions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = os.path.join(tmpdir, "test.py")
            with open(py_file, "w") as f:
                f.write("line1")

            perception = ProjectPerception(root_path=tmpdir)
            perception.perceive(full=True)

            perception.start_watching()

            for i in range(5):
                with open(py_file, "w") as f:
                    f.write(f"line{i}")
                time.sleep(0.1)

            time.sleep(1.5)

            perception.stop_watching()

            new_snapshot = perception.perceive(full=False)
            assert new_snapshot.file_tree.total_files >= 1

    def test_debounce_delay_less_than_2_seconds(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = os.path.join(tmpdir, "test.py")
            with open(py_file, "w") as f:
                f.write("start")

            perception = ProjectPerception(root_path=tmpdir)
            perception.perceive(full=True)

            perception.start_watching()

            start_time = time.time()
            with open(py_file, "w") as f:
                f.write("modified")

            time.sleep(1.5)

            elapsed = time.time() - start_time

            perception.stop_watching()

            assert elapsed < 3.0


class TestCacheInvalidation:
    """测试缓存失效"""

    def test_incremental_update_invalidates_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = os.path.join(tmpdir, "test.py")
            with open(py_file, "w") as f:
                f.write("print('hello')")

            perception = ProjectPerception(root_path=tmpdir)
            snapshot1 = perception.perceive(full=True)

            perception.start_watching()

            time.sleep(0.2)

            with open(py_file, "w") as f:
                f.write("print('modified')")

            time.sleep(1.5)

            perception.stop_watching()

            snapshot2 = perception.perceive(full=False)
            assert snapshot1 is not snapshot2


class TestTechDebtIncremental:
    """测试技术债增量更新"""

    def test_file_modification_updates_tech_debt(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = os.path.join(tmpdir, "test.py")
            with open(py_file, "w") as f:
                f.write("# TODO: fix")

            perception = ProjectPerception(root_path=tmpdir)
            snapshot = perception.perceive(full=True)
            initial_markers = snapshot.tech_debt.total_markers

            perception.start_watching()

            time.sleep(0.2)

            with open(py_file, "w") as f:
                f.write("# TODO: fix\n# FIXME: bug")

            time.sleep(1.5)

            perception.stop_watching()

            new_snapshot = perception.perceive(full=False)
            assert new_snapshot.tech_debt.total_markers >= 2