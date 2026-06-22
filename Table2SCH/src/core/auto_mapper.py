import json
import pandas as pd
import os

class AutoPinMapper:
    def __init__(self, project_name="STS8300_LB_RevA", sites=4):
        self.project_name = project_name
        self.sites = sites
        # 目标 CSV 的表头，与你 GUI 中的 table 保持一致
        self.csv_headers = [
            "Physical Pin (TP Name)", "Logical Net", "Resource Types", 
            "Channel Allocations", "Connect Type", "Active Circuits", "Passives", "Params"
        ]
        
    def load_json_testplan(self, json_path):
        """加载从 Test Plan 提取的 JSON 数据"""
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _apply_joulwatt_multiphase_rules(self, pin_name, pin_type, voltage=None):
        """
        🚀 核心映射算法：针对 Joulwatt 多相控制器的测试硬件逻辑
        这里替代了 GUI 里的手动选择，根据 pin 属性自动推断 ATE 资源
        """
        pin_name_upper = pin_name.upper()
        
        # 默认值
        resource = "DCM"
        connect_type = "Direct"
        active_circuits = ""
        params = {}

        # 1. 大电流电源引脚 (HPSM / Kelvin 架构)
        if "VIN" in pin_name_upper or "VCC" in pin_name_upper or "VDD" in pin_name_upper:
            resource = "HPSM"
            connect_type = "Kelvin"  # 电源强制开尔文连接
            if voltage and float(voltage.replace('V', '')) < 5.0:
                # 低压电源自动挂载 LDO 模块
                active_circuits = "TPS78401DRVR_3.3V"
                params["TPS78401DRVR_3.3V"] = {
                    "OUTPUT_NET": f"+{voltage}_ANA",
                    "GROUP_ID": f"LDO_{pin_name_upper}"
                }

        # 2. 模拟测量引脚 (ACM200 / FXVIe)
        elif pin_type in ["Analog", "Sense"]:
            resource = "ACM200"
            connect_type = "Relay" # 走 CBIT 继电器矩阵切换
            
            # 多相控制器的 Current Sense (CS) 需要运放
            if "CS" in pin_name_upper or "ISEN" in pin_name_upper:
                active_circuits = "OPA145_INA141"
                params["OPA145_INA141"] = {
                    "ROLE": "IN+ (正端)" if "+" in pin_name_upper else "IN- (负端)",
                    "GROUP_ID": "AMP_CS_Group",
                    "VCC_NET": "+3.3V_ANA"
                }

        # 3. 高速 PWM/数字引脚 (DCM)
        elif "PWM" in pin_name_upper or pin_type == "Digital":
            resource = "DCM"
            connect_type = "Direct"

        # 4. 接地引脚
        elif "GND" in pin_name_upper or "VSS" in pin_name_upper:
            resource = "GND"
            connect_type = "Direct"

        return resource, connect_type, active_circuits, json.dumps(params, ensure_ascii=False) if params else "{}"

    def mock_channel_allocation(self, resource, row_idx):
        """
        模拟调用现有的 ChannelScheduler 分配逻辑。
        真实环境应调用：ChannelScheduler.allocate(mock_table_data, total_sites, slot_map, channels_per_board)
        """
        if resource == "GND":
            return "GND"
            
        allocations = []
        for site in range(1, self.sites + 1):
            # 简单的虚拟通道分配，用于演示 CSV 结构
            channel = f"{resource}[B{site}_CH{row_idx}]"
            allocations.append(f"Site{site}({channel})")
        return " | ".join(allocations)

    def generate_csv(self, json_data, output_csv_path):
        """执行完整流水线并导出 CSV"""
        mapped_rows = []
        
        # 假设 json_data 是一个包含 pin 字典的列表: [{"PinName": "PWM1", "Type": "Digital", "Voltage": "3.3V"}, ...]
        for idx, pin_data in enumerate(json_data):
            pin_name = pin_data.get("PinName", f"PIN_{idx}")
            pin_type = pin_data.get("Type", "Unknown")
            voltage = pin_data.get("Voltage", None)
            
            # 1. 生成 Logical Net
            logical_net = f"{pin_name}_NET"
            
            # 2. 应用映射规则
            resource, conn_type, active_c, params = self._apply_joulwatt_multiphase_rules(pin_name, pin_type, voltage)
            
            # 3. 执行通道分配
            channel_alloc = self.mock_channel_allocation(resource, idx)
            
            # 4. 构建行数据
            row = {
                "Physical Pin (TP Name)": pin_name,
                "Logical Net": logical_net,
                "Resource Types": resource,
                "Channel Allocations": channel_alloc,
                "Connect Type": conn_type,
                "Active Circuits": active_c,
                "Passives": "", # 可根据需要在规则中扩展
                "Params": params
            }
            mapped_rows.append(row)
            
        # 转换为 DataFrame 并导出
        df = pd.DataFrame(mapped_rows, columns=self.csv_headers)
        df.to_csv(output_csv_path, index=False, encoding='utf-8')
        print(f"✅ 成功生成 ATE 硬件配置文件: {output_csv_path}")

# ==========================================
# 🚀 运行脚本
# ==========================================
if __name__ == "__main__":
    # 模拟读取到的 Test Plan JSON 格式
    dummy_json_data = [
        {"PinName": "VIN", "Type": "Power", "Voltage": "12V"},
        {"PinName": "VCC", "Type": "Power", "Voltage": "3.3V"},
        {"PinName": "PWM1", "Type": "Digital"},
        {"PinName": "PWM2", "Type": "Digital"},
        {"PinName": "CS1+", "Type": "Analog"},
        {"PinName": "GND", "Type": "Power"}
    ]
    
    # 实际使用时替换为: 
    # mapper = AutoPinMapper()
    # json_data = mapper.load_json_testplan("FT_Test_Plan_JSON.json")
    
    mapper = AutoPinMapper(sites=4)
    mapper.generate_csv(dummy_json_data, "STS8300_LB_RevA.csv")