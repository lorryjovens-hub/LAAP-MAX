"""测试 ProjectPerception 文件树扫描器和技术债扫描器"""

import os
import tempfile
import time

import pytest

from laap.sandbox._types import FileTreeState, TechDebtReport
from laap.workspace.perception import ProjectPerception


class TestScanFiles:
    """测试 _scan_files() 方法"""

    def test_scan_files_returns_file_tree_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("print('hello')")
            perception = ProjectPerception(root_path=tmpdir)
            result = perception._scan_files()
            assert isinstance(result, FileTreeState)

    def test_scan_files_total_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(3):
                with open(os.path.join(tmpdir, f"test{i}.py"), "w") as f:
                    f.write(f"print('hello {i}')")
            perception = ProjectPerception(root_path=tmpdir)
            result = perception._scan_files()
            assert result.total_files == 3

    def test_scan_files_total_lines(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("line1\nline2\nline3\n")
            perception = ProjectPerception(root_path=tmpdir)
            result = perception._scan_files()
            assert result.total_lines >= 3

    def test_scan_files_language_python(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("print('hello')")
            perception = ProjectPerception(root_path=tmpdir)
            result = perception._scan_files()
            assert "python" in result.languages

    def test_scan_files_file_paths_not_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("print('hello')")
            perception = ProjectPerception(root_path=tmpdir)
            result = perception._scan_files()
            assert len(result.file_paths) > 0

    def test_scan_files_largest_files_top_10(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(15):
                with open(os.path.join(tmpdir, f"test{i}.py"), "w") as f:
                    f.write("x\n" * i)
            perception = ProjectPerception(root_path=tmpdir)
            result = perception._scan_files()
            assert len(result.largest_files) == 10
            assert all("path" in f for f in result.largest_files)
            assert all("lines" in f for f in result.largest_files)
            assert all("language" in f for f in result.largest_files)

    def test_scan_files_respects_gitignore(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = os.path.join(tmpdir, ".git")
            os.makedirs(git_dir)
            with open(os.path.join(git_dir, "config"), "w") as f:
                f.write("[core]\n")
            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("print('hello')")
            perception = ProjectPerception(root_path=tmpdir)
            result = perception._scan_files()
            git_paths = [p for p in result.file_paths if ".git" in p]
            assert len(git_paths) == 0

    def test_scan_files_module_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = os.path.join(tmpdir, "sub")
            os.makedirs(subdir)
            with open(os.path.join(subdir, "test.py"), "w") as f:
                f.write("print('hello')")
            perception = ProjectPerception(root_path=tmpdir)
            result = perception._scan_files()
            assert isinstance(result.module_structure, dict)
            assert "sub" in result.module_structure


class TestScanTechDebt:
    """测试 _scan_tech_debt() 方法"""

    def test_scan_tech_debt_returns_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("# TODO: fix me")
            perception = ProjectPerception(root_path=tmpdir)
            file_tree = perception._scan_files()
            result = perception._scan_tech_debt(file_tree)
            assert isinstance(result, TechDebtReport)

    def test_scan_tech_debt_total_markers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("# TODO: fix me")
            perception = ProjectPerception(root_path=tmpdir)
            file_tree = perception._scan_files()
            result = perception._scan_tech_debt(file_tree)
            assert result.total_markers >= 1

    def test_scan_tech_debt_by_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("# TODO: fix me")
            perception = ProjectPerception(root_path=tmpdir)
            file_tree = perception._scan_files()
            result = perception._scan_tech_debt(file_tree)
            assert isinstance(result.by_file, dict)
            assert "test.py" in result.by_file

    def test_scan_tech_debt_hotspots_top_10(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(15):
                with open(os.path.join(tmpdir, f"test{i}.py"), "w") as f:
                    f.write("# TODO: fix\n" * i)
            perception = ProjectPerception(root_path=tmpdir)
            file_tree = perception._scan_files()
            result = perception._scan_tech_debt(file_tree)
            assert len(result.hotspots) <= 10

    def test_scan_tech_debt_regex_matches(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = os.path.join(tmpdir, "test.py")
            with open(py_file, "w", encoding="utf-8") as f:
                f.write("""
# TODO: implement feature
# FIXME: fix bug
# XXX: temp code
# HACK: workaround
                """)

            perception = ProjectPerception(root_path=tmpdir)
            file_tree = perception._scan_files()
            result = perception._scan_tech_debt(file_tree)

            assert result.todo_count >= 2
            assert result.fixme_count >= 1
            assert result.xxx_count >= 1
            assert result.total_markers >= 4

    def test_scan_tech_debt_skips_non_code_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            md_file = os.path.join(tmpdir, "test.md")
            with open(md_file, "w", encoding="utf-8") as f:
                f.write("# TODO: this should not be counted")

            perception = ProjectPerception(root_path=tmpdir)
            file_tree = perception._scan_files()
            result = perception._scan_tech_debt(file_tree)

            assert result.total_markers == 0


class TestComplexityHotspots:
    """测试 _find_complexity_hotspots() 方法"""

    def test_find_complexity_hotspots_returns_sorted_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(5):
                with open(os.path.join(tmpdir, f"test{i}.py"), "w") as f:
                    f.write("x\n" * (i * 10) + "# TODO: fix\n" * i)
            perception = ProjectPerception(root_path=tmpdir)
            file_tree = perception._scan_files()
            tech_debt = perception._scan_tech_debt(file_tree)
            hotspots = perception._find_complexity_hotspots(file_tree, tech_debt)
            assert len(hotspots) <= 10
            for i in range(len(hotspots) - 1):
                assert hotspots[i]["score"] >= hotspots[i + 1]["score"]

    def test_find_complexity_hotspots_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("# TODO: fix")
            perception = ProjectPerception(root_path=tmpdir)
            file_tree = perception._scan_files()
            tech_debt = perception._scan_tech_debt(file_tree)
            hotspots = perception._find_complexity_hotspots(file_tree, tech_debt)
            if hotspots:
                hotspot = hotspots[0]
                assert "path" in hotspot
                assert "lines" in hotspot
                assert "todo_density" in hotspot
                assert "score" in hotspot


class TestPerceiveIntegration:
    """测试 perceive() 集成"""

    def test_perceive_full_scans_all(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("# TODO: fix\nprint('hello')")
            perception = ProjectPerception(root_path=tmpdir)
            snapshot = perception.perceive(full=True)
            assert snapshot.file_tree.total_files > 0
            assert snapshot.tech_debt.total_markers >= 1

    def test_perceive_returns_complete_snapshot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("print('hello')")
            perception = ProjectPerception(root_path=tmpdir)
            snapshot = perception.perceive(full=True)
            assert isinstance(snapshot.file_tree, FileTreeState)
            assert isinstance(snapshot.tech_debt, TechDebtReport)
            assert snapshot.root_path == os.path.abspath(tmpdir)

    def test_perceive_cache_works(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("print('hello')")
            perception = ProjectPerception(root_path=tmpdir)
            snapshot1 = perception.perceive(full=True)
            time.sleep(0.1)
            snapshot2 = perception.perceive(full=False)
            assert snapshot1 is snapshot2
            stats = perception.stats()
            assert stats["cache_hit_count"] >= 1
            assert stats["cache_miss_count"] >= 1


@pytest.mark.slow
class TestScanFilesRealProject:
    """使用真实项目的测试（标记为 slow）"""

    def test_real_project_scan(self):
        perception = ProjectPerception(root_path="d:\\LAAP")
        result = perception._scan_files()
        assert result.total_files > 0
        assert result.total_lines > 0
        assert "python" in result.languages

    def test_real_project_tech_debt(self):
        perception = ProjectPerception(root_path="d:\\LAAP")
        file_tree = perception._scan_files()
        result = perception._scan_tech_debt(file_tree)
        assert result.total_markers >= 0

    def test_real_project_perceive_full(self):
        perception = ProjectPerception(root_path="d:\\LAAP")
        snapshot = perception.perceive(full=True)
        assert snapshot.file_tree.total_files > 0
        assert snapshot.tech_debt.total_markers >= 0