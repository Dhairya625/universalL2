import unittest
import tempfile
from pathlib import Path
from automate_core import scan_repository

class TestCoverage(unittest.TestCase):
    def test_coverage_parsing_xml(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "test.py").write_text("def ok():\n  pass\n")

            coverage_xml = """<?xml version="1.0" ?>
            <coverage branch-rate="0" branches-covered="0" branches-valid="0" complexity="0" line-rate="0.5" lines-covered="1" lines-valid="2" timestamp="1708453303790" version="7.4.3">
                <packages>
                    <package name="." line-rate="0.5" branch-rate="0" complexity="0">
                        <classes>
                            <class name="test.py" filename="test.py" complexity="0" line-rate="0.4" branch-rate="0">
                                <lines>
                                    <line number="1" hits="1"/>
                                    <line number="2" hits="0"/>
                                </lines>
                            </class>
                        </classes>
                    </package>
                </packages>
            </coverage>"""
            (root / "coverage.xml").write_text(coverage_xml)

            report = scan_repository(root)
            test_gaps = [f for f in report.findings if f.title == "Low test coverage detected"]
            self.assertEqual(len(test_gaps), 1)
            self.assertEqual(test_gaps[0].evidence[0].path, "test.py")
