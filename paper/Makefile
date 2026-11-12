PDFLATEX ?= pdflatex
BIBTEX := $(shell command -v bibtex >/dev/null 2>&1 && echo bibtex || echo bibtex8)
TEXFLAGS = -interaction=nonstopmode -halt-on-error

.PHONY: all main full clean

all: main full

main:
	$(PDFLATEX) $(TEXFLAGS) main.tex
	$(BIBTEX) main
	$(PDFLATEX) $(TEXFLAGS) main.tex
	$(PDFLATEX) $(TEXFLAGS) main.tex
	$(PDFLATEX) $(TEXFLAGS) main.tex

full:
	$(PDFLATEX) $(TEXFLAGS) full_working_draft.tex
	$(BIBTEX) full_working_draft
	$(PDFLATEX) $(TEXFLAGS) full_working_draft.tex
	$(PDFLATEX) $(TEXFLAGS) full_working_draft.tex
	$(PDFLATEX) $(TEXFLAGS) full_working_draft.tex

clean:
	rm -f *.aux *.bbl *.blg *.fdb_latexmk *.fls *.log *.out *.toc *.synctex.gz
