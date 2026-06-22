from skidl import *
import re

# ==========================================
# 辅助工具：电源自动识别
# ==========================================
def get_vcc5_net(ctrl_pin):
    """根据控制引脚的 Slot 自动返回对应的 5V 电源网络"""
    # 从引脚的属性中提取 Slot 编号 (例如从 'S34' 提取 34)
    slot_num = getattr(ctrl_pin, 'slot', '34') 
    return Net(f"S{slot_num}_J+5V")

# ==========================================
# 开关模块 (Relay Modules)
# ==========================================

@subcircuit
def kelvin_switch(f_in, s_in, f_out, s_out, cbit_pin):
    """包含 1N4148 保护的开尔文切换模块"""
    vcc5 = get_vcc5_net(cbit_pin)
    k = Part('ATE_Lib', 'RELAY_3UNIT', ref='K_KELV_')
    d = Part('device', 'D_1N4148', ref='D_')
    
    # 信号路径 (Unit A & C)
    f_in += k['A1']; k['A2'] += f_out
    s_in += k['C1']; k['C2'] += s_out
    
    # 线圈保护 (Unit B)
    vcc5 += k['B1'], d['K']
    cbit_pin += k['B2'], d['A']

@subcircuit
def direct_switch(sig_in, sig_out, cbit_pin):
    """单路直连继电器模块"""
    vcc5 = get_vcc5_net(cbit_pin)
    k = Part('ATE_Lib', 'RELAY_1UNIT', ref='K_DIR_')
    d = Part('device', 'D_1N4148', ref='D_')
    
    sig_in += k[1]; k[2] += sig_out
    vcc5 += k['B1'], d['K']
    cbit_pin += k['B2'], d['A']

# ==========================================
# 有源/无源网络 (Active/Passive Modules)
# ==========================================

@subcircuit
def active_buffer_opa145(sig_in, sig_out, slot_num):
    """有源运放缓冲电路"""
    v_pos = Net(f"S{slot_num}_+15V")
    v_neg = Net(f"S{slot_num}_-15V")
    
    u_opa = Part('ATE_Lib', 'OPA145', ref='U_BUF_')
    c_dec = Part('device', 'C', value='0.1uF', ref='C_')
    
    # 供电与去耦
    u_opa[7, 4] += v_pos, v_neg
    c_dec[1, 2] += v_pos, v_neg
    
    # 信号连接
    sig_in += u_opa[3]
    u_opa[6] += u_opa[2], sig_out

@subcircuit
def passive_pullup(sig_net, vcc_net, res_value='10k'):
    """无源上拉电阻"""
    r = Part('device', 'R', value=res_value, ref='R_PU_')
    sig_net += r[1]
    vcc_net += r[2]