"""
Traffic Analyzer - Reads server and client logs to generate a summary report.

OSI Layer Coverage:
  - Layer 7 (Application): Parses log files as application-layer data
  - Layer 4 (Transport): Analyzes TCP protocol stages and message timing
"""

import re
import os
from datetime import datetime
from collections import defaultdict

# Log file paths
SERVER_LOG = "server_log.txt"
CLIENT_LOG = "client_log.txt"
REPORT_FILE = "analysis_report.txt"


def parse_timestamp(line):
    """
    Extract timestamp from a log line.

    OSI Layer: Layer 7 (Application) - parses text-formatted log entries
    to extract structured timestamp data for analysis.
    """
    match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
    if match:
        return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
    return None


def parse_stage(line):
    """
    Extract TCP protocol stage tag from a log line.

    OSI Layer: Layer 4 (Transport) - identifies TCP connection stages
    (SYN, SYN-ACK, ACK, DATA, FIN) from logged entries.
    """
    match = re.search(r"\[(SYN|SYN-ACK|ACK|DATA|FIN)\]", line)
    if match:
        return match.group(1)
    return None


def parse_client_latency(line):
    """
    Extract latency value from a client log line.

    OSI Layer: Layer 4 (Transport) - extracts round-trip time measurements
    for analyzing network performance and message delivery timing.
    """
    match = re.search(r"latency: ([\d.]+) ms", line)
    if match:
        return float(match.group(1))
    return None


def parse_message_count(line):
    """
    Extract message number from a DATA stage log line.

    OSI Layer: Layer 7 (Application) - counts individual application messages
    exchanged during the TCP session for traffic analysis.
    """
    match = re.search(r"Message #(\d+)", line)
    if match:
        return int(match.group(1))
    return None


def analyze_log_file(filepath, source_name):
    """
    Analyze a single log file and extract metrics.

    OSI Layer: Layer 7 (Application) - reads and parses log files
    as application-layer data to extract meaningful traffic metrics.

    Returns:
        dict: Metrics including stages, message counts, and latencies
    """
    metrics = {
        "source": source_name,
        "stages": defaultdict(int),
        "message_count": 0,
        "latencies": [],
        "timestamps": [],
        "lines": []
    }

    if not os.path.exists(filepath):
        print(f"  [WARNING] {filepath} not found. Skipping {source_name} analysis.")
        return metrics

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            metrics["lines"].append(line)

            # Parse timestamp
            ts = parse_timestamp(line)
            if ts:
                metrics["timestamps"].append(ts)

            # Parse protocol stage
            stage = parse_stage(line)
            if stage:
                metrics["stages"][stage] += 1

            # Parse latency from client logs
            latency = parse_client_latency(line)
            if latency is not None:
                metrics["latencies"].append(latency)

            # Parse message count from server logs
            msg_num = parse_message_count(line)
            if msg_num is not None:
                metrics["message_count"] = max(metrics["message_count"], msg_num)

    return metrics


def calculate_average_latency(server_metrics, client_metrics):
    """
    Calculate average message latency from client-side measurements.

    OSI Layer: Layer 4 (Transport) - computes round-trip time averages
    to measure TCP connection performance and network responsiveness.
    """
    all_latencies = client_metrics["latencies"]
    if not all_latencies:
        return 0.0
    return sum(all_latencies) / len(all_latencies)


def calculate_total_duration(metrics):
    """
    Calculate the total duration of the session from timestamps.

    OSI Layer: Layer 4 (Transport) - measures the total time span
    of the TCP session from first to last logged event.
    """
    timestamps = metrics["timestamps"]
    if len(timestamps) < 2:
        return 0.0
    duration = (timestamps[-1] - timestamps[0]).total_seconds()
    return duration


