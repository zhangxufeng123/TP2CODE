import uuid
import os
import re

def gen_uuid():
    return str(uuid.uuid4())

# 这里是你提供的那几个器件的图形定义 (保持不变)
LIB_SYMBOLS_BLOCK = """
  (lib_symbols
    (symbol "JW_Component:DIODE_10L45A (Altium Display 1)" (pin_names (hide yes)) (exclude_from_sim no) (in_bom yes) (on_board yes) (property "Reference" "D" (at 0.254 4.064 0) (effects (font (size 1.27 1.27)))) (property "Value" "1N4148" (at -2.794 -4.318 0) (effects (font (size 1.27 1.27)) (justify left bottom))) (property "Footprint" "JWH636C2_JP25516A_HB_VQFN6X6-48_STS8300_25C_20250414_A:SOD123" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes))) (symbol "DIODE_10L45A (Altium Display 1)_1_0" (polyline (pts (xy -1.016 2.54) (xy 1.524 0) (xy -1.016 -2.54) (xy -1.016 2.54)) (stroke (width -0.0001) (type solid)) (fill (type outline))) (polyline (pts (xy 1.524 -2.54) (xy 1.778 -2.54) (xy 1.778 2.54) (xy 1.524 2.54) (xy 1.524 -2.54)) (stroke (width -0.0001) (type solid)) (fill (type outline))) (pin bidirectional line (at -3.81 0 0) (length 3.81) (name "1" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27))))) (pin bidirectional line (at 3.81 0 180) (length 2.54) (name "2" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))))
    (symbol "JW_Component:MMBD4148SE" (pin_names (hide yes)) (exclude_from_sim no) (in_bom yes) (on_board yes) (property "Reference" "D" (at 14.478 5.842 0) (effects (font (size 1.8288 1.8288)))) (property "Value" "MMBD4148SE" (at 10.414 1.524 0) (effects (font (size 1.8288 1.8288)) (justify left bottom))) (property "Footprint" "JWH636C2_JP25516A_HB_VQFN6X6-48_STS8300_25C_20250414_A:SOT23" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes))) (symbol "MMBD4148SE_1_0" (polyline (pts (xy -2.54 2.032) (xy 0 4.572) (xy 2.54 2.032) (xy -2.54 2.032)) (stroke (width -0.0001) (type solid)) (fill (type outline))) (polyline (pts (xy -0.254 4.826) (xy -0.254 7.62) (xy 6.35 7.62) (xy 6.35 4.826)) (stroke (width 0) (type solid)) (fill (type none))) (polyline (pts (xy 0 0) (xy 0 2.032)) (stroke (width 0) (type solid)) (fill (type none))) (polyline (pts (xy 2.54 4.572) (xy 2.54 4.826) (xy -2.54 4.826) (xy -2.54 4.572) (xy 2.54 4.572)) (stroke (width -0.0001) (type solid)) (fill (type outline))) (polyline (pts (xy 3.81 2.286) (xy 3.81 2.032) (xy 8.89 2.032) (xy 8.89 2.286) (xy 3.81 2.286)) (stroke (width -0.0001) (type solid)) (fill (type outline))) (polyline (pts (xy 6.35 0) (xy 6.35 2.286)) (stroke (width 0) (type solid)) (fill (type none))) (polyline (pts (xy 8.89 4.826) (xy 6.35 2.286) (xy 3.81 4.826) (xy 8.89 4.826)) (stroke (width -0.0001) (type solid)) (fill (type outline)))) (symbol "MMBD4148SE_1_1" (pin bidirectional line (at 0 -2.54 90) (length 2.54) (name "1" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27))))) (pin bidirectional line (at 2.54 10.16 270) (length 2.54) (name "3" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27))))) (pin bidirectional line (at 6.35 -2.54 90) (length 2.54) (name "2" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))))
    (symbol "JW_Component:RELAY_AGQ2004H_THT" (pin_names (hide yes)) (exclude_from_sim no) (in_bom yes) (on_board yes) (property "Reference" "K" (at 5.08 5.08 0) (effects (font (size 1.4478 1.4478)))) (property "Value" "RELAY_AGQ2004H_THT" (at 30.734 -5.588 0) (effects (font (size 1.4478 1.4478)) (justify left bottom))) (property "Footprint" "RELAY_AGQ2004H" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes))) (symbol "RELAY_AGQ2004H_THT_1_0" (polyline (pts (xy 2.54 0) (xy 2.54 1.27)) (stroke (width 0) (type solid)) (fill (type none))) (arc (start 2.54 1.27) (mid 3.81 2.54) (end 5.08 1.27) (stroke (width 0) (type solid)) (fill (type none))) (polyline (pts (xy 5.08 0) (xy 5.08 1.27)) (stroke (width 0) (type solid)) (fill (type none))) (arc (start 5.08 1.27) (mid 6.35 2.54) (end 7.62 1.27) (stroke (width 0) (type solid)) (fill (type none))) (polyline (pts (xy 7.62 0) (xy 7.62 1.27)) (stroke (width 0) (type solid)) (fill (type none))) (arc (start 7.62 1.27) (mid 8.89 2.54) (end 10.16 1.27) (stroke (width 0) (type solid)) (fill (type none))) (polyline (pts (xy 10.16 0) (xy 10.16 1.27)) (stroke (width 0) (type solid)) (fill (type none))) (arc (start 10.16 1.27) (mid 11.43 2.54) (end 12.7 1.27) (stroke (width 0) (type solid)) (fill (type none))) (polyline (pts (xy 12.7 0) (xy 12.7 1.27)) (stroke (width 0) (type solid)) (fill (type none))) (pin power_in line (at 0 0 0) (length 2.54) (name "" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27))))) (pin passive line (at 15.24 0 180) (length 2.54) (name "" (effects (font (size 1.27 1.27)))) (number "8" (effects (font (size 1.27 1.27)))))) (symbol "RELAY_AGQ2004H_THT_2_0" (circle (center 8.255 0) (radius 0.635) (stroke (width 0) (type solid)) (fill (type none))) (circle (center 17.145 2.54) (radius 0.635) (stroke (width 0) (type solid)) (fill (type none))) (circle (center 17.145 -2.54) (radius 0.635) (stroke (width 0) (type solid)) (fill (type none))) (polyline (pts (xy 18.161 -2.159) (xy 8.89 0)) (stroke (width 0) (type solid)) (fill (type none))) (pin passive line (at 0 0 0) (length 7.62) (name "" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27))))) (pin passive line (at 25.4 2.54 180) (length 7.62) (name "" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27))))) (pin passive line (at 25.4 -2.54 180) (length 7.62) (name "" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))) (symbol "RELAY_AGQ2004H_THT_3_0" (circle (center 8.255 0) (radius 0.635) (stroke (width 0) (type solid)) (fill (type none))) (circle (center 17.145 2.54) (radius 0.635) (stroke (width 0) (type solid)) (fill (type none))) (circle (center 17.145 -2.54) (radius 0.635) (stroke (width 0) (type solid)) (fill (type none))) (polyline (pts (xy 18.161 -2.159) (xy 8.89 0)) (stroke (width 0) (type solid)) (fill (type none))) (pin passive line (at 0 0 0) (length 7.62) (name "" (effects (font (size 1.27 1.27)))) (number "6" (effects (font (size 1.27 1.27))))) (pin passive line (at 25.4 2.54 180) (length 7.62) (name "" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27))))) (pin passive line (at 25.4 -2.54 180) (length 7.62) (name "" (effects (font (size 1.27 1.27)))) (number "7" (effects (font (size 1.27 1.27)))))))
    (symbol "JW_Component:R_SM_0805_2" (pin_numbers (hide yes)) (pin_names (hide yes)) (exclude_from_sim no) (in_bom yes) (on_board yes) (property "Reference" "R" (at -2.54 1.016 0) (effects (font (size 1.8288 1.8288)))) (property "Value" "1K" (at -5.334 1.016 0) (effects (font (size 1.8288 1.8288)) (justify left bottom))) (property "Footprint" "R_SM_0805_2" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes))) (symbol "R_SM_0805_2_1_0" (polyline (pts (xy 2.54 0) (xy 1.524 0) (xy 1.524 0) (xy 1.524 0) (xy 1.524 0) (xy 1.27 -0.508) (xy 1.27 -0.508) (xy 1.27 -0.508) (xy 1.27 -0.508) (xy 0.762 0.508) (xy 0.762 0.508) (xy 0.762 0.508) (xy 0.762 0.508) (xy 0.254 -0.508) (xy 0.254 -0.508) (xy 0.254 -0.508) (xy 0.254 -0.508) (xy -0.254 0.508) (xy -0.254 0.508) (xy -0.254 0.508) (xy -0.254 0.508) (xy -0.762 -0.508) (xy -0.762 -0.508) (xy -0.762 -0.508) (xy -0.762 -0.508) (xy -1.27 0.508) (xy -1.27 0.508) (xy -1.27 0.508) (xy -1.27 0.508) (xy -1.524 0) (xy -1.524 0) (xy -1.524 0) (xy -1.524 0) (xy -2.54 0)) (stroke (width 0) (type solid)) (fill (type none))) (pin passive line (at -5.08 0 0) (length 2.54) (name "1" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27))))) (pin passive line (at 5.08 0 180) (length 2.54) (name "2" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))))
    (symbol "power:GNDREF" (power) (pin_numbers (hide yes)) (pin_names (offset 0) (hide yes)) (exclude_from_sim no) (in_bom yes) (on_board yes) (property "Reference" "#PWR" (at 0 -6.35 0) (effects (font (size 1.27 1.27)) (hide yes))) (property "Value" "GNDREF" (at 0 -3.81 0) (effects (font (size 1.27 1.27)))) (symbol "GNDREF_0_1" (polyline (pts (xy -0.635 -1.905) (xy 0.635 -1.905)) (stroke (width 0) (type default)) (fill (type none))) (polyline (pts (xy -0.127 -2.54) (xy 0.127 -2.54)) (stroke (width 0) (type default)) (fill (type none))) (polyline (pts (xy 0 -1.27) (xy 0 0)) (stroke (width 0) (type default)) (fill (type none))) (polyline (pts (xy 1.27 -1.27) (xy -1.27 -1.27)) (stroke (width 0) (type default)) (fill (type none)))) (symbol "GNDREF_1_1" (pin power_in line (at 0 0 270) (length 0) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))))
  )
"""

