#!/bin/bash
echo "=== Тестирование с внешней VFS ==="
python main.py --vfs-path vfs/simple_vfs.zip --startup-script demo_commands.txt
