import os
import re
import glob

def deep_repair_kicad_files(template_dir):
    sch_files = glob.glob(os.path.join(template_dir, "*.kicad_sch"))
    print(f"🔧 开始终极修复，扫描 {len(sch_files)} 个文件...\n")
    
    # 定义顶部缓存符号的重命名映射
    PARENT_MAPPING = {
        r'.*Cap.*': 'JW_Component:C_SM_0603_1',
        r'.*Res.*': 'JW_Component:R_SM_0805_1',
        r'.*CON1.*': 'JW_Component:PinHeader_1x02',
        r'.*BUF634.*': 'JW_Component:BUF634_SOIC8',
        r'.*RELAY.*': 'JW_Component:Relay_Generic',
    }

    repaired_count = 0
    for filepath in sch_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        original_content = content
        
        # ==========================================
        # 修复 1：修复 lib_symbols 中的父子符号命名断层
        # ==========================================
        def fix_parent_child(match):
            parent_block = match.group(0)
            
            # 找到父符号名
            m = re.search(r'\n\t\t\(\s*symbol\s+"([^"]+)"', parent_block)
            if not m: return parent_block
            old_parent = m.group(1)
            
            new_parent = old_parent
            # 如果父名字还是旧的乱码，将它映射到 JW_Component
            for pat, new_name in PARENT_MAPPING.items():
                if re.match(pat, old_parent, re.IGNORECASE):
                    new_parent = new_name
                    break
            
            # 替换父符号名
            parent_block = parent_block.replace(f'(symbol "{old_parent}"', f'(symbol "{new_parent}"', 1)
            
            # 🌟 核心修复：强制统一子符号名前缀，解决 Invalid symbol prefix 报错！
            def child_repl(m_child):
                suffix = m_child.group(1) # 获取后缀如 _1_0
                return f'\n\t\t\t(symbol "{new_parent}{suffix}"'
            
            # 替换缩进为3个tab的子符号
            parent_block = re.sub(r'\n\t\t\t\(\s*symbol\s+"[^"]+(_[0-9]+_[0-9]+)"', child_repl, parent_block)
            return parent_block

        content = re.sub(r'\n\t\t\(\s*symbol\s+"[^"]+".*?\n\t\t\)', fix_parent_child, content, flags=re.DOTALL)

        # ==========================================
        # 修复 2 & 3：清理底部的脏数据 (lib_name 冲突, 错误的 lib_id)
        # ==========================================
        def fix_instance(match):
            block = match.group(0)
            
            # 强制删掉遗留的、引发解析崩溃的 lib_name 行
            block = re.sub(r'\n\t\t\(lib_name\s+"[^"]+"\)', '', block)
            
            # 根据 Reference (@C1@, @R2@等) 强制覆盖正确的 lib_id
            ref_match = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
            if ref_match:
                ref = ref_match.group(1).upper()
                new_lib = None
                
                if '@C' in ref or re.match(r'^C\d+', ref): new_lib = 'JW_Component:C_SM_0603_1'
                elif '@R' in ref or re.match(r'^R\d+', ref): new_lib = 'JW_Component:R_SM_0805_1'
                elif '@K' in ref or re.match(r'^K\d+', ref): new_lib = 'JW_Component:Relay_Generic'
                elif '@D' in ref or re.match(r'^D\d+', ref): new_lib = 'JW_Component:D_SM_SMA'
                elif '@TP' in ref or 'TP' in ref: new_lib = 'JW_Component:PinHeader_1x02'
                
                if new_lib:
                    block = re.sub(r'\(lib_id\s+"[^"]+"\)', f'(lib_id "{new_lib}")', block)
                    
            return block

        content = re.sub(r'\n\t\(symbol\n\t\t\(lib_id\s+"[^"]+"\).*?\n\t\)', fix_instance, content, flags=re.DOTALL)

        # 保存修复后的文件
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 成功重构修复: {os.path.basename(filepath)}")
            repaired_count += 1
            
    print(f"\n🎉 深度抢救完毕！共修复了 {repaired_count} 个文件。")

if __name__ == "__main__":
    # 填入你损坏的 templates 文件夹路径
    target_folder = r"C:\Users\11271\Desktop\Table2SCH\lib\templates"
    deep_repair_kicad_files(target_folder)