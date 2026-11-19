.lab_cache <- new.env(parent = emptyenv())

lab_lead <- function(x, n = 1L) {
  stopifnot(n >= 0L)
  if (n == 0L) return(x)
  c(x[-seq_len(n)], rep(NA, n))
}

lab_lag <- function(x, n = 1L) {
  stopifnot(n >= 0L)
  if (n == 0L) return(x)
  c(rep(NA, n), x[seq_len(length(x) - n)])
}

lab_roll <- function(x, n, fun) {
  stopifnot(n >= 1L)
  out <- rep(NA_real_, length(x))
  if (length(x) < n) return(out)
  for (i in seq.int(n, length(x))) {
    out[i] <- fun(x[seq.int(i - n + 1L, i)], na.rm = TRUE)
  }
  out
}

lab_read_data <- function(path = "data/aapl_daily.csv.gz") {
  key <- paste0("data::", normalizePath(path, mustWork = TRUE))
  if (exists(key, envir = .lab_cache, inherits = FALSE)) {
    return(get(key, envir = .lab_cache, inherits = FALSE))
  }

  data <- utils::read.csv(path, stringsAsFactors = FALSE)
  required <- c("date", "code", "open", "high", "low", "close", "volume")
  missing <- setdiff(required, names(data))
  if (length(missing)) stop("Missing columns: ", paste(missing, collapse = ", "))
  data$date <- as.Date(data$date)
  data <- data[order(data$code, data$date), , drop = FALSE]
  if (anyDuplicated(data[c("code", "date")])) stop("Duplicated code-date key")
  if (any(data$high < pmax(data$open, data$close, data$low), na.rm = TRUE) ||
      any(data$low > pmin(data$open, data$close, data$high), na.rm = TRUE)) {
    stop("Invalid OHLC relationship")
  }
  rownames(data) <- NULL
  assign(key, data, envir = .lab_cache)
  data
}

lab_xts <- function(data = lab_read_data()) {
  key <- "ohlc_xts"
  if (exists(key, envir = .lab_cache, inherits = FALSE)) {
    return(get(key, envir = .lab_cache, inherits = FALSE))
  }
  values <- as.matrix(data[c("open", "high", "low", "close", "volume", "close")])
  colnames(values) <- paste0(
    data$code[1], ".", c("Open", "High", "Low", "Close", "Volume", "Adjusted")
  )
  out <- xts::xts(values, order.by = data$date)
  assign(key, out, envir = .lab_cache)
  out
}

lab_features <- function(data = lab_read_data()) {
  key <- "features"
  if (exists(key, envir = .lab_cache, inherits = FALSE)) {
    return(get(key, envir = .lab_cache, inherits = FALSE))
  }

  out <- data
  candle_range <- pmax(out$high - out$low, .Machine$double.eps)
  body_high <- pmax(out$open, out$close)
  body_low <- pmin(out$open, out$close)
  out$body_ratio <- abs(out$close - out$open) / candle_range
  out$upper_ratio <- (out$high - body_high) / candle_range
  out$lower_ratio <- (body_low - out$low) / candle_range
  out$ret_1 <- out$close / lab_lag(out$close) - 1
  out$ret_5 <- out$close / lab_lag(out$close, 5) - 1
  out$sma_20 <- lab_roll(out$close, 20, mean)
  out$sma_50 <- lab_roll(out$close, 50, mean)
  delta <- c(NA_real_, diff(out$close))
  gain <- pmax(delta, 0, na.rm = FALSE)
  loss <- pmax(-delta, 0, na.rm = FALSE)
  avg_gain <- lab_roll(gain, 14, mean)
  avg_loss <- lab_roll(loss, 14, mean)
  rs <- avg_gain / pmax(avg_loss, .Machine$double.eps)
  out$rsi_14 <- 100 - 100 / (1 + rs)
  signed_volume <- sign(delta) * out$volume
  signed_volume[is.na(signed_volume)] <- 0
  out$obv <- cumsum(signed_volume)
  out$obv_slope_10 <- out$obv - lab_lag(out$obv, 10)
  out$high_60 <- lab_roll(out$high, 60, max)
  out$low_60 <- lab_roll(out$low, 60, min)
  out$range_position_60 <- (out$close - out$low_60) /
    pmax(out$high_60 - out$low_60, .Machine$double.eps)
  out$rv_20 <- sqrt(252) * lab_roll(out$ret_1, 20, stats::sd)
  true_range <- pmax(
    out$high - out$low,
    abs(out$high - lab_lag(out$close)),
    abs(out$low - lab_lag(out$close)),
    na.rm = TRUE
  )
  out$atr_14 <- lab_roll(true_range, 14, mean)
  out$drawdown_60 <- out$close / out$high_60 - 1
  out$volume_node_120 <- NA_real_
  if (nrow(out) >= 120L) {
    typical <- (out$high + out$low + out$close) / 3
    for (i in seq.int(120L, nrow(out))) {
      rows <- seq.int(i - 119L, i)
      lower <- min(out$low[rows], na.rm = TRUE)
      upper <- max(out$high[rows], na.rm = TRUE)
      if (!is.finite(lower) || !is.finite(upper) || upper <= lower) next
      breaks <- seq(lower, upper, length.out = 11L)
      bin <- cut(typical[rows], breaks = breaks, include.lowest = TRUE, labels = FALSE)
      volume_by_bin <- tapply(out$volume[rows], bin, sum, na.rm = TRUE)
      best <- as.integer(names(volume_by_bin)[which.max(volume_by_bin)])
      out$volume_node_120[i] <- mean(breaks[c(best, best + 1L)])
    }
  }
  assign(key, out, envir = .lab_cache)
  out
}

