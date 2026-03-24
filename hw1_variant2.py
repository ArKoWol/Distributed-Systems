#!/usr/bin/env python3
"""
Distributed Systems Homework #1 (Variant 2)
Multithreaded Text Processing with Log Collection (Python).
"""

from __future__ import annotations

import argparse
import queue
import re
import threading
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


WORD_RE = re.compile(r"[A-Za-z0-9']+")
SENTINEL = object()


@dataclass
class ProcessingResult:
    total_words: int
    word_counter: Counter[str]


class LogCollector(threading.Thread):
    def __init__(self, log_queue: "queue.Queue[object]", output_file: Optional[Path] = None) -> None:
        super().__init__(daemon=True)
        self.log_queue = log_queue
        self.output_file = output_file
        self.total_logs = 0
        self.level_counts = Counter()

    def run(self) -> None:
        log_stream = None
        try:
            if self.output_file is not None:
                self.output_file.parent.mkdir(parents=True, exist_ok=True)
                log_stream = self.output_file.open("w", encoding="utf-8")

            while True:
                item = self.log_queue.get()
                try:
                    if item is SENTINEL:
                        return
                    timestamp, worker_id, level, message = item  # type: ignore[misc]
                    self.total_logs += 1
                    self.level_counts[level] += 1
                    if log_stream is not None:
                        log_stream.write(f"[{timestamp}] [Worker {worker_id}] [{level}] {message}\n")
                finally:
                    self.log_queue.task_done()
        finally:
            if log_stream is not None:
                log_stream.close()


def now_timestamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def log_message(
    log_queue: "queue.Queue[object]",
    worker_id: int,
    level: str,
    message: str,
) -> None:
    log_queue.put((now_timestamp(), worker_id, level, message))


def tokenize(lines: Iterable[str]) -> list[str]:
    words: list[str] = []
    for line in lines:
        words.extend(WORD_RE.findall(line.lower()))
    return words


def split_chunks(lines: list[str], chunk_count: int) -> list[list[str]]:
    n = len(lines)
    if chunk_count <= 0:
        raise ValueError("chunk_count must be > 0")
    if n == 0:
        return [[]]
    chunk_count = min(chunk_count, n)
    base = n // chunk_count
    extra = n % chunk_count
    chunks: list[list[str]] = []
    start = 0
    for i in range(chunk_count):
        size = base + (1 if i < extra else 0)
        end = start + size
        chunks.append(lines[start:end])
        start = end
    return chunks


def process_chunk(
    worker_id: int,
    chunk_lines: list[str],
    results: list[Optional[ProcessingResult]],
    index: int,
    lock: threading.Lock,
    log_queue: "queue.Queue[object]",
) -> None:
    start = time.perf_counter()
    log_message(log_queue, worker_id, "INFO", "started processing chunk")

    empty_lines = 0
    words = []
    for line in chunk_lines:
        if not line.strip():
            empty_lines += 1
        words.extend(WORD_RE.findall(line.lower()))

    word_counter = Counter(words)
    total_words = len(words)
    elapsed = time.perf_counter() - start

    if empty_lines > 0:
        log_message(log_queue, worker_id, "WARNING", f"encountered {empty_lines} empty lines")
    if total_words == 0:
        log_message(log_queue, worker_id, "ERROR", "processed 0 words in chunk")
    else:
        log_message(log_queue, worker_id, "INFO", f"processed {total_words} words")

    with lock:
        results[index] = ProcessingResult(total_words=total_words, word_counter=word_counter)

    log_message(log_queue, worker_id, "INFO", f"finished chunk in {elapsed:.4f} seconds")


def process_single_thread(lines: list[str]) -> tuple[ProcessingResult, float]:
    start = time.perf_counter()
    words = tokenize(lines)
    result = ProcessingResult(total_words=len(words), word_counter=Counter(words))
    elapsed = time.perf_counter() - start
    return result, elapsed


