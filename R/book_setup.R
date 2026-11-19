options(
  htmltools.dir.version = FALSE,
  width = 80,
  digits = 4,
  stringsAsFactors = FALSE
)

if (requireNamespace("knitr", quietly = TRUE)) {
  knitr::opts_chunk$set(
    echo = TRUE,
    message = FALSE,
    warning = FALSE,
    fig.align = "center",
    fig.width = 8,
    fig.height = 4.8,
    dpi = 144,
    out.width = "100%"
  )
}

source("R/candlestick_lab.R", local = knitr::knit_global())