lab_pattern <- function(function_name) {
  key <- paste0("pattern::", function_name)
  if (exists(key, envir = .lab_cache, inherits = FALSE)) {
    return(get(key, envir = .lab_cache, inherits = FALSE))
  }
  detector <- getExportedValue("eCandleSticks", function_name)
  value <- detector(lab_xts())
  out <- as.data.frame(as.matrix(value))
  out[] <- lapply(out, function(x) !is.na(x) & as.logical(x))
  assign(key, out, envir = .lab_cache)
  out
}

lab_column <- function(pattern, column) {
  value <- lab_pattern(pattern)
  if (!column %in% names(value)) {
    stop("Pattern column not found: ", pattern, "::", column)
  }
  value[[column]]
}

lab_pair <- function(pattern, bull, bear) {
  as.integer(lab_column(pattern, bull)) - as.integer(lab_column(pattern, bear))
}

lab_merge_signals <- function(...) {
  signals <- list(...)
  score <- Reduce(`+`, signals)
  as.integer(sign(score))
}

lab_base_signals <- function() {
  key <- "base_signals"
  if (exists(key, envir = .lab_cache, inherits = FALSE)) {
    return(get(key, envir = .lab_cache, inherits = FALSE))
  }
  f <- lab_features()
  doji <- lab_column("add_csp_doji", "Doji")
  doji_direction <- ifelse(doji, -sign(f$ret_5), 0)
  doji_direction[!is.finite(doji_direction)] <- 0
  out <- list(
    hammer = as.integer(lab_column("add_csp_hammer", "Hammer")),
    shooting = -as.integer(lab_column("add_csp_shooting_star", "ShootingStar")),
    inverted = as.integer(lab_column("add_csp_inverted_hammer", "InvertedHammer")),
    engulfing = lab_pair("add_csp_engulfing", "Bull.Engulfing", "Bear.Engulfing"),
    star = lab_pair("add_csp_star", "MorningStar", "EveningStar"),
    harami = lab_pair("add_csp_harami", "Bull.Harami", "Bear.Harami"),
    counter = lab_pair("add_csp_counter_attack", "BullCounterAttack", "BearCounterAttack"),
    methods = lab_pair("add_csp_three_methods", "RisingThreeMethods", "FallingThreeMethods"),
    separating = lab_pair("add_csp_separating_lines", "BullSeparatingLines", "BearSeparatingLines"),
    tasuki = lab_pair("add_csp_tasuki_gap", "UpsideTasukiGap", "DownsideTasukiGap"),
    doji = as.integer(doji_direction),
    gap = lab_pair("add_csp_gap", "GapUp", "GapDown")
  )
  assign(key, out, envir = .lab_cache)
  out
}