class KelvinModuleBuilder:
    def __init__(self, ch_index, sheet_uuid, sheet_id="S1", offset_x=0.0, offset_y=0.0, net_map=None):
        self.ch = ch_index
        self.sheet_uuid = sheet_uuid  
        self.sheet_id = sheet_id      # 新增参数，定义图纸后缀
        self.dx = offset_x
        self.dy = offset_y
        self.net_map = net_map or {}
        self.output = []

    def get_net(self, default_name):
        base = self.net_map.get(default_name, default_name)
        # 为所有网络名追加图纸后缀 (例如 DPS1_F_S1)
        return f"{base}_{self.sheet_id}"

    def get_ref(self, base_ref):
        # 完美命名：基准名_通道号_图纸号 (例如 K1_CH1_S1)
        return f"{base_ref}_CH{self.ch}_{self.sheet_id}"

    def add_symbol(self, lib_id, ref_base, x, y, angle=0, unit=1, mirror=""):
        ref = self.get_ref(ref_base)
        x_pos, y_pos = x + self.dx, y + self.dy
        
        mirror_str = f"(mirror {mirror})" if mirror else ""
        angle_str = str(angle) if angle != 0 else "0"
        
        sym_uuid = gen_uuid()
        sym_expr = f"""
  (symbol (lib_id "{lib_id}") (at {x_pos:.2f} {y_pos:.2f} {angle_str}) {mirror_str} (unit {unit})
    (in_bom yes) (on_board yes) (uuid "{sym_uuid}")
    (property "Reference" "{ref}" (at {x_pos:.2f} {y_pos - 2.54:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "" (at {x_pos:.2f} {y_pos:.2f} 0) (effects (hide yes)))
    (instances (project "" (path "/{self.sheet_uuid}" (reference "{ref}") (unit {unit}))))
  )"""
        self.output.append(sym_expr)

    def add_label(self, net_base, shape, x, y, angle=0):
        net_name = self.get_net(net_base)
        x_pos, y_pos = x + self.dx, y + self.dy
        align = "right" if angle == 180 else "left"
        lbl_expr = f"""  (global_label "{net_name}" (shape {shape}) (at {x_pos:.2f} {y_pos:.2f} {angle}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {align})) (uuid "{gen_uuid()}"))"""
        self.output.append(lbl_expr)

    def add_power_label(self, net_base, x, y, angle=0):
        net_name = self.get_net(net_base)
        x_pos, y_pos = x + self.dx, y + self.dy
        pwr_uuid = gen_uuid()
        
        # 修复 U? 问题：追加隐藏的 Reference 属性及 instances 实例
        pwr_ref = f"#PWR_{pwr_uuid[:6]}"
        pwr_expr = f"""
  (symbol (lib_id "power:GNDREF") (at {x_pos:.2f} {y_pos:.2f} {angle}) (unit 1)
    (in_bom yes) (on_board yes) (uuid "{pwr_uuid}")
    (property "Reference" "{pwr_ref}" (at {x_pos:.2f} {y_pos:.2f} 0) (effects (hide yes)))
    (property "Value" "{net_name}" (at {x_pos+3.81:.2f} {y_pos:.2f} {angle}) (effects (font (size 1.27 1.27))))
    (instances (project "" (path "/{self.sheet_uuid}" (reference "{pwr_ref}") (unit 1))))
  )"""
        self.output.append(pwr_expr)

    def add_wire(self, x1, y1, x2, y2):
        wire_expr = f"""  (wire (pts (xy {x1+self.dx:.2f} {y1+self.dy:.2f}) (xy {x2+self.dx:.2f} {y2+self.dy:.2f})) (stroke (width 0) (type default)) (uuid "{gen_uuid()}"))"""
        self.output.append(wire_expr)

    def add_junction(self, x, y):
        junc_expr = f"""  (junction (at {x+self.dx:.2f} {y+self.dy:.2f}) (diameter 0) (color 0 0 0 0) (uuid "{gen_uuid()}"))"""
        self.output.append(junc_expr)

    def generate(self):
        # 1. 放置符号
        self.add_symbol("JW_Component:RELAY_AGQ2004H_THT", "K1", 102.87, 46.99, mirror="y", unit=1)
        self.add_symbol("JW_Component:RELAY_AGQ2004H_THT", "K1", 109.22, 82.55, mirror="x", unit=2)
        self.add_symbol("JW_Component:RELAY_AGQ2004H_THT", "K1", 109.22, 68.58, mirror="x", unit=3)
        self.add_symbol("JW_Component:RELAY_AGQ2004H_THT", "K2", 102.87, 34.29, mirror="y", unit=1)
        self.add_symbol("JW_Component:RELAY_AGQ2004H_THT", "K2", 69.85, 80.01, unit=2)
        self.add_symbol("JW_Component:RELAY_AGQ2004H_THT", "K2", 69.85, 66.04, unit=3)
        self.add_symbol("JW_Component:DIODE_10L45A (Altium Display 1)", "D1", 93.98, 26.67, unit=1)
        self.add_symbol("JW_Component:DIODE_10L45A (Altium Display 1)", "D2", 93.98, 39.37, unit=1)
        self.add_symbol("JW_Component:MMBD4148SE", "D128_S", 168.91, 63.5, angle=90, unit=1)
        self.add_symbol("JW_Component:R_SM_0805_2", "R1", 148.59, 60.96, unit=1)

        # 2. 放置网络接口
        self.add_label("S34_CBit1", "input", 77.47, 26.67, angle=180)
        self.add_label("S34_CBit1", "input", 77.47, 39.37, angle=180)
        self.add_label("5V", "input", 115.57, 26.67, angle=0)
        self.add_label("Socket_F", "input", 64.77, 66.04, angle=180)
        self.add_label("Socket_S", "input", 66.04, 80.01, angle=180)
        self.add_label("ATE_F", "output", 143.51, 66.04, angle=0)
        self.add_label("ATE_S", "output", 143.51, 73.66, angle=0)
        self.add_power_label("FL", 140.97, 85.09, angle=90)

        # 3. 连线拓扑
        wires = [
            (110.49, 34.29, 102.87, 34.29), (110.49, 39.37, 110.49, 46.99), 
            (64.77, 66.04, 69.85, 66.04), (97.79, 39.37, 110.49, 39.37), 
            (134.62, 80.01, 138.43, 80.01), (97.79, 26.67, 110.49, 26.67), 
            (110.49, 26.67, 115.57, 26.67), (77.47, 39.37, 82.55, 39.37), 
            (138.43, 73.66, 138.43, 80.01), (87.63, 34.29, 82.55, 34.29), 
            (138.43, 60.96, 138.43, 66.04), (82.55, 39.37, 82.55, 46.99), 
            (138.43, 71.12, 138.43, 73.66), (143.51, 73.66, 138.43, 73.66), 
            (134.62, 71.12, 138.43, 71.12), (82.55, 34.29, 82.55, 26.67), 
            (110.49, 34.29, 110.49, 39.37), (95.25, 68.58, 104.14, 68.58), 
            (110.49, 26.67, 110.49, 34.29), (95.25, 82.55, 104.14, 82.55), 
            (90.17, 39.37, 82.55, 39.37), (138.43, 60.96, 104.14, 60.96), 
            (110.49, 46.99, 102.87, 46.99), (104.14, 68.58, 109.22, 68.58), 
            (153.67, 60.96, 158.75, 60.96), (66.04, 80.01, 69.85, 80.01), 
            (138.43, 66.04, 143.51, 66.04), (104.14, 82.55, 109.22, 82.55), 
            (82.55, 26.67, 90.17, 26.67), (134.62, 66.04, 138.43, 66.04), 
            (77.47, 26.67, 82.55, 26.67), (104.14, 60.96, 104.14, 68.58), 
            (104.14, 82.55, 104.14, 92.71), (134.62, 85.09, 140.97, 85.09), 
            (82.55, 46.99, 87.63, 46.99), (173.99, 92.71, 173.99, 63.5), 
            (104.14, 92.71, 173.99, 92.71), (173.99, 63.5, 173.99, 57.15), 
            (173.99, 57.15, 171.45, 57.15), (173.99, 63.5, 171.45, 63.5),
            
            # 【修复项】：补充 R201 左侧缺失的这根导线！
            (138.43, 60.96, 143.51, 60.96)
        ]
        for w in wires:
            self.add_wire(w[0], w[1], w[2], w[3])

        # 4. 放置节点
        juncs = [
            (110.49, 26.67), (110.49, 39.37), (110.49, 34.29), (138.43, 66.04), 
            (104.14, 82.55), (138.43, 73.66), (104.14, 68.58), (82.55, 39.37), 
            (82.55, 26.67), (173.99, 63.5), (138.43, 60.96)
        ]
        for j in juncs:
            self.add_junction(j[0], j[1])

        return "\n".join(self.output)

