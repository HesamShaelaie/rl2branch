BUILDDIR := build
TEX      := main.tex
PDF      := $(BUILDDIR)/main.pdf
LATEX    := pdflatex -interaction=nonstopmode -output-directory=$(BUILDDIR)

.PHONY: all clean

all: $(PDF)

# Run twice to resolve TOC and cross-references
$(PDF): $(TEX)
	mkdir -p $(BUILDDIR)
	$(LATEX) $(TEX)
	$(LATEX) $(TEX)

# Delete the entire build folder
clean:
	rm -rf $(BUILDDIR)
