# filepath: src/exporters/kicad_api.py
import os
import uuid
import re

class KiCadTemplateEngine:
    def __init__(self, template_filepath):
        if not os.path.exists(template_filepath):
            raise FileNotFoundError(f"Template not found: {template_filepath}")
        self.template_filepath = template_filepath
        self.lib_symbols_block, self.raw_body = self._extract_parts(template_filepath)

    def _extract_parts(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        lib_sym_idx = content.find('(lib_symbols')
        lib_symbols_str = "(lib_symbols)"
        if lib_sym_idx != -1:
            bc = 0
            end = -1
            for i in range(lib_sym_idx, len(content)):
                if content[i] == '(':
                    bc += 1
                elif content[i] == ')':
                    bc -= 1
                    if bc == 0:
                        end = i + 1
                        break
            if end != -1:
                lib_symbols_str = content[lib_sym_idx:end]
                content = content[:lib_sym_idx] + content[end:]

        paper_match = re.search(r'\(paper\s+"[^"]+"(?:\s+[-\d.]+\s+[-\d.]+)?\)', content)
        start_idx = paper_match.end() if paper_match else 0

        sheet_match = re.search(r'\(sheet_instances', content)
        end_idx = sheet_match.start() if sheet_match else len(content)

        return lib_symbols_str, content[start_idx:end_idx].strip()

    @staticmethod
    def _remove_instances_block(block_text: str) -> str:
        inst_idx = block_text.find("(instances")
        if inst_idx == -1:
            return block_text
        bc, inst_end = 0, -1
        for i in range(inst_idx, len(block_text)):
            if block_text[i] == '(': bc += 1
            elif block_text[i] == ')':
                bc -= 1
                if bc == 0:
                    inst_end = i + 1
                    break
        if inst_end != -1:
            return block_text[:inst_idx] + block_text[inst_end:]
        return block_text

    @staticmethod
    def _extract_symbol_reference(block_text: str) -> str:
        m = re.search(r'\(\s*property\s+"Reference"\s+"([^"]*)"', block_text)
        return m.group(1) if m else "U?"

    @staticmethod
    def _extract_symbol_unit(block_text: str) -> str:
        m = re.search(r'\(\s*unit\s+(\d+)\s*\)', block_text)
        return m.group(1) if m else "1"

    @staticmethod
    def _normalize_reference_and_unit(ref_val: str, unit_val: str):
        if not ref_val: return "U?", unit_val or "1"
        m = re.match(r'^([A-Za-z0-9_#]+?\d+)([A-Z])$', ref_val)
        if m:
            clean_ref = m.group(1)
            unit_letter = m.group(2)
            forced_unit = str(ord(unit_letter) - ord('A') + 1)
            return clean_ref, forced_unit
        return ref_val, unit_val or "1"

    def _process_symbol_block(self, block_text, project_name, root_uuid, sheet_instance_uuid):
        ref_val, unit_val = self._extract_symbol_reference(block_text), self._extract_symbol_unit(block_text)
        ref_val, unit_val = self._normalize_reference_and_unit(ref_val, unit_val)
        old_ref = self._extract_symbol_reference(block_text)
        if old_ref != ref_val:
            block_text = block_text.replace(f'(property "Reference" "{old_ref}"', f'(property "Reference" "{ref_val}"', 1)
        block_text = re.sub(r'\(\s*unit\s+\d+\s*\)', f'(unit {unit_val})', block_text)
        block_text = self._remove_instances_block(block_text).rstrip()
        if block_text.endswith(')'):
            block_text = block_text[:-1].rstrip()
        instances_block = f"""
  (instances (project "{project_name}" (path "/{root_uuid}/{sheet_instance_uuid}" (reference "{ref_val}") (unit {unit_val}))))
)"""
        return block_text + instances_block

    @staticmethod
    def _replace_all_placeholders(text: str, replace_dict: dict) -> str:
        for k, v in replace_dict.items():
            text = text.replace(k, str(v))
        return text

    @staticmethod
    def _refresh_uuids(text: str) -> str:
        uuid_map = {}
        def repl(m):
            old_u = m.group(0)
            if old_u not in uuid_map: uuid_map[old_u] = str(uuid.uuid4())
            return uuid_map[old_u]
        return re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', repl, text)

    @staticmethod
    def _shift_coordinates(text: str, offset_x: float, offset_y: float) -> str:
        def shift_at(m): return f"(at {float(m.group(1)) + offset_x:.2f} {float(m.group(2)) + offset_y:.2f}{m.group(3)})"
        def shift_xy(m): return f"(xy {float(m.group(1)) + offset_x:.2f} {float(m.group(2)) + offset_y:.2f})"
        text = re.sub(r'\(at\s+([-\d.]+)\s+([-\d.]+)(.*?)\)', shift_at, text)
        text = re.sub(r'\(xy\s+([-\d.]+)\s+([-\d.]+)\)', shift_xy, text)
        return text

    def stamp(self, root_uuid, sheet_instance_uuid, project_name, offset_x=0.0, offset_y=0.0, replace_dict=None):
        text = self._replace_all_placeholders(self.raw_body, replace_dict or {})
        text = self._refresh_uuids(text)
        result = []
        idx = 0
        while idx < len(text):
            next_open = text.find('(', idx)
            if next_open == -1:
                result.append(text[idx:]); break
            result.append(text[idx:next_open])
            bc, block_start, block_end = 0, next_open, None
            for i in range(next_open, len(text)):
                if text[i] == '(': bc += 1
                elif text[i] == ')':
                    bc -= 1
                    if bc == 0:
                        block_end = i + 1; break
            if block_end is None:
                result.append(text[block_start:]); break
            block_text = text[block_start:block_end]
            if block_text.startswith("(symbol") and "(lib_id" in block_text:
                block_text = self._process_symbol_block(block_text, project_name, root_uuid, sheet_instance_uuid)
            result.append(block_text)
            idx = block_end
        text = "".join(result)
        text = self._shift_coordinates(text, offset_x, offset_y)
        return text + "\n"

    @classmethod
    def rewrite_external_child_schematic(
        cls, src_filepath: str, dst_filepath: str, project_name: str,
        root_uuid: str, sheet_instance_uuid: str, child_page: int,
        generator: str = "eeschema", generator_version: str = "9.0"
    ):
        eng = cls(src_filepath)
        rebuilt_body = eng.stamp(root_uuid, sheet_instance_uuid, project_name).rstrip()
        
        # 🌟 核心修复: 在重写外部文件时，也使用最新的版本号！
        kicad_version_header = '(version 20240317)' 
        
        content = (
            f'(kicad_sch {kicad_version_header} '
            f'(generator "{generator}") (generator_version "{generator_version}") '
            f'(uuid "{str(uuid.uuid4())}") (paper "A3")\n'
            f'{eng.lib_symbols_block}\n{rebuilt_body}\n'
            f'  (sheet_instances (path "/{sheet_instance_uuid}" (page "{child_page}")))\n'
            f')'
        )
        with open(dst_filepath, "w", encoding="utf-8") as f:
            f.write(content)