def create_project():
    master_sheet_uuid = gen_uuid()
    
    # 实例化通道 1，并设置后缀名为 "S1"
    net_map_ch1 = { "Socket_F": "CH1_F", "Socket_S": "CH1_S", "ATE_F": "DPS1_F", "ATE_S": "DPS1_S", "S34_CBit1": "RLY_CTRL_1" }
    mod1 = KelvinModuleBuilder(ch_index=1, sheet_uuid=master_sheet_uuid, sheet_id="S1", offset_x=0, offset_y=0, net_map=net_map_ch1)
    
    # 实例化通道 2，也设置后缀名为 "S1" (它们在同一张图纸上)
    net_map_ch2 = { "Socket_F": "CH2_F", "Socket_S": "CH2_S", "ATE_F": "DPS2_F", "ATE_S": "DPS2_S", "S34_CBit1": "RLY_CTRL_2" }
    mod2 = KelvinModuleBuilder(ch_index=2, sheet_uuid=master_sheet_uuid, sheet_id="S1", offset_x=0, offset_y=80, net_map=net_map_ch2)

    kicad_sch_content = f"""(kicad_sch
  (version 20250114)
  (generator "eeschema")
  (generator_version "9.0")
  (uuid "{master_sheet_uuid}") 
  (paper "A4")
  {LIB_SYMBOLS_BLOCK}
  {mod1.generate()}
  {mod2.generate()}
  (sheet_instances (path "/" (page "1")))
)"""

    output_filename = "Kelvin_Ultimate_Fix.kicad_sch"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(kicad_sch_content)
    print(f"✅ 生成成功！请查看修复后的文件: {os.path.abspath(output_filename)}")

if __name__ == "__main__":
    create_project()