def generate_report(server_metrics, client_metrics):
    """
    Generate a comprehensive analysis report from parsed logs.

    OSI Layer: Layer 7 (Application) - aggregates parsed data into
    a human-readable summary report for network traffic analysis.
    """
    # Combine stages from both logs
    combined_stages = defaultdict(int)
    for stage, count in server_metrics["stages"].items():
        combined_stages[stage] += count
    for stage, count in client_metrics["stages"].items():
        combined_stages[stage] += count

    # Calculate metrics
    total_connections = server_metrics["stages"].get("SYN", 0)
    total_messages = max(server_metrics["message_count"], client_metrics["message_count"])
    avg_latency = calculate_average_latency(server_metrics, client_metrics)

    # Use combined timestamps for total duration
    all_timestamps = sorted(server_metrics["timestamps"] + client_metrics["timestamps"])
    if len(all_timestamps) >= 2:
        total_duration = (all_timestamps[-1] - all_timestamps[0]).total_seconds()
    else:
        total_duration = 0.0

    # Build report
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("TCP Network Simulation - Traffic Analysis Report")
    report_lines.append("=" * 60)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    report_lines.append("--- Connection Summary ---")
    report_lines.append(f"Total connections made: {total_connections}")
    report_lines.append(f"Total messages exchanged: {total_messages}")
    report_lines.append(f"Session duration: {total_duration:.2f} seconds")
    report_lines.append("")

    report_lines.append("--- Latency Analysis ---")
    report_lines.append(f"Average latency per message: {avg_latency:.2f} ms")
    if client_metrics["latencies"]:
        report_lines.append(f"Min latency: {min(client_metrics['latencies']):.2f} ms")
        report_lines.append(f"Max latency: {max(client_metrics['latencies']):.2f} ms")
    report_lines.append("")

    report_lines.append("--- Protocol Stages Completed ---")
    for stage in ["SYN", "SYN-ACK", "ACK", "DATA", "FIN"]:
        count = combined_stages.get(stage, 0)
        report_lines.append(f"  {stage}: {count} occurrences")
    report_lines.append("")

    report_lines.append("--- Server Log Summary ---")
    for stage, count in sorted(server_metrics["stages"].items()):
        report_lines.append(f"  {stage}: {count}")
    report_lines.append(f"  Total log entries: {len(server_metrics['lines'])}")
    report_lines.append("")

    report_lines.append("--- Client Log Summary ---")
    for stage, count in sorted(client_metrics["stages"].items()):
        report_lines.append(f"  {stage}: {count}")
    report_lines.append(f"  Total log entries: {len(client_metrics['lines'])}")
    report_lines.append("")

    report_lines.append("=" * 60)
    report_lines.append("Analysis Complete")
    report_lines.append("=" * 60)

    return "\n".join(report_lines)


def main():
    """
    Main entry point: parse logs, generate report, and display results.

    OSI Layer: Layer 7 (Application) - orchestrates the analysis pipeline
    from log ingestion through report generation and output.
    """
    print("=" * 60)
    print("TCP Network Simulator - Traffic Analyzer")
    print("=" * 60)

    # Check if log files exist
    server_exists = os.path.exists(SERVER_LOG)
    client_exists = os.path.exists(CLIENT_LOG)

    if not server_exists and not client_exists:
        print("No log files found. Please run server.py and client.py first.")
        print(f"Expected: {SERVER_LOG} and {CLIENT_LOG}")
        return

    print(f"\nAnalyzing {SERVER_LOG}...")
    server_metrics = analyze_log_file(SERVER_LOG, "Server")

    print(f"Analyzing {CLIENT_LOG}...")
    client_metrics = analyze_log_file(CLIENT_LOG, "Client")

    # Generate report
    print("\nGenerating analysis report...")
    report = generate_report(server_metrics, client_metrics)

    # Save report to file
    with open(REPORT_FILE, "w") as f:
        f.write(report)

    # Print report to console
    print("\n" + report)
    print(f"\nReport saved to {REPORT_FILE}")


if __name__ == "__main__":
    main()
