#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
from pathlib import Path
import sys
s=Path(sys.argv[1]); b=s/'arch/arm/boards/kindle-mx50'
p=b/'Makefile'; p.write_text(p.read_text()+'\nobj-y += boot-trace.o\n')
p=b/'lowlevel.c'; t=p.read_text(); needle='\timx5_cpu_lowlevel_init();'; pos=t.index(needle,t.index('ENTRY_FUNCTION(start_imx50_kindle_d01100'))
t=t[:pos]+'\twritel(0x4b344231, IOMEM(0xf8008000));\n\twritel(1, IOMEM(0xf8008004));\n'+t[pos:]; p.write_text(t)
p=b/'board.c'; t=p.read_text(); start=t.index('\tkindle_rev_init("/dev/mmc2.boot0.userdata"'); end=t.index(';',start)+1; t=t[:start]+ '\t/* Host loader does not read idme or probe storage. */'+t[end:]
start=t.index('\t/* Probe the eMMC'); end=t.index('\tdefaultenv_append_directory',start); t=t[:start]+t[end:]; t=t.replace('\tstruct device *dev;\n',''); a=t.index('static struct envdata'); z=t.index('/* The original kernel',a); t=t[:a]+t[z:]
a=t.index('static void kindle_rev_init'); z=t.index('static int is_mx50_kindle',a); t=t[:a]+t[z:]; p.write_text(t)
# Eliminate vendor boot script, explicit future extension point only.
for p in (b/'defaultenv-kindle-mx50/boot').glob('*'): p.unlink()
(b/'defaultenv-kindle-mx50/boot/host-ram').write_text('#!/bin/sh\necho "Use explicit verified RAM uploads and bootm; no eMMC autoboot implemented"\nexit 1\n')
