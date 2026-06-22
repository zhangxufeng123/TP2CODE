#!/usr/bin/env python3
"""简化版被动元件生成测试"""

import sys
from pathlib import Path

src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from debug_gen import load_csv_as_dict

print("🎯 简化版被动元件检测")

csv_file = "STS8300_LB_RevA.csv"
config_data = load_csv_as_dict(csv_file)

print(f"✅ 成功读取CSV")
print(f"📊 配置中包含 {len(config_data.get('pin_template_mapping', []))} 个引脚")

# 直接统计被动元件
total_passives = 0
for pin_data in config_data.get('pin_template_mapping', []):
    passives = pin_data.get('passive_circuits', [])
    if passives:
        total_passives += len(passives)
        for passive in passives:
            print(f"⚡ 发现: {passive}")

print(f"\n🎊 总计: {total_passives} 个被动元件")

# 查看最后的生成状态
projects_dir = Path("projects")
if projects_dir.exists():
    print(f"📁 项目目录已存在")
    for item in projects_dir.iterdir():
        if item.is_dir():
            print(f"  项目: {item.name}")
else:
    print("❌ 项目目录不存在")