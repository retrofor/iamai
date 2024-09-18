# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?= .
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = _build
SPHINXINTL    ?= sphinx-intl 
lang		  ?= zh_CN
SPHINXAPIDOCS ?= sphinx-apidoc
SPHINX 		  ?= sphinx

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# build translation files ``.pot``
trans build:
	@pdm run $(SPHINXBUILD) -b gettext . ./$(BUILDDIR)/gettext $(O)
	# make -e SPHINXOPTS="-D language='de'" html
# update translation command
trans update:
	@$(SPHINXBUILD) -M gettext "$(SOURCEDIR)" "$(BUILDDIR)" $(O)
	@pdm run $(SPHINXINTL) update -p ./$(BUILDDIR)/gettext -l $(lang) $(O)

# build api docs
api build:
	@pdm run $(SPHINXAPIDOCS) -o $(SOURCEDIR)/pages/api ../iamai ../packages -f -e --tocfile index $(O)

# build docs
docs build:
	@pdm run $(SPHINXBUILD) "$(SOURCEDIR)" "$(BUILDDIR)" $(O)