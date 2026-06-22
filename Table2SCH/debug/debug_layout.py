import uuid
import re

# -------------------------------------------------------------------
# 1. 定义你的 KelvinModule 类 (与之前一致，略作精简以突出核心逻辑)
# -------------------------------------------------------------------
class KelvinModule:
    def __init__(self, channel_index, socket_f, socket_s, ate_f, ate_s, fl="FL", ctrl_net="S34_CBit1", pwr_net="5V"):
        self.channel_index = channel_index
        self.net_mapping = {
            "Socket_F": socket_f, "Socket_S": socket_s, 
            "ATE_F": ate_f, "ATE_S": ate_s, 
            "FL": fl, "S34_CBit1": ctrl_net, "5V": pwr_net
        }
        self.ref_mapping = {
            "K1": f"K{channel_index}_1", "K2": f"K{channel_index}_2",
            "D1": f"D{channel_index}_1", "D2": f"D{channel_index}_2",
            "R1": f"R{channel_index}_1", "D128_S1": f"D128_S{channel_index}"
        }

        # 注意：这里只放入连线(wire)、节点(junction)、全局标签(global_label)和符号实例化(symbol)
        # 不要把 (kicad_sch ...) 和 (lib_symbols ...) 放在这里！
        self.raw_sch_template = """
        (junction (at 138.43 73.66) (diameter 0) (color 0 0 0 0) (uuid "28135d7b-38a1-4e24-b16d-a0c2a3eb9ab2"))
        (wire (pts (xy 82.55 39.37) (xy 82.55 46.99)) (stroke (width 0) (type default)) (uuid "056ef137-128f-4ec8-bbc3-7ac15fd1a0cd"))
        (global_label "Socket_F" (shape input) (at 64.77 66.04 180) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify right)) (uuid "83b66d63-651a-47a0-905b-0a23dc533ee5"))
        (symbol (lib_id "JW_Component:R_SM_0805_2") (at 148.59 60.96 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced yes) (uuid "0fc6b23a-be1b-4c70-b37f-0d875eacae64")
            (property "Reference" "R1" (at 148.59 53.34 0) (effects (font (size 1.8288 1.8288))))
        )
        ;; ... [此处省略了大量中间坐标信息，实际测试时请把你那段代码的内部组件全部粘贴于此] ...
        """

    def generate(self, offset_x=0.0, offset_y=0.0):
        text = self.raw_sch_template
        
        # 1. 替换网络和位号
        for old_net, new_net in self.net_mapping.items():
            text = text.replace(f'"{old_net}"', f'"{new_net}"')
        for old_ref, new_ref in self.ref_mapping.items():
            text = text.replace(f'"{old_ref}"', f'"{new_ref}"')

        # 2. 正则偏移坐标
        def shift_at(m):
            x, y = float(m.group(1)), float(m.group(2))
            rest = m.group(3) if m.group(3) else ""
            return f"(at {x + offset_x:.2f} {y + offset_y:.2f}{rest})"

        def shift_xy(m):
            x, y = float(m.group(1)), float(m.group(2))
            return f"(xy {x + offset_x:.2f} {y + offset_y:.2f})"

        text = re.sub(r'\(at\s+([-\d.]+)\s+([-\d.]+)(.*?)\)', shift_at, text)
        text = re.sub(r'\(xy\s+([-\d.]+)\s+([-\d.]+)\)', shift_xy, text)

        # 3. 刷新 UUID
        text = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', 
                      lambda m: str(uuid.uuid4()), text)
        return text

# -------------------------------------------------------------------
# 2. 组装 KiCad 原理图文件
# -------------------------------------------------------------------
def build_test_schematic():
    # 文件头：包含版本信息和依赖的符号库 (lib_symbols)
    # 在你的 table2sch 模块中，这部分应该是全局共享的
    kicad_header = f"""(kicad_sch
    (version 20250114)
    (generator "eeschema")
    (generator_version "9.0")
    (uuid "{uuid.uuid4()}")
    (paper "A4")
    (lib_symbols
        ;; 测试时可保持为空，或填入你之前的 (symbol "JW_Component:DIODE_10L45A..." ) 等库定义
    )
    """

    # 实例化通道 1 (无偏移)
    ch1 = KelvinModule(
        channel_index=1,
        socket_f="CH1_Socket_F", socket_s="CH1_Socket_S",
        ate_f="CH1_ATE_F", ate_s="CH1_ATE_S",
        fl="GND_FL", ctrl_net="CTRL_RLY_1", pwr_net="5V"
    )
    block1 = ch1.generate(offset_x=0, offset_y=0)

    # 实例化通道 2 (向下偏移 80mm)
    ch2 = KelvinModule(
        channel_index=2,
        socket_f="CH2_Socket_F", socket_s="CH2_Socket_S",
        ate_f="CH2_ATE_F", ate_s="CH2_ATE_S",
        fl="GND_FL", ctrl_net="CTRL_RLY_2", pwr_net="5V"
    )
    block2 = ch2.generate(offset_x=0, offset_y=80.0)

    # 文件尾部：必须包含 sheet_instances，否则 KiCad 打开会报错
    kicad_footer = """
    (sheet_instances
        (path "/" (page "1"))
    )
)
    """

    # 组合写入文件
    output_filename = r"C:\Users\11271\Desktop\Table2SCH\debug\debug_kelvin_array.kicad_sch" 
    # 注意前面的 r 不要漏掉，防止 \ 符号被转义
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(kicad_header)
        f.write(block1)
        f.write(block2)
        f.write(kicad_footer)
    
    print(f"✅ 生成成功！请使用 KiCad 8/9 打开 {output_filename} 查看效果。")

if __name__ == "__main__":
    build_test_schematic()