# HOMEWORK TASK #1
## Multithreaded Text Processing with Log Collection (Python)

Student: Artsiom Yasiukou  
Teacher: Gintaras Dmitrijev  
Vilnius, 2026

---

## Table of Contents

1. Aims and objectives of the homework  
2. Work steps  
   2.1 Step 1: Preparing input data  
   2.2 Step 2: Parallel text processing  
   2.3 Step 3: Log production and collection  
   2.4 Step 4: Aggregation of final statistics  
   2.5 Step 5: Performance measurement  
3. Program run and results  
4. Conclusions

---

## 1. Aims and objectives of the homework

The aim of this homework is to design and implement a multithreaded text processing system in Python.  
The implemented solution must:

- process a large text file in parallel;
- compute global word statistics;
- generate and collect logs during processing;
- demonstrate safe synchronization between threads;
- compare single-thread and multithread execution time.

This work focuses on practical use of Python `threading`, shared communication via `queue.Queue`, and correct aggregation of distributed worker results.

## 2. Work steps

### 2.1 Step 1: Preparing input data

The program works with a text file that contains at least 10,000 lines, as required by the task.  
For easier testing and reproducibility, the script can automatically generate a sample file named `sample_text_12000.txt` with 12,000 lines by using the `--auto-generate-sample` flag.

### 2.2 Step 2: Parallel text processing

The input file is split into chunks by line count.  
Each chunk is assigned to a dedicated worker thread.  
Every worker:

- tokenizes words (case-insensitive),
- counts total words in its own chunk,
- builds local frequency statistics (`Counter`),
- detects empty lines and reports them to logging.

To avoid race conditions, workers store results in a shared list under synchronization (`threading.Lock`).

### 2.3 Step 3: Log production and collection

While processing, each worker generates log events such as:

- start of chunk processing;
- finish of chunk with execution time;
- number of processed words;
- warning about empty lines.

Each log entry includes:

- timestamp,
- worker ID,
- log level (`INFO`, `WARNING`, `ERROR`),
- message text.

Logs are sent to a shared thread-safe queue (`queue.Queue`).

A separate `LogCollector` thread continuously reads logs from the queue, updates counters for total logs and logs per level, and writes all log entries to `processing.log`.

### 2.4 Step 4: Aggregation of final statistics

After all worker threads complete:

- local counters are merged into one global counter;
- global total word count is calculated;
- unique word count is computed;
- top 20 most frequent words are extracted.

These values are printed in the final report section of the program output.

### 2.5 Step 5: Performance measurement

The same data is processed in two modes:

1. single-thread mode;
2. multi-thread mode.

The program measures:

- single-thread execution time;
- multi-thread execution time;
- speedup (`single / multi`);
- throughput (words per second in multi-thread mode).

This allows direct comparison of performance characteristics.

## 3. Program run and results

Program file: `hw1_variant2.py`

Example run command:

```bash
python3 hw1_variant2.py --auto-generate-sample
```

Produced files:

- `sample_text_12000.txt` (if not present),
- `processing.log`,
- console output with text statistics, log statistics, and performance values.

Example result (from execution):

- Total words: 143,844
- Unique words: 11
- Total logs generated: 24
- INFO: 18, WARNING: 6, ERROR: 0
- Single-thread time: 0.0244 s
- Multi-thread time: 0.0222 s
- Speedup: 1.10x
- Throughput: 6,470,594 words/sec

## 4. Conclusions

This homework successfully implements a multithreaded text processing pipeline using only Python standard library components.  
The solution demonstrates correct concurrent processing of file chunks, safe inter-thread communication through a queue, and centralized log collection in a dedicated collector thread.

The final output includes both text analytics and operational logging metrics, which together provide a complete overview of system behavior.  
Performance measurement between single-thread and multi-thread execution confirms the practical impact of parallel processing for this task.


# Attention 
This Markdown file is the original source of the document. The Word (.docx) version was generated from it using Pandoc utility. If any discrepancies occur, the content remains identical.