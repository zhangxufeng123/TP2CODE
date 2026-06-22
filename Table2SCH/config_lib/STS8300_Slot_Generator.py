import pandas as pd
from skidl import *

class TIBInterface:
    def __init__(self, excel_path, lib_name='ATE_Library'):
        # 1. 加载 Excel 映射表
        self.df = pd.read_excel(excel_path)
        self.pogo_parts = {}    # 存储 P101-P124 实例
        self.resource_map = {}  # 存储 (Slot, Resource) -> Pin 的映射

        # 2. 遍历 Excel 行，自动例化并赋名
        for _, row in self.df.iterrows():
            ref = row['Pogo_Ref']       # 如 P101
            pin_num = str(row['Pin_Num']) # 如 A2
            net_name = row['Full_Net_Name'] # 如 S5_ACM200_FH0
            slot = row['Slot']          # 如 5
            res_func = row['Resource']   # 如 FH0

            # 如果该 Pogo 块还未例化，则在 skidl 中创建它
            if ref not in self.pogo_parts:
                # 使用你转化好的 kicad_sym 库中的 POGO_BLOCK
                self.pogo_parts[ref] = Part(lib_name, 'POGO_BLOCK', ref=ref)

            # 获取具体的引脚对象
            pin_obj = self.pogo_parts[ref][pin_num]

            # --- 引脚赋名 (即连接到命名网络) ---
            # skidl 会自动合并同名网络，从而处理跨 Pogo 的连接
            target_net = Net(net_name)
            pin_obj += target_net

            # 3. 建立逻辑索引，方便后续通过 Slot 查找
            # 将引脚对象存入字典，Key 为 (槽位, 资源名)
            self.resource_map[(str(slot), res_func)] = pin_obj

    def get_pin(self, slot, resource):
        """核心接口：通过 Slot 和资源名直接拿引脚"""
        return self.resource_map.get((str(slot), resource))

# ==============================
# 2. 如何在 tp2code 中调用？
# ==============================

# 初始化整个 TIB 电路对象
tib = TIBInterface("TIB_Pogo_Resource_Mapping.xlsx")

# 示例：我们要把 Slot 5 的 FH0 连到一个继电器
pogo_pin = tib.get_pin(slot=5, resource='FH0')

if pogo_pin:
    # 就像在 AD 里连线一样简单
    relay = Part('device', 'Relay_SPST', ref='K_CH1')
    pogo_pin += relay[1] 
    print(f"已成功将 {pogo_pin.nets[0].name} 连接至继电器 K_CH1")