import pandas as pd
import yaml
import re
import csv
import json
import os
from pathlib import Path

class MultisiteTesterPool:
    def __init__(self, ate_platform_str, config_dir=None, site_count=4):
        # 动态路径计算
        self.project_root = Path(__file__).parent.parent.parent
        self.slot_path = self.project_root / "Sch_lib" / "platforms" / "sts8300_slot.xlsx"
        
        # 确保文件存在
        if not self.slot_path.exists():
            raise FileNotFoundError(
                f"关键文件缺失！请确认以下文件存在:\n{self.slot_path}\n"
                f"当前工作目录: {os.getcwd()}"
            )

        self.site_count = site_count
        self.ate_platform = ate_platform_str
        self.config_dir = config_dir or (self.project_root / "config")
        self.board_accuracy = self._load_accuracy_yaml()  # 修复：补充这个方法
        self.slots = self._load_slots()
        self.status = {}
        self._init_status()

    def _load_accuracy_yaml(self):
        """加载板卡精度配置文件"""
        base_platform = re.search(r'(STS\d+)', self.ate_platform.upper()).group(1)
        yaml_file = f"boardcard_accuracy_{base_platform}.yaml"
        yaml_path = self.config_dir / yaml_file
        
        if not yaml_path.exists():
            print(f"[!] 警告: 未找到精度配置文件 {yaml_path}, 使用默认配置")
            return {"default": True}
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _load_slots(self):
        """加载槽位配置"""
        try:
            df = pd.read_excel(self.slot_path)
            df.columns = df.columns.str.strip().str.replace('\n', '')
            return df.to_dict('records')
        except Exception as e:
            raise ValueError(f"读取Slot文件失败 {self.slot_path}: {str(e)}")

    def _init_status(self):
        for slot in self.slots:
            slot_id = slot['Physical_Slot']
            self.status[slot_id] = {
                'board': slot['Resource_Type'],
                'site': str(slot['Site_ID']),
                'max_ch': int(slot['Max_Channels']),
                'used_ch_count': 0
            }

    # ... (其他现有方法保持不变) ...

def generate_schematic_mapping(output_csv, ate_platform_str, config_dir=None):
    try:
        # 动态路径计算
        project_root = Path(__file__).parent.parent.parent
        if config_dir is None:
            config_dir = project_root / "config"
        
        tester = MultisiteTesterPool(
            ate_platform_str=ate_platform_str,
            config_dir=config_dir,
            site_count=4
        )
        
        pin_csv = project_root / "Final_Pin_Specs_v4.csv"
        if not pin_csv.exists():
            raise FileNotFoundError(f"测试计划文件缺失: {pin_csv}")

        # ... (后续处理逻辑保持不变) ...
        print(f"✅ 配置文件已生成: {output_csv}")
    
    except Exception as e:
        print(f"❌ 生成失败: {str(e)}")
        raise

if __name__ == "__main__":
    generate_schematic_mapping(
        output_csv="STS8300_LB_RevA.csv",
        ate_platform_str="STS8300_A28D4"
    )