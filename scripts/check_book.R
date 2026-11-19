chapter_files <- sprintf("%02d-%s.Rmd", 1:19, c(
  "introduction", "candle", "single-candle", "two-candle", "multi-candle",
  "gap-continuation", "doji-failure", "pattern-dictionary", "pattern-scoring", "trend", "percentage", "ma",
  "rsi", "obv", "waves", "profile", "option", "hedging", "comprehensive"
))

required_headings <- c(
  "## 问题现场", "## 学习目标", "## 经典形态与市场机制",
  "## 可计算定义", "## 研究设计", "## R实现", "## Python实现",
  "## 图形诊断", "## 证据与稳健性", "## AI协作实验室",
  "## 失效条件与常见误区", "## 本章小结与练习"
)

stopifnot(all(file.exists(chapter_files)))
for (path in chapter_files) {
  lines <- readLines(path, encoding = "UTF-8", warn = FALSE)
  positions <- match(required_headings, lines)
  if (anyNA(positions)) {
    stop(path, " missing: ", paste(required_headings[is.na(positions)], collapse = ", "))
  }
  if (is.unsorted(positions)) stop(path, " headings are out of order")
}

all_lines <- unlist(lapply(list.files(pattern = "\\.Rmd$"), readLines, warn = FALSE))
labels <- sub("^```\\{r[[:space:]]*([^,}]*).*$", "\\1", grep("^```\\{r", all_lines, value = TRUE))
labels <- labels[nzchar(labels)]
if (anyDuplicated(labels)) stop("Duplicated R chunk label: ", labels[duplicated(labels)][1])

source("R/candlestick_lab.R")
chapters <- c(
  "intro", "candle", "single", "two", "multi", "gap",
  "doji", "dictionary", "scoring", "trend", "percentage", "ma", "rsi", "obv",
  "waves", "profile", "option", "hedging", "comprehensive"
)
for (chapter in chapters) {
  signal <- lab_chapter_signal(chapter)
  stopifnot(length(signal) == nrow(lab_read_data()), all(signal %in% -1:1))
}

cat("PASS: 19 chapters, heading order, chunk labels, data, and signals\n")
