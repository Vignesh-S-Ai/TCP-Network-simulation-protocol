import unittest
import subprocess
import time
import os
import signal
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_SCRIPT = os.path.join(PROJECT_DIR, "server.py")
CLIENT_SCRIPT = os.path.join(PROJECT_DIR, "client.py")
ANALYZER_SCRIPT = os.path.join(PROJECT_DIR, "analyzer.py")
TOPOLOGY_SCRIPT = os.path.join(PROJECT_DIR, "topology.py")

TEST_HOST = "127.0.0.1"
TEST_PORT = 5001


def find_python():
    return sys.executable


class TestServerClientIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server_proc = subprocess.Popen(
            [find_python(), SERVER_SCRIPT, "--host", TEST_HOST, "--port", str(TEST_PORT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        if cls.server_proc.poll() is None:
            cls.server_proc.terminate()
            try:
                cls.server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls.server_proc.kill()

    def test_client_connects_and_sends_messages(self):
        result = subprocess.run(
            [find_python(), CLIENT_SCRIPT, "--host", TEST_HOST, "--port", str(TEST_PORT), "--messages", "3"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Messages sent: 3", result.stdout)
        self.assertIn("Messages received: 3", result.stdout)
        self.assertIn("Average latency:", result.stdout)

    def test_client_custom_delay(self):
        result = subprocess.run(
            [find_python(), CLIENT_SCRIPT, "--host", TEST_HOST, "--port", str(TEST_PORT), "--messages", "2", "--delay", "0.1"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Messages sent: 2", result.stdout)

    def test_client_refused_connection(self):
        result = subprocess.run(
            [find_python(), CLIENT_SCRIPT, "--host", "127.0.0.1", "--port", "59999", "--messages", "1"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout + result.stderr
        self.assertIn("Connection refused", output)


class TestAnalyzerIntegration(unittest.TestCase):
    def test_analyzer_with_existing_logs(self):
        result = subprocess.run(
            [find_python(), CLIENT_SCRIPT, "--host", TEST_HOST, "--port", str(TEST_PORT)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            self.skipTest("Client failed to run; analyzer test skipped")

        result = subprocess.run(
            [find_python(), ANALYZER_SCRIPT],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Connection Summary", result.stdout)
        self.assertIn("Latency Analysis", result.stdout)
        self.assertTrue(os.path.exists(os.path.join(PROJECT_DIR, "analysis_report.txt")))

    def test_analyzer_json_output(self):
        result = subprocess.run(
            [find_python(), ANALYZER_SCRIPT, "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('"connection_summary"', result.stdout)
        self.assertIn('"latency_analysis"', result.stdout)

    def test_analyzer_no_logs_warning(self):
        result = subprocess.run(
            [find_python(), ANALYZER_SCRIPT, "--server-log", "no_server.log", "--client-log", "no_client.log"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertIn("No log files found", result.stdout)


class TestTopologyIntegration(unittest.TestCase):
    def test_topology_runs_successfully(self):
        result = subprocess.run(
            [find_python(), TOPOLOGY_SCRIPT],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Simulation Complete", result.stdout)
        self.assertIn("DELIVERED", result.stdout)


if __name__ == "__main__":
    unittest.main()