def process_multi_thread(
    lines: list[str],
    workers: int,
    log_queue: "queue.Queue[object]",
) -> tuple[ProcessingResult, float]:
    chunks = split_chunks(lines, workers)
    lock = threading.Lock()
    results: list[Optional[ProcessingResult]] = [None] * len(chunks)
    threads: list[threading.Thread] = []

    start = time.perf_counter()
    for idx, chunk in enumerate(chunks):
        worker_id = idx + 1
        thread = threading.Thread(
            target=process_chunk,
            args=(worker_id, chunk, results, idx, lock, log_queue),
            daemon=False,
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
    elapsed = time.perf_counter() - start

    merged_counter: Counter[str] = Counter()
    total_words = 0
    for result in results:
        if result is None:
            continue
        total_words += result.total_words
        merged_counter.update(result.word_counter)

    return ProcessingResult(total_words=total_words, word_counter=merged_counter), elapsed


def format_top_words(counter: Counter[str], limit: int = 20) -> list[tuple[str, int]]:
    return counter.most_common(limit)


def generate_sample_text(path: Path, lines_count: int = 12000) -> None:
    tokens = [
        "distributed", "systems", "thread", "queue", "log", "worker",
        "python", "synchronization", "parallel", "processing", "homework",
    ]
    with path.open("w", encoding="utf-8") as f:
        for i in range(lines_count):
            # Insert some empty lines to trigger warning logs.
            if i % 997 == 0:
                f.write("\n")
                continue
            line_words = [tokens[(i + j) % len(tokens)] for j in range(12)]
            f.write(" ".join(line_words) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Homework #1 - Variant 2")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("sample_text_12000.txt"),
        help="Path to input text file (>= 10000 lines recommended).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=6,
        help="Number of worker threads.",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=Path("processing.log"),
        help="Path for collected logs.",
    )
    parser.add_argument(
        "--auto-generate-sample",
        action="store_true",
        help="Generate a 12000-line sample file if input does not exist.",
    )
    args = parser.parse_args()

    if not args.input.exists():
        if args.auto_generate_sample:
            generate_sample_text(args.input, lines_count=12000)
        else:
            raise FileNotFoundError(
                f"Input file not found: {args.input}. "
                "Provide --auto-generate-sample or choose another file."
            )

    with args.input.open("r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    if len(lines) < 10_000:
        print(f"WARNING: file has {len(lines)} lines (requirement is >= 10000 lines).")

    log_queue: "queue.Queue[object]" = queue.Queue()
    collector = LogCollector(log_queue=log_queue, output_file=args.log_file)
    collector.start()

    single_result, single_time = process_single_thread(lines)
    multi_result, multi_time = process_multi_thread(lines, args.workers, log_queue)

    log_queue.put(SENTINEL)
    log_queue.join()
    collector.join()

    print("TEXT STATISTICS")
    print("---------------")
    print(f"Total words: {multi_result.total_words:,}")
    print(f"Unique words: {len(multi_result.word_counter):,}")
    print("Top 20 words:")
    for idx, (word, count) in enumerate(format_top_words(multi_result.word_counter), start=1):
        print(f"{idx:2d}. {word:<20} {count:,}")

    print()
    print("LOG STATISTICS")
    print("--------------")
    print(f"Total logs generated: {collector.total_logs:,}")
    for level in ("INFO", "WARNING", "ERROR"):
        print(f"{level}: {collector.level_counts[level]:,}")

    throughput = multi_result.total_words / multi_time if multi_time > 0 else 0.0
    speedup = single_time / multi_time if multi_time > 0 else 0.0
    print()
    print("PERFORMANCE")
    print("-----------")
    print(f"Single-thread time: {single_time:.4f} seconds")
    print(f"Multi-thread time : {multi_time:.4f} seconds")
    print(f"Speedup           : {speedup:.2f}x")
    print(f"Throughput        : {throughput:,.0f} words/sec")


if __name__ == "__main__":
    main()
