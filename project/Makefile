# SPDX-License-Identifier: GPL-2.0-or-later
.PHONY: images kernel check
MODE ?= source
images:
	python3 images.py --inputs "$(INPUTS)" --out "$(OUT)" --mode "$(MODE)" $(if $(SOURCE),--source "$(SOURCE)",)
check:
	python3 images.py --inputs "$(INPUTS)" --out "$(OUT)" --mode "$(MODE)" $(if $(SOURCE),--source "$(SOURCE)",) --check-only
kernel:
	python3 build.py --inputs "$(INPUTS)" --out "$(OUT)" --mode "$(MODE)" $(if $(SOURCE),--source "$(SOURCE)",)
