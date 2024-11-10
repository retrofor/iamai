# Define variables
SRC_DIR := iamai
LOCALE_DIR := locale
POT_FILE := i18n.pot

# Find all Python files in the source directory
PY_FILES := $(shell find $(SRC_DIR) -name "*.py")

# Generate the .pot file
trans-pot: $(SRC_DIR)/$(LOCALE_DIR)/$(POT_FILE)

$(SRC_DIR)/$(LOCALE_DIR)/$(POT_FILE): $(PY_FILES)
	@echo "Generating POT file..."
	@mkdir -p $(dir $@)  # Ensure the directory exists
	@xgettext -o $@ --language=Python --keyword=_ $(PY_FILES)

# Generate .po files for specified languages
trans-gen: trans-pot
	@langs=$(if $(LANGUAGES),$(LANGUAGES),zh)  # Use LANGUAGES if provided, otherwise default to "zh"
	for lang in $$langs; do \
		po_dir=$(SRC_DIR)/$(LOCALE_DIR)/$$lang/LC_MESSAGES; \
		po_file=$$po_dir/i18n.po; \
		mkdir -p $$po_dir; \
		if [ ! -f $$po_file ]; then \
			echo "Generating PO file for language $$lang..."; \
			msginit --locale=$$lang --input=$(SRC_DIR)/$(LOCALE_DIR)/$(POT_FILE) --output-file=$$po_file --no-translator; \
			sed -i 's/charset=ASCII/charset=UTF-8/' $$po_file; \
		else \
			echo "PO file for language $$lang already exists, skipping generation."; \
		fi; \
	done

# Update existing .po files with new .pot file
trans-update: trans-pot
	@for po_file in $(shell find $(SRC_DIR)/$(LOCALE_DIR) -name "i18n.po"); do \
		echo "Updating $$po_file..."; \
		msgmerge --update $$po_file $(SRC_DIR)/$(LOCALE_DIR)/$(POT_FILE); \
	done

# Clean up generated files
trans-clean:
	@echo "Cleaning up translation files..."
	@rm -f $(POT_FILE)
	@find $(LOCALE_DIR) -name "i18n.po" -delete

trans-compile:
	@for po_file in $(shell find $(SRC_DIR)/$(LOCALE_DIR) -name "i18n.po"); do \
		mo_file=$${po_file%.po}.mo; \
		echo "Compiling $$po_file to $$mo_file..."; \
		msgfmt -o $$mo_file $$po_file; \
	done

.PHONY: trans-pot trans-gen trans-update trans-clean trans-compile