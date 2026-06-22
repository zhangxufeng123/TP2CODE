# filepath: src/exporters/sch_generator.py
import os
import uuid
import re

from models.schema import Table2SchConfig
from exporters.kicad_api import KiCadTemplateEngine
from core.socket_router import SocketRouter
from core.net_mapper import NetMapper
from core.layout_engine import LayoutEngine


class SchGenerator:

    @staticmethod
    def _merge_lib_symbols(*blocks):
        def split_top_symbols(text):
            items = []
            idx = 0
            while True:
                start = text.find('(symbol "', idx)
                if start == -1: break
                bc = 0
                end = -1
                for i in range(start, len(text)):
                    if text[i] == '(': bc += 1
                    elif text[i] == ')':
                        bc -= 1
                        if bc == 0:
                            end = i + 1
                            break
                if end == -1: break
                blk = text[start:end]
                m = re.match(r'\(symbol\s+"([^"]+)"', blk)
                if m: items.append((m.group(1), blk))
                idx = end
            return items

        seen = {}
        for b in blocks:
            if not b: continue
            b = b.strip()
            if not b.startswith("(lib_symbols"): continue
            start = b.find("(lib_symbols") + len("(lib_symbols")
            end = b.rfind(")")
            if start == -1 or end == -1 or end <= start: continue
            inner = b[start:end].strip()
            for name, blk in split_top_symbols(inner):
                if name not in seen:
                    seen[name] = blk

        merged = "\n".join(seen.values())
        return f"(lib_symbols\n{merged}\n)"

    @staticmethod
    def generate_from_config(config: Table2SchConfig, base_output_dir="projects\\"):
        proj_name = config.project_info.project_name
        total_sites = config.project_info.site_num
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

        proj_dir = os.path.join(base_dir, base_output_dir, proj_name)
        os.makedirs(proj_dir, exist_ok=True)
        tpl_dir = os.path.join(base_dir, "Sch_lib", "templates")

        actual_proj_name = f"{proj_name}_Master"
        root_uuid = str(uuid.uuid4())
        site_uuids = [str(uuid.uuid4()) for _ in range(total_sites)]

        p_src = os.path.join(base_dir, "Sch_lib", "Pogo_Cont", "Pogo_STS8300")
        pogo_sheets = []
        if not os.path.exists(p_src):
            raise FileNotFoundError(f"🚨 找不到 Pogo 模板库目录: {p_src}")

        pogo_files = sorted([f for f in os.listdir(p_src) if f.endswith(".kicad_sch")])
        pogo_start_page = total_sites + 2

        for idx, f in enumerate(pogo_files):
            sheet_uuid = str(uuid.uuid4())
            pogo_sheets.append({"n": f"U_{f.replace('.kicad_sch', '')}", "f": f, "u": sheet_uuid})
            KiCadTemplateEngine.rewrite_external_child_schematic(
                src_filepath=os.path.join(p_src, f), dst_filepath=os.path.join(proj_dir, f),
                project_name=actual_proj_name, root_uuid=root_uuid,
                sheet_instance_uuid=sheet_uuid, child_page=pogo_start_page + idx
            )

        gnd_template_name = f"GND_S{total_sites}.kicad_sch"
        gnd_src_path = os.path.join(tpl_dir, gnd_template_name)
        gnd_eng = KiCadTemplateEngine(gnd_src_path) if os.path.exists(gnd_src_path) else None

        k_eng = KiCadTemplateEngine(os.path.join(tpl_dir, "Kelvin_Template.kicad_sch"))
        c_eng = KiCadTemplateEngine(os.path.join(tpl_dir, "ChargeRelease_Template.kicad_sch"))
        mux_eng = KiCadTemplateEngine(os.path.join(tpl_dir, "Relay_MUX.kicad_sch")) if os.path.exists(os.path.join(tpl_dir, "Relay_MUX.kicad_sch")) else None
        
        engines = {"Kelvin": k_eng, "ChargeRelease": c_eng, "Relay_Direct": mux_eng, "Relay_MUX_Shared": mux_eng}
        # 1. 加载名字与分组名完全对应的常规模块
        for mod_name in ["BUF634A_SOP8", "OPA145_INA141", "OPA189", "SN74LVC2G17DBVR", "TPS78401DRVR_3.3V", "5V_Power2Relay"]:
            path = os.path.join(tpl_dir, f"{mod_name}.kicad_sch")
            if os.path.exists(path): 
                engines[mod_name] = KiCadTemplateEngine(path)
        
        # 👇 新增：挂载无源器件模板
        r_path = os.path.join(tpl_dir, "Resistor_Template.kicad_sch")
        if os.path.exists(r_path):
            engines["Resistor"] = KiCadTemplateEngine(r_path)

        c_path = os.path.join(tpl_dir, "Capacitor_Template.kicad_sch")
        if os.path.exists(c_path):
            engines["Capacitor"] = KiCadTemplateEngine(c_path)

        # 🌟 2. 核心修复：显式处理名称不一致的模板映射
        coil_path = os.path.join(tpl_dir, "Coil_Template.kicad_sch")
        if os.path.exists(coil_path):
            engines["Relay_Coils"] = KiCadTemplateEngine(coil_path)  # 👈 强制映射到 NetMapper 输出的组名

        # 在 src/exporters/sch_generator.py 中：
        sock_path = config.project_info.component_overrides.get('SOCKET_PATH', '')
        
        # 🌟 如果它是相对路径，把它和项目根目录拼接起来变成当前的绝对路径
        if not os.path.isabs(sock_path):
            sock_path = os.path.normpath(os.path.join(base_dir, sock_path))
            
        sock_name = config.project_info.component_overrides.get('SOCKET_NAME', '')
        sock_lib, pin_coords = SocketRouter.extract_and_parse_socket(sock_path, sock_name)

        blocks_to_merge = [sock_lib] + [eng.lib_symbols_block for eng in engines.values() if eng]
        if gnd_eng: blocks_to_merge.append(gnd_eng.lib_symbols_block)
        for s in pogo_sheets:
            pogo_eng = KiCadTemplateEngine(os.path.join(proj_dir, s["f"]))
            blocks_to_merge.append(pogo_eng.lib_symbols_block)

        m_syms = SchGenerator._merge_lib_symbols(*blocks_to_merge)

        # 🌟 修复: 更新版本号为 KiCad 9.0 的新格式
        kicad_version_header = '(version 20240317)'
        
        root_content = f'(kicad_sch {kicad_version_header} (generator "eeschema") (generator_version "9.0") (uuid "{root_uuid}") (paper "A2")\n{m_syms}\n'

        for i, uid in enumerate(site_uuids, 1):
            x, y = 50 + (i - 1) * 45, 50
            root_content += f'(sheet (at {x} {y}) (size 35 6) (uuid "{uid}") (property "Sheetname" "Site_{i}" (at {x} {y - 1.5} 0) (effects (font (size 1.27 1.27)) (justify left bottom))) (property "Sheetfile" "Site_{i}.kicad_sch" (at {x} {y + 7} 0) (effects (font (size 1.27 1.27)) (justify left top))) (instances (project "{actual_proj_name}" (path "/{uid}" (page "{i + 1}")))))\n'

        for idx, s in enumerate(pogo_sheets):
            x, y = 50 + (idx % 6) * 45, 100 + (idx // 6) * 15
            root_content += f'(sheet (at {x} {y}) (size 35 6) (uuid "{s["u"]}") (property "Sheetname" "{s["n"]}" (at {x} {y - 1.5} 0) (effects (font (size 1.27 1.27)) (justify left bottom))) (property "Sheetfile" "{s["f"]}" (at {x} {y + 7} 0) (effects (font (size 1.27 1.27)) (justify left top))) (instances (project "{actual_proj_name}" (path "/{s["u"]}" (page "{pogo_start_page + idx}")))))\n'
        
        if gnd_eng:
            gnd_body = gnd_eng.stamp(root_uuid, root_uuid, actual_proj_name, offset_x=300.0, offset_y=150.0)
            gnd_body = gnd_body.replace(f'(path "/{root_uuid}/{root_uuid}"', f'(path "/{root_uuid}"')
            root_content += "\n" + gnd_body

        hierarchy_paths = ['    (path "/" (page "1"))'] + [f'    (path "/{uid}" (page "{i + 1}"))' for i, uid in enumerate(site_uuids)] + [f'    (path "/{s["u"]}" (page "{pogo_start_page + idx}"))' for idx, s in enumerate(pogo_sheets)]
        root_content += "\n  (sheet_instances\n" + "\n".join(hierarchy_paths) + "\n  )\n)"

        with open(os.path.join(proj_dir, f"{actual_proj_name}.kicad_sch"), "w", encoding="utf-8") as f: f.write(root_content)

        cbit_counters = {}
        for i, s_uuid in enumerate(site_uuids, 1):
            sheet_id = f"S{i}"
            # 🌟 修复: 更新子图纸的版本号
            site_content = f'(kicad_sch {kicad_version_header} (generator "eeschema") (generator_version "9.0") (uuid "{uuid.uuid4()}") (paper "User" 2000 2000)\n{m_syms}\n'
            site_content += SocketRouter.generate_fanout(sock_name, pin_coords, config.pin_template_mapping, i, 80, 80, root_uuid, s_uuid, actual_proj_name)
            grouped_modules = NetMapper.build_site_modules(config.pin_template_mapping, i, sheet_id, cbit_counters, bool(mux_eng))
            site_content += LayoutEngine.render_site(grouped_modules, engines, None, root_uuid, s_uuid, actual_proj_name)

            # 🌟 新增：生成被动元件（电容等）
            # try:
            #     passives_content = LayoutEngine.render_passive_components(grouped_modules, engines, config, i, root_uuid, s_uuid, proj_name=actual_proj_name)
            #     if passives_content:
            #         site_content += "\n\n" + passives_content
            # except Exception as e:
            #     print(f"⚠️ 被动元件生成失败: {e}")

            site_content += f'\n  (sheet_instances (path "/{s_uuid}" (page "{i + 1}"))) \n)'
            with open(os.path.join(proj_dir, f"Site_{i}.kicad_sch"), "w", encoding="utf-8") as f: f.write(site_content)

        return os.path.join(proj_dir, f"{actual_proj_name}.kicad_sch")