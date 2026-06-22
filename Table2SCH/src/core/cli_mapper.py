import os
import sys
import json
import pandas as pd
import re
import math

# ========================================================
# 🛠️ 路径注入与核心模块导入
# ========================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

project_root = os.path.dirname(src_dir)

try:
    from parsers.excel_parser import HardwareExcelParser
    from core.scheduler import ChannelScheduler
except ImportError as e:
    print(f"⚠️ 核心模块导入提示: {e}")

# ========================================================
# 📊 真实板卡硬件量程与精度规格 (基于 boardcard_accuracy.yaml)
# ========================================================
BOARD_SPECS = {
    "FOVI100": {
        "channels": 16,
        "v_ranges": [
            {"max_v": 0.1, "fs_pct": 0.4, "mode": "MV"},       # ±100mV
            {"max_v": 1.0, "fs_pct": 0.05, "mode": "FV/MV"},   # ±1V
            {"max_v": 50.0, "fs_pct": 0.05, "mode": "FV/MV"}   # ±50V
        ],
        "i_ranges": [
            {"max_i": 10e-6, "fs_pct": 0.5, "mode": "MI"},     # ±10uA (FOVI100 独有高精度档)
            {"max_i": 100e-6, "fs_pct": 0.1, "mode": "FI/MI"}, # ±100uA
            {"max_i": 1.0, "fs_pct": 0.5, "mode": "FI/MI"}     # ±1A
        ]
    },
    "FPVI10_PLUS": {
        "channels": 16,
        "v_ranges": [
            {"max_v": 0.1, "fs_pct": 0.4, "mode": "MV"},       # ±100mV
            {"max_v": 1.0, "fs_pct": 0.05, "mode": "FV/MV"},   # ±1V
            {"max_v": 100.0, "fs_pct": 0.05, "mode": "FV/MV"}  # ±100V
        ],
        "i_ranges": [
            {"max_i": 100e-6, "fs_pct": 0.1, "mode": "FI/MI"}, # ±100uA (FPVI10_PLUS 的最小电流档)
            {"max_i": 10.0, "fs_pct": 0.5, "mode": "FI/MI"}    # ±10A
        ]
    },
    "HV1K": {
        "channels": 8,
        "v_ranges": [
            {"max_v": 100.0, "fs_pct": 0.05, "mode": "FV/MV"}, 
            {"max_v": 1000.0, "fs_pct": 0.05, "mode": "FV/MV"}
        ],
        "i_ranges": [
            {"max_i": 10e-6, "fs_pct": 0.5, "mode": "MI"},     # ±10uA
            {"max_i": 10e-3, "fs_pct": 0.1, "mode": "FI/MI"}   # ±10mA
        ]
    },
    "UIS100": {
        "channels": 8,
        "v_ranges": [
            {"max_v": 50.0, "fs_pct": 0.5, "mode": "MV"},
            {"max_v": 2500.0, "reading_pct": 2.5, "mode": "FV"} 
        ],
        "i_ranges": [
            {"max_i": 100.0, "fs_pct": 0.5, "mode": "FI/MI"}   # ±100A
        ]
    }
}
# ========================================================
# 🧠 核心算法 1: 提取测试极值与需要的绝对测量精度
# ========================================================
def parse_test_plan_metrics(json_2d_array):
    pin_profiles = {}

    def init_pin(p_name):
        if p_name not in pin_profiles:
            # req_i_acc: 要求系统能分辨的最小电流(A), req_v_acc: 最小电压(V)
            pin_profiles[p_name] = {"max_v": 0.0, "max_i": 0.0, "req_i_acc": 1.0, "req_v_acc": 1.0, "is_digital": False}

    for row in json_2d_array:
        if len(row) < 5: continue
        condition_str, unit, test_name = str(row[3]), str(row[4]).upper(), str(row[2]).upper()

        # 1. 提取极值 (Force/Measure Range) 
        force_blocks = re.findall(r'F[VI]\[(.*?)\]', condition_str)
        for block in force_blocks:
            for assignment in block.split(','):
                if '=' in assignment:
                    # 🌟 修复点 1：只切第一刀！(避免 VDD=VIN=17V 导致的崩溃)
                    parts = assignment.split('=', 1) 
                    if len(parts) != 2: continue # 如果格式实在太奇葩，直接跳过
                    
                    raw_pins, raw_val = parts[0], parts[1]
                    sub_pins = [p.strip() for p in raw_pins.split(',') if p.strip()]
                    
                    # 提取数值 (过滤掉后面可能跟着的脏字符)
                    val_match = re.search(r'([-+]?\d*\.\d+|\d+)', raw_val)
                    val = float(val_match.group(1)) if val_match else 0.0
                    
                    for pin in sub_pins:
                        init_pin(pin)
                        if "V" in raw_val.upper() or "FV" in condition_str:
                            pin_profiles[pin]["max_v"] = max(pin_profiles[pin]["max_v"], abs(val))
                        elif "A" in raw_val.upper() or "FI" in condition_str:
                            pin_profiles[pin]["max_i"] = max(pin_profiles[pin]["max_i"], abs(val))

        # 2. 🎯 精度需求推断 (Accuracy Requirements)
        measure_blocks = re.findall(r'(?:MI|MV|Float)\[(.*?)\]', condition_str)
        for block in measure_blocks:
            sub_pins = [p.strip() for p in block.split(',') if p.strip()]
            for pin in sub_pins:
                init_pin(pin)
                if "UA" in unit or "ILKG" in test_name:
                    pin_profiles[pin]["req_i_acc"] = min(pin_profiles[pin]["req_i_acc"], 5e-7) 
                elif "MA" in unit:
                    pin_profiles[pin]["req_i_acc"] = min(pin_profiles[pin]["req_i_acc"], 5e-4) 
                elif "MV" in unit:
                    pin_profiles[pin]["req_v_acc"] = min(pin_profiles[pin]["req_v_acc"], 5e-3) 

    return pin_profiles

