import unittest
import os
import json
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analyzer import (
    parse_timestamp,
    parse_stage,
    parse_client_latency,
    parse_message_count,
    analyze_log_file,
    generate_report,
    generate_json_report,
)


class TestParseTimestamp(unittest.TestCase):
    def test_valid_timestamp(self):
        line = "2026-05-05 21:30:05 - [SYN] Connection received"
        ts = parse_timestamp(line)
        self.assertIsNotNone(ts)
        self.assertEqual(ts.year, 2026)
        self.assertEqual(ts.month, 5)
        self.assertEqual(ts.day, 5)
        self.assertEqual(ts.hour, 21)
        self.assertEqual(ts.minute, 30)
        self.assertEqual(ts.second, 5)

    def test_no_timestamp(self):
        line = "no timestamp here"
        self.assertIsNone(parse_timestamp(line))

    def test_partial_timestamp(self):
        line = "2026-05-05 - [SYN] missing time"
        self.assertIsNone(parse_timestamp(line))


class TestParseStage(unittest.TestCase):
    def test_syn(self):
        self.assertEqual(parse_stage("[SYN] Connection received"), "SYN")

    def test_syn_ack(self):
        self.assertEqual(parse_stage("[SYN-ACK] Response sent"), "SYN-ACK")

    def test_ack(self):
        self.assertEqual(parse_stage("[ACK] Handshake complete"), "ACK")

    def test_data(self):
        self.assertEqual(parse_stage("[DATA] Message #1: 'hello'"), "DATA")

    def test_fin(self):
        self.assertEqual(parse_stage("[FIN] Closing connection"), "FIN")

    def test_no_stage(self):
        self.assertIsNone(parse_stage("no stage here"))

    def test_stage_in_middle(self):
        self.assertEqual(parse_stage("2026-05-05 - [DATA] some log"), "DATA")


class TestParseClientLatency(unittest.TestCase):
    def test_valid_latency(self):
        line = "Message #1 latency: 1.23 ms"
        self.assertAlmostEqual(parse_client_latency(line), 1.23)

    def test_no_latency(self):
        self.assertIsNone(parse_client_latency("no latency info"))

    def test_zero_latency(self):
        line = "Message #1 latency: 0.00 ms"
        self.assertAlmostEqual(parse_client_latency(line), 0.0)


class TestParseMessageCount(unittest.TestCase):
    def test_valid_count(self):
        line = "Message #5: 'hello'"
        self.assertEqual(parse_message_count(line), 5)

    def test_no_count(self):
        self.assertIsNone(parse_message_count("Total messages received: 5"))

    def test_total_line(self):
        line = "Total messages received: 5"
        self.assertIsNone(parse_message_count(line))


class TestAnalyzeLogFile(unittest.TestCase):
    def test_missing_file(self):
        metrics = analyze_log_file("nonexistent.txt", "Test")
        self.assertEqual(metrics["source"], "Test")
        self.assertEqual(len(metrics["lines"]), 0)

    def test_parses_server_log(self):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
        tmp.write("2026-05-05 21:30:00 - [SYN] Server started\n")
        tmp.write("2026-05-05 21:30:05 - [DATA] Message #1: 'hello'\n")
        tmp.write("2026-05-05 21:30:08 - [FIN] Connection closed\n")
        tmp.close()
        metrics = analyze_log_file(tmp.name, "Server")
        os.unlink(tmp.name)

        self.assertEqual(metrics["stages"]["SYN"], 1)
        self.assertEqual(metrics["stages"]["DATA"], 1)
        self.assertEqual(metrics["stages"]["FIN"], 1)
        self.assertEqual(metrics["message_count"], 1)
        self.assertEqual(len(metrics["timestamps"]), 3)

    def test_parses_client_log(self):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
        tmp.write("2026-05-05 21:30:05 - Message #1 latency: 1.23 ms\n")
        tmp.write("2026-05-05 21:30:06 - Message #2 latency: 0.52 ms\n")
        tmp.close()
        metrics = analyze_log_file(tmp.name, "Client")
        os.unlink(tmp.name)

        self.assertEqual(len(metrics["latencies"]), 2)
        self.assertAlmostEqual(metrics["latencies"][0], 1.23)
        self.assertAlmostEqual(metrics["latencies"][1], 0.52)


class TestGenerateReport(unittest.TestCase):
    def setUp(self):
        self.server_metrics = {
            "source": "Server",
            "stages": {"SYN": 1, "SYN-ACK": 1, "ACK": 1, "DATA": 5, "FIN": 2},
            "message_count": 5,
            "latencies": [],
            "timestamps": [],
            "lines": ["line1", "line2", "line3"],
        }
        self.client_metrics = {
            "source": "Client",
            "stages": {"SYN": 1, "SYN-ACK": 1, "ACK": 1, "DATA": 5, "FIN": 2},
            "message_count": 5,
            "latencies": [1.0, 2.0, 3.0],
            "timestamps": [],
            "lines": ["line1", "line2"],
        }

    def test_text_report_contains_sections(self):
        report = generate_report(self.server_metrics, self.client_metrics)
        self.assertIn("Connection Summary", report)
        self.assertIn("Latency Analysis", report)
        self.assertIn("Protocol Stages Completed", report)
        self.assertIn("Average latency per message: 2.00 ms", report)
        self.assertIn("Min latency: 1.00 ms", report)
        self.assertIn("Max latency: 3.00 ms", report)

    def test_json_report_structure(self):
        data = generate_json_report(self.server_metrics, self.client_metrics)
        self.assertIn("connection_summary", data)
        self.assertIn("latency_analysis", data)
        self.assertIn("protocol_stages", data)
        self.assertEqual(data["connection_summary"]["total_connections"], 1)
        self.assertEqual(data["connection_summary"]["total_messages"], 5)
        self.assertAlmostEqual(data["latency_analysis"]["average_ms"], 2.0)

    def test_json_report_serializable(self):
        data = generate_json_report(self.server_metrics, self.client_metrics)
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["connection_summary"]["total_messages"], 5)

    def test_empty_latencies(self):
        empty_client = {**self.client_metrics, "latencies": []}
        data = generate_json_report(self.server_metrics, empty_client)
        self.assertIsNone(data["latency_analysis"]["min_ms"])
        self.assertIsNone(data["latency_analysis"]["max_ms"])


if __name__ == "__main__":
    unittest.main()