lab_chapter_signal <- function(chapter) {
  key <- paste0("chapter::", chapter)
  if (exists(key, envir = .lab_cache, inherits = FALSE)) {
    return(get(key, envir = .lab_cache, inherits = FALSE))
  }
  f <- lab_features()
  s <- lab_base_signals()
  n <- nrow(f)

  signal <- switch(
    chapter,
    intro = s$engulfing,
    candle = s$doji,
    single = lab_merge_signals(s$hammer, s$shooting, s$inverted),
    two = lab_merge_signals(s$engulfing, s$harami, s$counter),
    multi = lab_merge_signals(s$star, s$methods),
    gap = lab_merge_signals(s$gap, s$methods, s$separating, s$tasuki),
    doji = s$doji,
    dictionary = {
      score <- s$hammer + s$shooting + s$engulfing + s$star + s$harami + s$methods
      ifelse(abs(score) >= 1, sign(score), 0)
    },
    scoring = {
      mat <- do.call(cbind, s[c("hammer", "shooting", "engulfing", "star", "harami", "counter", "doji")])
      score <- rowSums(mat)
      hits <- rowSums(mat != 0)
      ifelse(hits >= 2 & score != 0, sign(score), 0)
    },
    trend = {
      raw <- lab_merge_signals(s$hammer, s$shooting, s$engulfing)
      ifelse((raw > 0 & f$close < f$sma_20) | (raw < 0 & f$close > f$sma_20), raw, 0)
    },
    percentage = {
      near_level <- pmin(abs(f$range_position_60 - 0.382),
                         abs(f$range_position_60 - 0.5),
                         abs(f$range_position_60 - 0.618)) <= 0.04
      raw <- lab_merge_signals(s$hammer, s$shooting, s$engulfing)
      ifelse(near_level, raw, 0)
    },
    ma = {
      near_ma <- abs(f$close / f$sma_20 - 1) <= 0.015 |
        abs(f$close / f$sma_50 - 1) <= 0.015
      ifelse(near_ma, s$engulfing, 0)
    },
    rsi = ifelse((s$hammer > 0 & f$rsi_14 < 35), 1,
                 ifelse(s$shooting < 0 & f$rsi_14 > 65, -1, 0)),
    obv = ifelse(s$engulfing != 0 & sign(f$obv_slope_10) == s$engulfing, s$engulfing, 0),
    waves = ifelse(s$hammer > 0 & f$range_position_60 < 0.15, 1,
                   ifelse(s$shooting < 0 & f$range_position_60 > 0.85, -1, 0)),
    profile = {
      near_node <- abs(f$close - f$volume_node_120) <= f$atr_14
      ifelse(near_node, s$engulfing, 0)
    },
    option = {
      high_vol <- f$rv_20 >= stats::median(f$rv_20, na.rm = TRUE)
      ifelse(high_vol, lab_merge_signals(s$star, s$engulfing), 0)
    },
    hedging = {
      risk <- f$drawdown_60 < -0.08 | f$rv_20 > stats::quantile(f$rv_20, 0.75, na.rm = TRUE)
      ifelse(risk & lab_merge_signals(s$shooting, s$engulfing) < 0, -1, 0)
    },
    comprehensive = {
      trend_score <- sign(f$close - f$sma_50)
      momentum_score <- ifelse(f$rsi_14 < 35, 1, ifelse(f$rsi_14 > 65, -1, 0))
      price_score <- s$hammer + s$shooting + s$engulfing + s$star + s$harami
      score <- price_score + trend_score + momentum_score
      ifelse(abs(score) >= 2 & price_score != 0, sign(score), 0)
    },
    stop("Unknown chapter signal: ", chapter)
  )
  signal <- as.integer(signal)
  signal[!is.finite(signal)] <- 0L
  stopifnot(length(signal) == n, all(signal %in% -1:1))
  assign(key, signal, envir = .lab_cache)
  signal
}

lab_event_returns <- function(signal, horizon = 5L, cost_bps = 10,
                              nonoverlap = FALSE) {
  data <- lab_read_data()
  stopifnot(length(signal) == nrow(data), horizon >= 1L)
  event <- signal != 0L
  if (nonoverlap) {
    keep <- rep(FALSE, length(event))
    next_allowed <- 1L
    for (i in which(event)) {
      if (i >= next_allowed) {
        keep[i] <- TRUE
        next_allowed <- i + horizon + 1L
      }
    }
    event <- keep
  }
  entry <- lab_lead(data$open, 1L)
  exit <- lab_lead(data$open, horizon + 1L)
  gross <- signal * (exit / entry - 1)
  net <- gross - ifelse(event, cost_bps / 10000, 0)
  data.frame(
    date = data$date,
    signal = signal,
    event = event,
    gross_return = ifelse(event, gross, NA_real_),
    net_return = ifelse(event, net, NA_real_)
  )
}

