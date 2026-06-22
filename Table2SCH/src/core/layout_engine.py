# filepath: src/core/layout_engine.py
import uuid

class LayoutEngine:
    DEFAULT_CONFIG = {
        "Kelvin": {
            "title": "Kelvin Relays Zone (开尔文连接区)", 
            "spacing_x": 220.0, "spacing_y": 75.0, "items_per_col": 10,
            "offset_x": 0.0, "offset_y": 0.0
        },
        "ChargeRelease": {
            "title": "Charge Release Zone (放电电路区)",
            "spacing_x": 100.0, "spacing_y": 60.0, "items_per_col": 10,
            "offset_x": -90.0, "offset_y": -80.0
        },
        "Relay_Direct": {  
            "title": "Relay Mode Zone (单通道继电器区)",
            "spacing_x": 100.0, "spacing_y": 50.0, "items_per_col": 10,
            "offset_x": -20.0, "offset_y": 0.0
        },
        "Relay_MUX_Shared": {  
            "title": "MUX Relays Zone (QTMU / 模块复用切换区)",
            "spacing_x": 130.0, "spacing_y": 30.0, "items_per_col": 10,
            "offset_x": 50.0, "offset_y": -20.0,
            "title_offset_x": 50.0 
        },
        "FH_SH_Shorts": {
            "title": "Direct Mode Shorts (直连强制短接区)",
            "spacing_x": 110.0, "spacing_y": 20.0, "items_per_col": 30,
            "offset_x": 50.0, "offset_y": 0.0
        },
        "Hardwire": {
            "title": "Hardwire Direct Zone (纯导线直连区)",
            "spacing_x": 80.0, "spacing_y": 15.0, "items_per_col": 30,
            "offset_x": 40.0, "offset_y": 0.0
        },
        "Relay_Coils": {
            "title": "Relay Coils Matrix (继电器线圈控制阵列)",
            "spacing_x": 80.0, "spacing_y": 30.0, "items_per_col": 15,
            "offset_x": -160.0, "offset_y": -80.0
        },
        "BUF634A_SOP8": {
            "title": "BUF634A Buffer Zone (高速缓冲器区)",
            "spacing_x": 230.0, "spacing_y": 110.0, "items_per_col": 8,
            "offset_x": 0.0, "offset_y": 0.0
        },
        "OPA145_INA141": {
            "title": "OPA145 + INA141 Zone (仪表放大器区)",
            "spacing_x": 300.0, "spacing_y": 150.0, "items_per_col": 4,
            "offset_x": -290.0, "offset_y": -80.0
        },
        "OPA189": {
            "title": "OPA189 OpAmp Zone (运放区)",
            "spacing_x": 180.0, "spacing_y": 65.0, "items_per_col": 8,
            "offset_x": -100.0, "offset_y": -50.0
        },
        "SN74LVC2G17DBVR": {
            "title": "SN74 Schmitt Trigger Zone (施密特触发器区)",
            "spacing_x": 180.0, "spacing_y": 60.0, "items_per_col": 8,
            "offset_x": -290.0, "offset_y": -180.0
        },
        "TPS78401DRVR_3.3V": {
            "title": "TPS78401 LDO Zone (LDO电源区)",
            "spacing_x": 180.0, "spacing_y": 75.0, "items_per_col": 8,
            "offset_x": -270.0, "offset_y": -200.0
        },
        "Ground_Ties": { 
            "title": "Instrument Ground Ties (仪器FL/SL接地汇流区)",
            "spacing_x": 130.0, "spacing_y": 15.0, "items_per_col": 30,
            "offset_x": 40.0, "offset_y": 0.0
        },
        # 👇 新增：电阻和电容的专区排版参数
        "Resistor": {
            "title": "Passive Components Zone (电阻网络区)",
            "spacing_x": 100.0, "spacing_y": 30.0, "items_per_col": 15,
            "offset_x": 0.0, "offset_y": 0.0
        },
        "Capacitor": {
            "title": "Decoupling/Filter Caps (滤波电容区)",
            "spacing_x": 100.0, "spacing_y": 30.0, "items_per_col": 15,
            "offset_x": 50.0, "offset_y": 0.0
        },
    }

    @staticmethod
    def render_site(grouped_modules, engines, layout_config, root_uuid, s_uuid, proj_name):
        site_content = ""
        MAX_SHEET_WIDTH = 1900.0   
        zone_margin_x = 120.0      
        zone_margin_y = 120.0      
        current_zone_x = 350.0     
        current_zone_y = 50.0      
        max_height_in_current_row = 0.0 
        
        active_config = layout_config if layout_config else LayoutEngine.DEFAULT_CONFIG
        
        for cat_name, items in grouped_modules.items():
            if not items: continue
            
            # 排除纯代码渲染的模块 (不需要模板引擎)
            if cat_name not in ["FH_SH_Shorts", "Hardwire", "Ground_Ties"]:
                eng = engines.get(cat_name)
                if not eng: 
                    print(f"⚠️ 警告: 找不到 '{cat_name}' 模板文件！已跳过！")
                    continue
            
            cfg = active_config.get(cat_name, {"title": f"{cat_name} Zone", "spacing_x": 250.0, "spacing_y": 100.0, "items_per_col": 10, "offset_x": 0.0, "offset_y": 0.0})
            
            title_text = cfg["title"]
            spacing_x = cfg["spacing_x"]
            spacing_y = cfg["spacing_y"]
            items_per_col = cfg["items_per_col"]
            t_off_x = cfg.get("offset_x", 0.0)  
            t_off_y = cfg.get("offset_y", 0.0)  
            title_off_x = cfg.get("title_offset_x", 0.0)

            grid_items = [r for r in items if "_FLOAT_LEFT" not in r]
            float_items = [r for r in items if "_FLOAT_LEFT" in r]

            num_cols = (len(grid_items) - 1) // items_per_col + 1 if grid_items else 1
            zone_width = num_cols * spacing_x
            
            MIN_ZONE_WIDTH = 200.0  
            if zone_width < MIN_ZONE_WIDTH: zone_width = MIN_ZONE_WIDTH
            
            if current_zone_x + zone_width > MAX_SHEET_WIDTH and current_zone_x > 350.0:
                current_zone_x = 350.0
                current_zone_y += max_height_in_current_row + zone_margin_y
                max_height_in_current_row = 0.0
            
            title_uuid = str(uuid.uuid4())
            site_content += f'\n  (text "{title_text}" (at {current_zone_x + title_off_x} {current_zone_y - 15.0} 0) (effects (font (size 8 8) (thickness 1.0)) (justify left bottom)) (uuid "{title_uuid}"))'

            zone_max_y = 0.0
            
            for float_reps in float_items:
                float_dist_x = float_reps.pop("_FLOAT_LEFT", 0.0)
                float_dist_y = float_reps.pop("_FLOAT_DY", 0.0)
                ox = current_zone_x + t_off_x - float_dist_x
                oy = current_zone_y + t_off_y + float_dist_y
                
                used_eng = eng
                if "_TEMPLATE_OVERRIDE" in float_reps:
                    override_name = float_reps.pop("_TEMPLATE_OVERRIDE")
                    if engines.get(override_name): 
                        used_eng = engines[override_name]
                
                safe_float_reps = {k: str(v) for k, v in float_reps.items()}
                site_content += "\n" + used_eng.stamp(root_uuid, s_uuid, proj_name, ox, oy, safe_float_reps)

            for item_idx, reps in enumerate(grid_items):
                col = item_idx // items_per_col
                row = item_idx % items_per_col
                ox = current_zone_x + col * spacing_x + t_off_x
                oy = current_zone_y + row * spacing_y + t_off_y
                
                if (row + 1) * spacing_y > zone_max_y: zone_max_y = (row + 1) * spacing_y
                
                if cat_name == "FH_SH_Shorts":
                    fh, sh, ch = reps["FH"], reps["SH"], reps.get("CH", reps["FH"]+"_CH")
                    uid1, uid2, uid3, uid4, uid5, uid6, uid7, uid8 = [str(uuid.uuid4()) for _ in range(8)]
                    
                    site_content += f"""
  (global_label "{fh}" (shape bidirectional) (at {ox} {oy} 180) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify right)) (uuid "{uid1}"))
  (global_label "{sh}" (shape bidirectional) (at {ox} {oy+5.08} 180) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify right)) (uuid "{uid2}"))
  (global_label "{ch}" (shape bidirectional) (at {ox+15.24} {oy+2.54} 0) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify left)) (uuid "{uid3}"))
  (wire (pts (xy {ox} {oy}) (xy {ox+7.62} {oy})) (stroke (width 0) (type default)) (uuid "{uid4}"))
  (wire (pts (xy {ox} {oy+5.08}) (xy {ox+7.62} {oy+5.08})) (stroke (width 0) (type default)) (uuid "{uid5}"))
  (wire (pts (xy {ox+7.62} {oy}) (xy {ox+7.62} {oy+5.08})) (stroke (width 0) (type default)) (uuid "{uid6}"))
  (wire (pts (xy {ox+7.62} {oy+2.54}) (xy {ox+15.24} {oy+2.54})) (stroke (width 0) (type default)) (uuid "{uid7}"))
  (junction (at {ox+7.62} {oy+2.54}) (diameter 0) (color 0 0 0 0) (uuid "{uid8}"))"""
                
                elif cat_name == "Hardwire":
                    sock_net, ate_net = reps["SOCKET_NET"], reps["ATE_NET"]
                    uid1, uid2, uid3 = [str(uuid.uuid4()) for _ in range(3)]
                    site_content += f"""
  (global_label "{sock_net}" (shape input) (at {ox} {oy} 180) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify right)) (uuid "{uid1}"))
  (global_label "{ate_net}" (shape bidirectional) (at {ox+15.24} {oy} 0) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify left)) (uuid "{uid2}"))
  (wire (pts (xy {ox} {oy}) (xy {ox+15.24} {oy})) (stroke (width 0) (type default)) (uuid "{uid3}"))"""
                
                # 🌟 用纯导线短接法生成接地图，绝对不闪退
                elif cat_name == "Ground_Ties":
                    net = reps["NET"]
                    # 智能提取 Sheet 后缀 (比如 S1_ACM200_FL(0-11) 提取出 S1)
                    extracted_sheet_id = net.split('_')[0] if '_' in net else "S1"
                    
                    uid1, uid2, uid3 = [str(uuid.uuid4()) for _ in range(3)]
                    
                    site_content += f"""
  (global_label "{net}" (shape bidirectional) (at {ox} {oy} 180) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify right)) (uuid "{uid1}"))
  (global_label "FL_{extracted_sheet_id}" (shape bidirectional) (at {ox+15.24} {oy} 0) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify left)) (uuid "{uid2}"))
  (wire (pts (xy {ox} {oy}) (xy {ox+15.24} {oy})) (stroke (width 0) (type default)) (uuid "{uid3}"))"""
                
                else:
                    used_eng = eng
                    if "_TEMPLATE_OVERRIDE" in reps:
                        override_name = reps.pop("_TEMPLATE_OVERRIDE")
                        if engines.get(override_name): 
                            used_eng = engines[override_name]
                    
                    safe_reps = {k: str(v) for k, v in reps.items()}
                    site_content += "\n" + used_eng.stamp(root_uuid, s_uuid, proj_name, ox, oy, safe_reps)
            
            if zone_max_y > max_height_in_current_row:
                max_height_in_current_row = zone_max_y
            current_zone_x += zone_width + zone_margin_x

        # 🔧 重要修复：生成被动元件并添加到原理图内容中
        # try:
        #     passives_content = LayoutEngine.render_passive_components(grouped_modules, engines, None, site_index, root_uuid, s_uuid, proj_name=proj_name)
        #     if passives_content:
        #         site_content += "\n" + passives_content
        # except Exception as e:
        #     print(f"⚠️ 被动元件生成失败 (将跳过): {e}")

        return site_content

    @staticmethod
    def render_passive_components(grouped_modules, engines, config, site_index, root_uuid, s_uuid, offset_x=50, offset_y=150, proj_name="STS8300_LB_RevA_Master"):
        """生成被动元件（电容等）"""
        passives_content = ""
        x_pos, y_pos = offset_x, offset_y

        print(f"🎯 被动元件生成器被调用: 站点 {site_index}")

        # 检查是否有电容模板引擎
        capacitor_eng = engines.get("Capacitor")
        if not capacitor_eng:
            print(f"⚠️ 警告: 未找到电容模板引擎，将跳过电容生成")
            print(f"  可用引擎: {list(engines.keys())}")
            return ""
        else:
            print(f"✅ 找到电容模板引擎")

        # 从 grouped_modules 中获取被动元件数据
        site_passives = grouped_modules.get("Capacitor", [])
        print(f"📈 站点 {site_index} 总计: {len(site_passives)} 个被动元件")

        for passive_idx, passive in enumerate(site_passives):
            if passive.get("part") == "C":  # 电容
                value = passive.get("value", "100nF")
                pins = passive.get("pins", [])
                print(f"  [{passive_idx+1}] 生成电容: {value} 在 {pins}")

                # 使用电容模板引擎生成电容符号
                if len(pins) >= 2:
                    cap_ref = f"C{site_index * 10 + passive_idx + 1}"

                    print(f"  🎯 使用模板生成电容 {cap_ref}: 值={value}, 引脚={pins}")

                    # 创建替换字典 - 使用正确的模板格式
                    replace_dict = {
                        "@C1@": cap_ref,
                        "@VALUE@": value,
                        "@Pos_Pin@": pins[0],
                        "@Neg_Pin@": pins[1],
                        "@INTERSHEET_REFS@": ""
                    }

                    try:
                        symbol_content = capacitor_eng.stamp(root_uuid, s_uuid, proj_name, x_pos, y_pos, replace_dict)
                        print(f"    ✅ 电容模板替换成功")
                        passives_content += symbol_content
                    except Exception as e:
                        print(f"    ❌ 电容模板错误: {e}")
                        # 模板失败时使用最简化的符号定义
                        simple_cap = f"""
(symbol (lib_id "JW_Component:CAP_SM_0805_1") (at {x_pos} {y_pos})
  (property "Reference" "{cap_ref}")
  (property "Value" "{value}")
)"""
                        passives_content += simple_cap

                # 增加间距，避免元件重叠
                x_pos += 30
                if x_pos > 400:  # 换行
                    x_pos = offset_x
                    y_pos += 40

        return passives_content