import re
import pandas as pd

def parse_kicad_netlist(file_path, output_excel):
    # 1. 读取 KiCad 导出的网表文件
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return

    # 2. 🌟 绝对防御：直接用 '(net (code' 暴力切块，无视任何换行和空格差异！
    net_chunks = content.split('(net (code')
    
    rows = []
    for chunk in net_chunks[1:]:  # 第0块是头部信息，跳过
        
        # 提取网络名
        name_match = re.search(r'\(name\s+"([^"]+)"\)', chunk)
        if not name_match:
            continue
        net_name = name_match.group(1)
        
        slot, instrument, resource = "N/A", "N/A", net_name
        
        # --- 解析网络名，提取板卡和通道信息 ---
        standard_match = re.match(r'^S(\d+)_([^_]+)_(.*)', net_name)
        cbit_match = re.match(r'^S(\d+S\d+|\d+)(CBITE|CBIT|_)([^\s]*)', net_name, re.IGNORECASE)

        if standard_match:
            slot = standard_match.group(1)
            instrument = standard_match.group(2)
            resource = standard_match.group(3)
        elif cbit_match:
            slot = cbit_match.group(1)
            instrument = "CBIT/Power"
            resource = cbit_match.group(2) + cbit_match.group(3)
        elif net_name.upper() in ["AGND", "GND", "DGND", "GNDS"]:
            slot, instrument, resource = "Global", "GND", net_name

        # 3. 🌟 提取该网络下所有的 node (即引脚)
        # 极度宽容的正则，只要是 ref 和 pin 就抓出来
        nodes = re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', chunk)
        
        extracted_pins = []
        for ref, pin in nodes:
            # 🌟 修复：放宽过滤条件，支持 P?A 这种未编号的器件，以及 J, U_P 开头的连接器
            if ref.startswith('P') or ref.startswith('U_P') or ref.startswith('J'):
                extracted_pins.append({"Pogo_Ref": ref, "Pin_Num": pin})

        if not extracted_pins:
            continue

        # ========================================================
        # 🌟 核心魔法：智能拆分被强行合并的 FH 和 SH 
        # ========================================================
        # 如果资源名叫 FH，并且恰好被合并了 2 个 Pogo Pin
        if resource.startswith("FH") and len(extracted_pins) == 2:
            
            # 对引脚进行智能排序 (A2 必须在 A3 前面)
            def sort_key(p):
                m = re.match(r'([A-Za-z]+)(\d+)', p["Pin_Num"])
                return (m.group(1), int(m.group(2))) if m else (p["Pin_Num"], 0)
                
            extracted_pins.sort(key=sort_key)
            
            # 第 1 个引脚保持 Force (FH)
            rows.append({
                "Slot_Group": slot, "Instrument": instrument, "Resource_Function": resource,
                "Pogo_Ref": extracted_pins[0]["Pogo_Ref"], "Pin_Num": extracted_pins[0]["Pin_Num"],
                "Original_Net": net_name
            })
            
            # 第 2 个引脚强行恢复为 Sense (SH)！
            sense_resource = resource.replace("FH", "SH")
            rows.append({
                "Slot_Group": slot, "Instrument": instrument, "Resource_Function": sense_resource,
                "Pogo_Ref": extracted_pins[1]["Pogo_Ref"], "Pin_Num": extracted_pins[1]["Pin_Num"],
                "Original_Net": net_name + " (Auto-Split to Sense)"
            })
            
        else:
            # 正常情况
            for p in extracted_pins:
                rows.append({
                    "Slot_Group": slot, "Instrument": instrument, "Resource_Function": resource,
                    "Pogo_Ref": p["Pogo_Ref"], "Pin_Num": p["Pin_Num"],
                    "Original_Net": net_name
                })

    # 4. 生成 Excel
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by=['Slot_Group', 'Pogo_Ref', 'Pin_Num'])
        df.to_excel(output_excel, index=False)
        print(f"✅ 解析成功！共提取并处理了 {len(df)} 个连接点！\n📁 文件已保存至: {output_excel}")
    else:
        print("❌ 警告：生成的表格依然为空！")
        print("👉 请检查：")
        print("  1. 你的 Exported_Pogo.net 里是否有元件的标号以 'P', 'U_P' 或 'J' 开头？")
        print("  2. 如果你的 Pogo 连机器叫其他名字（比如 CON1, Socket1），请修改代码第 38 行的 if 过滤条件。")

if __name__ == "__main__":
    input_file = r"C:\Users\11271\Desktop\Table2SCH\projects\STS8300_LB_RevA\STS8300_LB_RevA_Master.net"  # 确保这个文件和你在同一个目录下
    parse_kicad_netlist(input_file, "KiCad_Final_Mapping.xlsx")