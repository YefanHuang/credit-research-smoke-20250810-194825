#!/bin/bash
# 文件自动分类脚本
# 在项目根目录运行此脚本，自动整理新增的测试和文档文件

echo "🔧 开始自动整理项目文件..."

# 创建必要目录
mkdir -p tests docs examples scripts

# Python自动分类
python -c "
from auto_organize import FileOrganizer
organizer = FileOrganizer()
moves = organizer.organize_files()
total = sum(len(files) for files in moves.values())
if total > 0:
    print(f'📁 共整理 {total} 个文件')
else:
    print('✅ 所有文件都已在正确位置')
"

echo "🎉 文件整理完成！"
