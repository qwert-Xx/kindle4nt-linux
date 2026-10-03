#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
import pathlib, subprocess, sys
if __name__=="__main__":
 args=sys.argv[1:];args=["--cache" if x=="--out" else x for x in args]
 subprocess.run([sys.executable,str(pathlib.Path(__file__).resolve().parents[2]/"sources/fetch.py")]+args,check=True)
