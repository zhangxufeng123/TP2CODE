# filepath: src/hw_modules/opa189.py
from .base_template_module import TemplateHWModule

class OPA189Module(TemplateHWModule):
    
    @classmethod
    def get_module_name(cls):
        return "OPA189"

    @classmethod
    def process(cls, ctx, res_manager, grouped_modules):
        if cls.get_module_name() not in (ctx.pin_data.active_circuits or []):
            return

        sheet_id = ctx.sheet_id
        group_id = ctx.params.get("GROUP_ID", None)
        
        # 组网逻辑
        shared_bus_net = f"BUS_OPA189_{group_id}_{sheet_id}" if group_id else f"IN_{ctx.logical_net}_{sheet_id}"
        
        # MUX 继电器部分
        if ctx.mux_eng_exists:
            k_mux = res_manager.relay.get_switch(f"MUX_{group_id}" if group_id else None)
            mux_reps = {
                "@K1@": k_mux, "@D1@": res_manager.comp.get_next("D"),
                "@Input@": ctx.primary_socket_net, "@SHARED_BUS@": shared_bus_net,
                "@5V@": ctx.sys_5v
            }
            grouped_modules["Relay_MUX_Shared"].append(mux_reps)

        # 检查是否是同一组，避免重复放置实体运放
        unique_key = f"OPA189_{group_id}" if group_id else f"OPA189_PIN_{ctx.clean_pin}"
        if unique_key in ctx.placed_shared_groups:
            return
        ctx.placed_shared_groups.add(unique_key)

        # 申请器件编号
        u_val = res_manager.comp.get_next("U")
        r_vals = res_manager.comp.get_next("R", count=4)
        c_vals = res_manager.comp.get_next("C", count=4)
        d_val = res_manager.comp.get_next("D")
        k_int = res_manager.relay.get_switch()

        opa189_reps = {
            "U1": u_val, '"@U25_S1@"': f'"{u_val}"',
            "@K1@": k_int, "@D1@": d_val,
            "@R1@": r_vals[0], '"R67_S1"': f'"{r_vals[0]}"',
            "@R2@": r_vals[1], '"R68_S1"': f'"{r_vals[1]}"',
            "@R3@": r_vals[2], '"@R3@"': f'"{r_vals[2]}"',
            "@R4@": r_vals[3], '"@R4@"': f'"{r_vals[3]}"',
            "@C1@": c_vals[0], '"C44_S1"': f'"{c_vals[0]}"',
            "@C2@": c_vals[1], '"C45_S1"': f'"{c_vals[1]}"',
            "@C3@": c_vals[2], '"@C3@"': f'"{c_vals[2]}"',
            "@C4@": c_vals[3], '"@C4@"': f'"{c_vals[3]}"',
            "@FL@": ctx.fl_net, '"GNDREF"': f'"{ctx.fl_net}"', '"AGND"': f'"{ctx.fl_net}"',
            '"GND3"': f'"{ctx.fl_net}"', '"GND"': f'"{ctx.fl_net}"',
            "@5V@": ctx.sys_5v, "@+15V@": f"+15V_{sheet_id}", "@-15V@": f"-15V_{sheet_id}", "@+3.3V@": f"+3.3V_{sheet_id}",
            "@IN@": shared_bus_net, "@INPUT@": shared_bus_net,
            "@IINPUT@": shared_bus_net, "@IINPUT+@": shared_bus_net, "@INPUT+@": shared_bus_net,
            "@OUT@": f"OUT_{group_id}_{sheet_id}" if group_id else f"OUT_{ctx.logical_net}_{sheet_id}",
            "@OUTPUT@": f"OUT_{group_id}_{sheet_id}" if group_id else f"OUT_{ctx.logical_net}_{sheet_id}",
        }
        grouped_modules[cls.get_module_name()].append(opa189_reps)