# SPDX-License-Identifier: GPL-2.0-or-later
.PHONY: images check
images:
	python3 build.py --inputs "$(INPUTS)" --out "$(OUT)" $(if $(SOURCE),--source "$(SOURCE)",)
check:
	python3 build.py --inputs "$(INPUTS)" --out "$(OUT)" $(if $(SOURCE),--source "$(SOURCE)",) --check-only
