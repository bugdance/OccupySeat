#!/bin/bash
kill -9 `ps -ef | grep login_xw.py | awk '{print $2}' `
echo 3 > /proc/sys/vm/drop_caches
rm -rf test.log
python3 login_xw.py > /dev/null 2>&1 &