# ========================================================
# 🧠 核心算法 2: 辅助电路智能推断引擎
# ========================================================
def infer_auxiliary_circuits(pin_name, profile, best_board, config):
    active_circuits = []
    params = {}
    passives = []
    pin_upper = pin_name.upper()

    def_pkg = config.get('def_pkg', '0603')
    def_vol = config.get('def_vol', '50V')
    def_tol = config.get('def_tol', '1%')

    # 1. 信号调理 - 差分运放
    if any(x in pin_upper for x in ["CS", "ISEN", "SENSE", "VFI", "VFB"]):
        opamp_model = "OPA145_INA141"
        active_circuits.append(opamp_model)
        role = "IN+ (正端)" if "+" in pin_upper or "P" in pin_upper[-2:] else "IN- (负端)"
        base_group = re.sub(r'[\+\-\_]', '', pin_upper.replace('ISEN', 'CS'))
        params[opamp_model] = {"ROLE": role, "GROUP_ID": f"AMP_{base_group}", "GAIN": "10V/V"}

    # 2. 纯净电源 - 低噪 LDO
    if any(x in pin_upper for x in ["VDD", "VCC", "AVDD", "VREF"]) and profile["max_v"] <= 5.5:
        ldo_model = "TPS78401DRVR_3.3V"
        active_circuits.append(ldo_model)
        i_limit = "1A" if profile["max_i"] > 0.5 else "500mA"
        params[ldo_model] = {
            "OUTPUT_NET": f"+{profile['max_v']}V_{pin_upper}_CLN",
            "GROUP_ID": f"LDO_{pin_upper}",
            "I_LIMIT": i_limit
        }

    # 3. 信号路由 - 继电器矩阵 (FOVI或高精度漏电流必须通过矩阵)
    if best_board == "FOVI100" or profile.get("req_i_acc", 1.0) <= 5e-7:
        relay_model = "Relay_Matrix"
        active_circuits.append(relay_model)
        params[relay_model] = {"CBIT": f"CBIT_AUTO_{pin_upper}", "DEFAULT_STATE": "NO (常开)"}

    # 4. 高频匹配与滤波电容
    if profile.get("is_digital") or "PWM" in pin_upper:
        passives.append(f"R_33ohm_{def_pkg}_{def_tol}")
    elif best_board in ["HPSM", "HV1K", "UIS100"]:
        passives.append(f"C_10uF_{def_pkg}_{def_vol}")

    return ",".join(active_circuits), ", ".join(passives), params

