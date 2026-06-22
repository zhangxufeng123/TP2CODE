import json
import csv
import yaml
import os

class ReportGenerator:
    @staticmethod
    def export_all(config_dict: dict, output_dir: str = ""):
        """接收标准化的字典数据，一键导出三种格式"""
        proj_name = config_dict["project_info"]["project_name"]
        if not proj_name:
            proj_name = "ATE_Project"
            
        base_path = os.path.join(output_dir, proj_name)

        # 1. 导出 JSON
        with open(f"{base_path}.json", "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
        # 2. 导出 YAML
        with open(f"{base_path}.yaml", "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
            
        # 3. 导出 CSV
        csv_rows = []
        csv_rows.append(["# ====== PROJECT SETUP METADATA ======"])
        for k, v in config_dict["project_info"].items():
            csv_rows.append([k, v])
        csv_rows.append(["Hardware Config", config_dict["hardware_config"]])
        csv_rows.append([]) 
        csv_rows.append(["# ====== PIN MAPPING ======"])
        
        csv_headers = ["Display Pin", "Hidden F/S Mapping", "Logical Net", 
                       "Resource Types", "Channel Allocations", "Connect Type", 
                       "Active Circuits", "Passive Circuits (Parsed)", "Params"]
        csv_rows.append(csv_headers)
        
        for row in config_dict["pin_template_mapping"]:
            csv_rows.append([
                row["display_pin"],
                str(row["socket_pins_map"]),
                row["logical_net"],
                ", ".join(row["resources"]),
                row["allocated_channels"],
                row["connect_type"],
                ", ".join(row["active_circuits"]),
                str(row["passive_circuits"]),
                row["parameters"]
            ])
            
        with open(f"{base_path}.csv", "w", newline="", encoding="utf-8-sig") as f: 
            writer = csv.writer(f)
            writer.writerows(csv_rows)
            
        return f"✅ {proj_name}.json\n✅ {proj_name}.yaml\n✅ {proj_name}.csv"