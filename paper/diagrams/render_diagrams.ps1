$ErrorActionPreference = "Stop"

$diagrams = @(
  "aen_architecture",
  "triadic_turn_protocol",
  "cb7_instruction_dispatch",
  "single_model_vs_triad",
  "controller_finalization_contract"
)

$root = Resolve-Path (Join-Path $PSScriptRoot "..")

Push-Location $root
try {
  foreach ($name in $diagrams) {
    $tex = "\documentclass[tikz,border=6pt]{standalone}\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage{xcolor}\usepackage{tikz}\usetikzlibrary{arrows.meta,positioning,fit,shapes.geometric}\begin{document}\input{diagrams/$name}\end{document}"
    pdflatex -interaction=nonstopmode -halt-on-error -output-directory=diagrams "-jobname=$name" $tex
    pdftocairo -png -singlefile -r 300 "diagrams/$name.pdf" "diagrams/$name"
    Remove-Item -LiteralPath "diagrams/$name.aux", "diagrams/$name.log" -Force -ErrorAction SilentlyContinue
  }
}
finally {
  Pop-Location
}
