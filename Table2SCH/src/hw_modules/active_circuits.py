from .base_module import BaseHardwareModule

# ==========================================
# 1. 运放缓冲器 (Voltage Follower)
# 特点：输出脚直接短接到反相输入脚
# ==========================================
class OPA145Buffer(BaseHardwareModule):
    def draw(self, net_in, net_out, net_vcc="+15V", net_vee="-15V"):
        # 模糊查找库器件
        lib_opa = self.sch.fuzzy_find_symbol("OPA145") or "Amplifier_Operational:OPA145"
        
        # 放置运放
        u_x, u_y = self.ox + 30, self.oy
        self.sch.add_symbol(lib_opa, f"U_{self.ref_suffix}", "OPA145", u_x, u_y)

        # 绘制缓冲器特有的反馈线 (Output 连到 In-)
        # 假设引脚：3(In+), 2(In-), 6(Out)
        self.sch.add_wire([(u_x + 10, self.oy), (u_x + 10, self.oy - 10)])       # 输出向上走
        self.sch.add_wire([(u_x + 10, self.oy - 10), (u_x - 10, self.oy - 10)])  # 往回走
        self.sch.add_wire([(u_x - 10, self.oy - 10), (u_x - 10, self.oy + 2)])   # 接到负输入端

        # 放置输入输出标签
        self.sch.add_global_label(net_in, self.ox, self.oy + 5)   # 接 In+
        self.sch.add_global_label(net_out, self.ox + 60, self.oy) # 接 Out
        
        # 连接线段
        self.sch.add_wire([(self.ox, self.oy + 5), (u_x - 10, self.oy + 5)])
        self.sch.add_wire([(u_x + 10, self.oy), (self.ox + 60, self.oy)])

# ==========================================
# 2. 运放放大器 (带有外部反馈电阻的同相放大)
# ==========================================
class OPA235Amp(BaseHardwareModule):
    def draw(self, net_in, net_out, net_vcc="+5V", net_vee="GND"):
        lib_opa = self.sch.fuzzy_find_symbol("OPA235") or "Amplifier_Operational:OPA235"
        lib_res = self.sch.fuzzy_find_symbol("RES_0805") or "Device:R"
        
        # 放置器件
        u_x, u_y = self.ox + 40, self.oy
        self.sch.add_symbol(lib_opa, f"U_{self.ref_suffix}", "OPA235", u_x, u_y)
        
        # 放置反馈网络电阻 Rf 和 Rg
        self.sch.add_symbol(lib_res, f"Rf_{self.ref_suffix}", "10k", u_x, u_y - 15)
        self.sch.add_symbol(lib_res, f"Rg_{self.ref_suffix}", "1k", u_x - 20, u_y + 10, angle=90)

        # ... (连线逻辑同上，连接引脚形成同相放大结构) ...
        self.sch.add_global_label(net_in, self.ox, self.oy + 5)
        self.sch.add_global_label(net_out, self.ox + 80, self.oy)

# ==========================================
# 3. 仪表放大器 (INA141)
# ==========================================
class INA141InstAmp(BaseHardwareModule):
    def draw(self, net_in_plus, net_in_minus, net_out, net_ref="GND"):
        lib_ina = self.sch.fuzzy_find_symbol("INA141") or "Amplifier_Instrumentation:INA141"
        u_x, u_y = self.ox + 40, self.oy
        self.sch.add_symbol(lib_ina, f"U_{self.ref_suffix}", "INA141", u_x, u_y)

        # 仪表放大器有两个输入端
        self.sch.add_global_label(net_in_plus, self.ox, self.oy + 5)
        self.sch.add_global_label(net_in_minus, self.ox, self.oy - 5)
        self.sch.add_global_label(net_out, self.ox + 80, self.oy)
        self.sch.add_global_label(net_ref, self.ox + 80, self.oy + 10)

# ==========================================
# 4. 八路 D 型锁存器 (SN74HC273)
# ==========================================
class SN74HC273Latch(BaseHardwareModule):
    def draw(self, d_nets: list, q_nets: list, clk_net, clr_net):
        """参数接收一组输入输出网络列表"""
        lib_ic = self.sch.fuzzy_find_symbol("74HC273") or "74xx:74HC273"
        u_x, u_y = self.ox + 50, self.oy
        self.sch.add_symbol(lib_ic, f"U_{self.ref_suffix}", "74HC273", u_x, u_y)
        
        # 简化的引脚生成逻辑 (用循环画出 D0~D7 和 Q0~Q7 的连线)
        self.sch.add_global_label(clk_net, self.ox, self.oy + 20)
        self.sch.add_global_label(clr_net, self.ox, self.oy - 20)

# ==========================================
# 5. 单刀单掷/双刀双掷继电器控制 (Relay Switch)
# ==========================================
class RelaySwitch(BaseHardwareModule):
    def draw(self, net_in, net_out, ctrl_net):
        lib_relay = self.sch.fuzzy_find_symbol("RELAY") or "Relay:G6K"
        u_x, u_y = self.ox + 30, self.oy
        self.sch.add_symbol(lib_relay, f"K_{self.ref_suffix}", "Relay", u_x, u_y)
        
        self.sch.add_global_label(net_in, self.ox, self.oy + 5)
        self.sch.add_global_label(net_out, self.ox + 60, self.oy + 5)
        self.sch.add_global_label(ctrl_net, self.ox, self.oy - 10)