# ========================================================
# 🧠 核心算法 3: 量程与精度二维匹配算法
# ========================================================
def check_board_capability(board_name, profile):
    spec = BOARD_SPECS.get(board_name)
    if not spec: return False, float('inf')

    v_range_ok = False
    for r in spec["v_ranges"]:
        if r["max_v"] >= profile["max_v"]:
            v_range_ok = True
            break
            
    best_i_acc = float('inf')
    i_range_ok = False
    for r in spec["i_ranges"]:
        if r["max_i"] >= profile["max_i"]:
            i_range_ok = True
            abs_err = r["max_i"] * (r.get("fs_pct", 1.0) / 100.0) 
            best_i_acc = min(best_i_acc, abs_err)
            
    if not (v_range_ok and i_range_ok):
        return False, float('inf')
        
    if profile["max_i"] == 0.0 and best_i_acc > profile["req_i_acc"]:
        return False, float('inf')

    return True, best_i_acc

def auto_select_board(pin_name, profile, config):
    pin_upper = pin_name.upper()
    
    if any(x in pin_upper for x in ["GND", "VSS"]): 
        return "GND", "Direct", "", "", "{}"
        
    if profile.get("is_digital") and profile["max_v"] <= 7.0: 
        _, passives, _ = infer_auxiliary_circuits(pin_name, profile, "DIO", config)
        return "DIO", "Direct", "", passives, "{}"

    candidates = ["FOVI100", "FPVI10_PLUS", "HV1K", "UIS100"]
    valid_boards = []
    
    for board in candidates:
        is_capable, error_score = check_board_capability(board, profile)
        if is_capable:
            valid_boards.append((board, error_score))
            
    if not valid_boards:
        print(f"⚠️ 引脚 {pin_name} 规格超出所有板卡精度限制 (Req V: {profile['max_v']}V, I: {profile['max_i']}A)，强制降级分配.")
        best_board = "FPVI10_PLUS"
    else:
        valid_boards.sort(key=lambda x: x[1])
        best_board = valid_boards[0][0]

    # 🚀 在确定了板卡后，调用辅助电路引擎推断外围电路
    active_circuits, passives, params = infer_auxiliary_circuits(pin_name, profile, best_board, config)

    connect_type = "Direct"
    if profile["max_i"] > 2.0 or best_board in ["UIS100", "HV1K"]:
        connect_type = "Kelvin"
    elif "Relay_Matrix" in active_circuits:
        connect_type = "Relay"

    return best_board, connect_type, active_circuits, passives, json.dumps(params, ensure_ascii=False)

