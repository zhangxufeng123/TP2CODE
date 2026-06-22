# filepath: src/hw_modules/instrument_router.py
import re
from .base_template_module import TemplateHWModule
from core.net_naming import NetNamingManager

class InstrumentRouter(TemplateHWModule):
    @classmethod
    def get_module_name(cls):
        return "InstrumentRouter"

    @classmethod
    def process(cls, ctx, res_manager, grouped_modules):
        resources = [ctx.pin_data.resource_type] if ctx.pin_data.resource_type else []
        if not resources: return

        group_id = ctx.params.get("GROUP_ID", None)
        qtmu_params = ctx.params.get("QTMUe", {})
        qtmu_group = qtmu_params.get("GROUP_ID", "")
        qtmu_path = "A" if "A" in qtmu_params.get("QTMU_PATH", "A").upper() else "B"

        resource_nets = []
        main_res = None
        
        # 确定主资源
        for r in resources:
            if "QTMU" not in r.upper() and not main_res: main_res = r
        if not main_res and resources: main_res = resources[0]

        ordered_resources = []
        if main_res: ordered_resources.append(main_res)
        for r in resources:
            if r != main_res: ordered_resources.append(r)

        # 提取通道和网络名
        for r in ordered_resources:
            raw_net = ctx.chan_map.get(r, "NC_CH0")
            
            # =========================================================
            # 🌟 FIX 1: 完美继承 Scheduler 的分配，不再暴力覆盖通道号！
            # =========================================================
            if "QTMU" in r.upper():
                m = re.match(r'(S\d+_CH\d+)', raw_net)
                if m:
                    base_chan = m.group(1)
                    raw_net = f"{base_chan}_{qtmu_path}"
                else:
                    raw_net = f"{raw_net}_{qtmu_path}"
                    
                if qtmu_group:
                    bus_net = f"QTMU_BUS_{qtmu_group}_{qtmu_path}_{ctx.sheet_id}"
                    if bus_net not in ctx.placed_qtmu_buses:
                        grouped_modules["Hardwire"].append({"SOCKET_NET": bus_net, "ATE_NET": raw_net})
                        ctx.placed_qtmu_buses.add(bus_net)
                    raw_net = bus_net 
            
            resource_nets.append({"name": r, "net": raw_net})

        if resource_nets:
            ctx.fallback_ate_f = resource_nets[0]["net"] 
            main_r = resource_nets[0]
            other_rs = resource_nets[1:] 
            main_ate_net = main_r["net"]
            KELVIN_INSTRUMENTS = ["ACM", "FPVI", "FXVI", "DPS", "HPSM"]
            is_main_kelvin = any(k in main_r["name"].upper() for k in KELVIN_INSTRUMENTS)
            effective_connect_type = ctx.pin_data.connect_type if ctx.pin_data.connect_type in ["Direct", "Relay", "Kelvin"] else "Direct"

            if effective_connect_type == "Kelvin":
                k_1 = res_manager.relay.get_pair()
                k_2 = res_manager.relay.get_pair()
                ate_f_pogo, ate_s_pogo = NetNamingManager.get_fh_sh_nets(main_ate_net)
                d_vals = res_manager.comp.get_next("D", 3)
                reps = {
                    "@K1@": k_1, 
                    "@K2@": k_2, 
                    "@D1@": d_vals[0], "@D2@": d_vals[1], "@D3@": d_vals[2], 
                    "@R1@": res_manager.comp.get_next("R"), 
                    "@Socket_F@": f"{ctx.base_net}_F_{ctx.sheet_id}", "@Socket_S@": f"{ctx.base_net}_S_{ctx.sheet_id}",   
                    "@ATE_F@": ate_f_pogo, "@ATE_S@": ate_s_pogo, 
                    "@5V@": ctx.sys_5v, "@FL@": ctx.fl_net
                }
                grouped_modules["Kelvin"].append(reps)
            
            else:
                has_dcm = any("DCM" in r["name"].upper() for r in resource_nets)
                has_ana = any(k in r["name"].upper() for r in resource_nets for k in KELVIN_INSTRUMENTS)

                if has_dcm and has_ana and len(resource_nets) == 2:
                    ana_r = next(r for r in resource_nets if "DCM" not in r["name"].upper())
                    dig_r = next(r for r in resource_nets if "DCM" in r["name"].upper())

                    ana_net = ana_r["net"]
                    dig_net = dig_r["net"]

                    if not group_id:
                        if "SDA" in ctx.logical_net.upper() or "SCL" in ctx.logical_net.upper():
                            grp = f"AUTO_I2C_MUX_{ctx.sheet_id}"
                        else:
                            grp = f"MUX_{ctx.clean_pin}_{ctx.sheet_id}"
                    else:
                        grp = group_id

                    relay_ref = res_manager.relay.get_switch(grp)

                    reps = {
                        "@K1@": relay_ref, 
                        "@D1@": res_manager.comp.get_next("D"),
                        "@PIN_NET@": ctx.primary_socket_net,  
                        "@ANA_NET@": ana_net,                 
                        "@DIG_NET@": dig_net,                 
                        "@COM@": ctx.primary_socket_net,
                        "@NC@": ana_net,
                        "@NO@": dig_net,
                        "@Input@": ctx.primary_socket_net, 
                        "@SHARED_BUS@": dig_net,
                        "@5V@": ctx.sys_5v
                    }
                    grouped_modules["Relay_MUX_Shared"].append(reps)

                    if any(k in ana_r["name"].upper() for k in KELVIN_INSTRUMENTS):
                        of, os = NetNamingManager.get_fh_sh_nets(ana_net)
                        grouped_modules["FH_SH_Shorts"].append({"FH": of, "SH": os, "CH": ana_net})

                else:
                    current_com = ctx.primary_socket_net
                    for i, r_info in enumerate(other_rs):
                        no_net = r_info["net"] 
                        if i < len(other_rs) - 1:
                            nc_net = f"CASCADE_{ctx.clean_pin}_NODE{i+1}_{ctx.sheet_id}"
                        else:
                            nc_net = main_ate_net if effective_connect_type == "Direct" else f"CASCADE_{ctx.clean_pin}_MAIN_{ctx.sheet_id}"

                        grp = None
                        # =========================================================
                        # 🌟 FIX 2: 加入 _L{i} (Layer标识)，防止不同深度的级联引脚错误合体！
                        # =========================================================
                        if "QTMU" in r_info["name"].upper() and qtmu_group: 
                            grp = f"QTMU_{qtmu_group}_L{i}"
                        elif group_id: 
                            grp = f"CASCADE_{r_info['name']}_{group_id}_L{i}"
                            
                        reps = {
                            "@K1@": res_manager.relay.get_switch(grp), 
                            "@D1@": res_manager.comp.get_next("D"),
                            "@PIN_NET@": current_com,
                            "@ANA_NET@": nc_net,
                            "@DIG_NET@": no_net,
                            "@COM@": current_com, "@NO@": no_net, "@NC@": nc_net,
                            "@Input@": current_com, "@SHARED_BUS@": no_net,
                            "@5V@": ctx.sys_5v
                        }
                        grouped_modules["Relay_MUX_Shared"].append(reps)
                        current_com = nc_net 

                        if any(k in r_info["name"].upper() for k in KELVIN_INSTRUMENTS):
                            of, os = NetNamingManager.get_fh_sh_nets(no_net)
                            grouped_modules["FH_SH_Shorts"].append({"FH": of, "SH": os, "CH": no_net})

                    if effective_connect_type == "Direct":
                        if len(other_rs) == 0:
                            grouped_modules["Hardwire"].append({"SOCKET_NET": current_com, "ATE_NET": main_ate_net})
                    elif effective_connect_type == "Relay":
                        nc_net_main = f"NC_MAIN_{ctx.clean_pin}_{ctx.sheet_id}"
                        reps = {
                            "@K1@": res_manager.relay.get_switch(f"MAIN_{group_id}" if group_id else None), 
                            "@D1@": res_manager.comp.get_next("D"),
                            "@PIN_NET@": current_com,
                            "@ANA_NET@": nc_net_main,       
                            "@DIG_NET@": main_ate_net,      
                            "@COM@": current_com, "@NO@": main_ate_net, "@NC@": nc_net_main, 
                            "@Input@": current_com, "@SHARED_BUS@": main_ate_net,
                            "@5V@": ctx.sys_5v
                        }
                        grouped_modules["Relay_Direct"].append(reps)

                if not (has_dcm and has_ana and len(resource_nets) == 2):
                    if is_main_kelvin:
                        mf, ms = NetNamingManager.get_fh_sh_nets(main_ate_net)
                        grouped_modules["FH_SH_Shorts"].append({"FH": mf, "SH": ms, "CH": main_ate_net})