$ErrorActionPreference = "Stop"

Push-Location $PSScriptRoot
try {
    if (Get-Command latexmk -ErrorAction SilentlyContinue) {
        latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
    }
    else {
        pdflatex -interaction=nonstopmode -halt-on-error main.tex
        bibtex main
        pdflatex -interaction=nonstopmode -halt-on-error main.tex
        pdflatex -interaction=nonstopmode -halt-on-error main.tex
    }
}
finally {
    Pop-Location
}