# ========================================================
# 🧠 核心算法 4: KiCad 符号库智能自适应解析
# ========================================================
def parse_kicad_symbol_pins(sym_path):
    if not os.path.exists(sym_path): 
        print(f"⚠️ 找不到符号文件: {sym_path}")
        return []
        
    with open(sym_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 🌟 修复点 2：加入 re.DOTALL 跨行匹配，搞定 KiCad V6+ 格式
    raw_pins = re.findall(r'\(pin\s+.*?\(\s*name\s+"([^"]+)"', content, re.DOTALL)
    
    # 过滤掉空的或异常名字
    valid_pins = [p.replace('~', '').strip() for p in raw_pins if p.strip()]
    
    return list(set(valid_pins))

# ========================================================
# 🚀 自动化配置流水线总控
# ========================================================
def get_user_input(prompt_msg, default_val):
    val = input(f"🔹 {prompt_msg} [{default_val}]: ").strip()
    return val if val else default_val

class InteractiveMapper:
    def __init__(self):
        self.csv_headers = [
            "Physical Pin (TP Name)", "Logical Net", "Resource Types", 
            "Channel Allocations", "Connect Type", "Active Circuits", "Passives", "Params"
        ]
        self.config = {}

    def setup_project_defaults(self):
        print("\n" + "="*60)
        print("🛠️  Table2Sch 工业级自适应 ATE 规划器 (V6.0 Aux-Inference)")
        print("="*60)
        self.config['project_name'] = get_user_input("Project Name", "STS8300_LB_RevA")
        self.config['sites'] = int(get_user_input("Total Sites", "4"))
        self.config['def_pkg'] = get_user_input("Default Package", "0603")
        self.config['def_vol'] = get_user_input("Default Voltage", "50V")
        self.config['def_tol'] = get_user_input("Default Tolerance", "1%")
        
        default_hw = os.path.join(project_root, "Sch_lib", "platforms", "sts8300_slot.xlsx")
        self.config['hw_path'] = get_user_input("Hardware Config Excel", os.path.normpath(default_hw))
        
        default_tp = os.path.join(project_root, "FT_Test_Plan_JSON.json")
        self.config['tp_path'] = get_user_input("Test Plan JSON Path", default_tp)
        
        default_sym = os.path.join(project_root, "Sch_lib", "sockets", "JW_Contator.kicad_sym")
        self.config['sym_path'] = get_user_input("KiCad Sym Path", os.path.normpath(default_sym))

    def run_pipeline(self):
        self.setup_project_defaults()
        
        try:
            self.slot_map, self.channels_per_board = HardwareExcelParser.parse(self.config['hw_path'])
            print(f"✅ [1/4] 硬件机箱拓扑解析成功.")
        except Exception as e:
            print(f"❌ 硬件 Excel 解析失败: {e}. 将启用备用资源字典。")
            self.slot_map, self.channels_per_board = {"FPVI10_PLUS": [1, 2], "FOVI100": [3]}, {}

        socket_pins = parse_kicad_symbol_pins(self.config['sym_path'])
        print(f"✅ [2/4] Symbol 库自动解析成功. 提取到 {len(socket_pins)} 个封装管脚.")

        print("⏳ [3/4] 正在深度扫描测试向量条件...")
        try:
            with open(self.config['tp_path'], 'r', encoding='utf-8') as f:
                raw_json = json.load(f)
            pin_profiles = parse_test_plan_metrics(raw_json)
            print(f"✅ 成功从向量中逆向解析出 {len(pin_profiles)} 个独立活跃引脚.")
        except Exception as e:
            print(f"❌ Test Plan 扫描失败: {e}")
            return

        print("⏳ [4/4] 启动精度调度与辅助电路推断引擎...")
        table_data_for_scheduler = []
        gui_table_rows = []

        for idx, (pin, profile) in enumerate(pin_profiles.items()):
            # 🚀 引擎接管：传入 config 字典，一次性解析出板卡、外围器件与参数
            board_type, conn, active, passives, params_json = auto_select_board(pin, profile, self.config)

            table_data_for_scheduler.append({
                "resources": [board_type] if board_type != "GND" else [],
                "params": json.loads(params_json),
                "row_idx": idx
            })

            gui_table_rows.append({
                "Physical Pin (TP Name)": pin,
                "Logical Net": f"{pin}_NET",
                "Resource Types": board_type,
                "Connect Type": conn,
                "Active Circuits": active,
                "Passives": passives,
                "Params": params_json,
                "Channel Allocations": "GND" if board_type == "GND" else ""
            })

        try:
            allocations = ChannelScheduler.allocate(
                table_data_for_scheduler, self.config['sites'], 
                self.slot_map, self.channels_per_board
            )
            for i, row in enumerate(gui_table_rows):
                if row["Resource Types"] != "GND":
                    row["Channel Allocations"] = allocations.get(i, f"{row['Resource Types']}[AUTO_CH]")
        except Exception as e:
            print(f"⚠️ 通道精细分配器警告: {e}")
            for i, row in enumerate(gui_table_rows):
                if row["Resource Types"] != "GND":
                    row["Channel Allocations"] = f"{row['Resource Types']}[Slot1_CH{i}]"

        output_csv = f"{self.config['project_name']}.csv"
        df = pd.DataFrame(gui_table_rows, columns=self.csv_headers)
        df.to_csv(output_csv, index=False, encoding='utf-8')
        print(f"\n🚀 自动化流水线完美执行结束！硬件映射表已存至: {output_csv}\n")

if __name__ == "__main__":
    cli = InteractiveMapper()
    cli.run_pipeline()