lab_event_summary <- function(signal, horizon = 5L, cost_bps = 10,
                              nonoverlap = FALSE) {
  events <- lab_event_returns(signal, horizon, cost_bps, nonoverlap)
  values <- events$net_return[events$event & is.finite(events$net_return)]
  gross <- events$gross_return[events$event & is.finite(events$gross_return)]
  n <- length(values)
  se <- if (n > 1L) stats::sd(values) / sqrt(n) else NA_real_
  data.frame(
    events = n,
    mean_gross = if (n) mean(gross) else NA_real_,
    mean_net = if (n) mean(values) else NA_real_,
    win_rate = if (n) mean(values > 0) else NA_real_,
    ci_low = if (n > 1L) mean(values) - 1.96 * se else NA_real_,
    ci_high = if (n > 1L) mean(values) + 1.96 * se else NA_real_
  )
}

lab_horizon_table <- function(signal, horizons = c(1L, 3L, 5L, 10L),
                              cost_bps = 10) {
  out <- do.call(rbind, lapply(horizons, function(h) {
    data.frame(horizon = h, lab_event_summary(signal, h, cost_bps))
  }))
  rownames(out) <- NULL
  out
}

lab_chapter_table <- function(chapter, horizon = 5L, cost_bps = 10) {
  signal <- lab_chapter_signal(chapter)
  all_events <- lab_event_summary(signal, horizon, cost_bps, FALSE)
  separated <- lab_event_summary(signal, horizon, cost_bps, TRUE)
  rbind(
    cbind(sample = "全部事件", all_events),
    cbind(sample = "非重叠事件", separated)
  )
}

lab_chart <- function(signal, start_date = "2023-01-01", end_date = "2024-12-31",
                      title = "AAPL蜡烛图与候选信号", show_ma = FALSE) {
  data <- lab_read_data()
  x <- lab_xts(data)
  chart <- eFinCharts::ecandlesticks(
    x,
    start_date = start_date,
    end_date = end_date,
    show_volume = TRUE,
    show_ma = show_ma,
    ma_periods = c(20, 50),
    title = title,
    subtitle = "复权OHLC；红色三角=看涨候选，蓝色三角=看跌候选"
  )
  markers <- data[data$date >= as.Date(start_date) & data$date <= as.Date(end_date) & signal != 0, ]
  markers$signal <- signal[data$date >= as.Date(start_date) & data$date <= as.Date(end_date) & signal != 0]
  if (!nrow(markers)) return(chart$combined_plot)
  markers$marker_y <- ifelse(markers$signal > 0, markers$low * 0.985, markers$high * 1.015)
  chart$price_plot +
    ggplot2::geom_point(
      data = markers,
      ggplot2::aes(x = date, y = marker_y, shape = factor(signal), color = factor(signal)),
      inherit.aes = FALSE,
      size = 2.2
    ) +
    ggplot2::scale_shape_manual(values = c(`-1` = 25, `1` = 24), guide = "none") +
    ggplot2::scale_color_manual(values = c(`-1` = "#2166AC", `1` = "#B2182B"), guide = "none")
}

lab_evidence_plot <- function(signal, title = "候选信号的方向调整收益") {
  table <- lab_horizon_table(signal)
  ggplot2::ggplot(table, ggplot2::aes(x = horizon, y = mean_net)) +
    ggplot2::geom_hline(yintercept = 0, color = "grey55", linewidth = 0.5) +
    ggplot2::geom_errorbar(
      ggplot2::aes(ymin = ci_low, ymax = ci_high), width = 0.5, color = "#2166AC"
    ) +
    ggplot2::geom_point(size = 2.5, color = "#B2182B") +
    ggplot2::scale_x_continuous(breaks = table$horizon) +
    ggplot2::scale_y_continuous(labels = scales::label_percent(accuracy = 0.1)) +
    ggplot2::labs(
      title = title,
      subtitle = "t日收盘识别，t+1日开盘成交；已扣除双边10bp成本；误差线为正态近似95%区间",
      x = "持有期（交易日）", y = "方向调整后的平均净收益"
    ) +
    ggplot2::theme_minimal(base_size = 11)
}

lab_print_table <- function(x, digits = 4) {
  numeric_columns <- vapply(x, is.numeric, logical(1))
  x[numeric_columns] <- lapply(x[numeric_columns], round, digits = digits)
  knitr::kable(x)
}
