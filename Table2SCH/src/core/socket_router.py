import uuid
import re

class SocketRouter:
    @staticmethod
    def extract_and_parse_socket(filepath, target_sym):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = f.read()
        sym_start = data.find(f'(symbol "{target_sym}"')
        if sym_start == -1: return "", {}
        bc, end = 0, -1
        for i in range(sym_start, len(data)):
            if data[i] == '(': bc += 1
            elif data[i] == ')':
                bc -= 1
                if bc == 0: end = i + 1; break
        sym_block = data[sym_start:end]
        pin_info = {}
        pins_raw = sym_block.split('(pin ')[1:]
        for p in pins_raw:
            at_m = re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)', p)
            num_m = re.search(r'\(number\s+"([^"]+)"', p)
            if at_m and num_m:
                pin_info[num_m.group(1)] = {'x': float(at_m.group(1)), 'y': -float(at_m.group(2))}
        return f"(lib_symbols\n{sym_block}\n)", pin_info

    @staticmethod
    def generate_fanout(socket_name, pin_coords, pin_mappings, site_idx: int, SX, SY, root_uuid, sheet_uuid, proj_name):
        if not pin_coords: return ""
        sym_uuid = str(uuid.uuid4())
        ref_name = f"SOCKET_S{site_idx}"
        content = f'  (symbol (lib_id "{socket_name}") (at {SX} {SY} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid "{sym_uuid}") (property "Reference" {ref_name} (at {SX} {SY-20} 0) (id 0) (effects (font (size 2 2)))) (property "Value" "{socket_name}" (at {SX} {SY+20} 0) (id 1) (effects (font (size 2 2)))) (instances (project "{proj_name}" (path "/{root_uuid}/{sheet_uuid}" (reference {ref_name}) (unit 1)))))\n'

        xs = [p['x'] for p in pin_coords.values()]; ys = [p['y'] for p in pin_coords.values()]
        min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
        cy = (min_y + max_y) / 2.0

        # 辅助函数：将坐标吸附到 KiCad 默认的 1.27mm 栅格上，确保交点和连线完美对齐
        def snap(val): return round(val / 1.27) * 1.27

        for row in pin_mappings:
            if not row.socket_pins_map: continue
            
            is_kelvin = row.connect_type == "Kelvin"
            
            # 提取当前行分配到的所有有效引脚
            valid_pins = []
            for role, pid in row.socket_pins_map.items():
                if pid in pin_coords:
                    valid_pins.append((role, pid, pin_coords[pid]))
            
            if not valid_pins: continue

            # ========================================================
            # 模式 1：Kelvin 或 单引脚 Direct -> 独立扇出
            # ========================================================
            if is_kelvin or len(valid_pins) == 1:
                for role, pid, p in valid_pins:
                    px, py = SX + p['x'], SY + p['y']
                    label = f"{row.logical_net}_{role}_S{site_idx}" if is_kelvin else f"{row.logical_net}_S{site_idx}"
                    
                    dists = {'L': p['x']-min_x, 'R': max_x-p['x'], 'T': p['y']-min_y, 'B': max_y-p['y']}
                    closest = min(dists, key=dists.get)
                    is_internal = dists[closest] > 7.62
                    
                    is_even = int(re.search(r'\d+', pid).group()) % 2 == 0 if re.search(r'\d+', pid) else False
                    length = 5.08 if is_internal else (15.24 if is_even else 30.48)

                    if is_internal:
                        dy_dir = -length if p['y'] < cy else length
                        la = 90 if p['y'] < cy else 270
                        just = "left" if la == 90 else "right" 
                        content += f'  (wire (pts (xy {px:.2f} {py:.2f}) (xy {px:.2f} {py+dy_dir:.2f})) (stroke (width 0) (type default)))\n  (global_label "{label}" (shape bidirectional) (at {px:.2f} {py+dy_dir:.2f} {la}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {just})))\n'
                    elif closest == 'L':
                        content += f'  (wire (pts (xy {px:.2f} {py:.2f}) (xy {px-length:.2f} {py:.2f})) (stroke (width 0) (type default)))\n  (global_label "{label}" (shape bidirectional) (at {px-length:.2f} {py:.2f} 180) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify right)))\n'
                    elif closest == 'R':
                        content += f'  (wire (pts (xy {px:.2f} {py:.2f}) (xy {px+length:.2f} {py:.2f})) (stroke (width 0) (type default)))\n  (global_label "{label}" (shape bidirectional) (at {px+length:.2f} {py:.2f} 0) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify left)))\n'
                    elif closest == 'T':
                        content += f'  (wire (pts (xy {px:.2f} {py:.2f}) (xy {px:.2f} {py-length:.2f})) (stroke (width 0) (type default)))\n  (global_label "{label}" (shape bidirectional) (at {px:.2f} {py-length:.2f} 90) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify left)))\n'
                    elif closest == 'B':
                        content += f'  (wire (pts (xy {px:.2f} {py:.2f}) (xy {px:.2f} {py+length:.2f})) (stroke (width 0) (type default)))\n  (global_label "{label}" (shape bidirectional) (at {px:.2f} {py+length:.2f} 270) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify right)))\n'
            
            # ========================================================
            # 模式 2：多引脚 Direct -> 物理汇聚合并扇出
            # ========================================================
            else:
                label = f"{row.logical_net}_S{site_idx}"
                pts = [(SX + p['x'], SY + p['y']) for _, _, p in valid_pins]
                
                # 依据第一个引脚决定整体引出方向
                p_x, p_y = valid_pins[0][2]['x'], valid_pins[0][2]['y']
                dists = {'L': p_x - min_x, 'R': max_x - p_x, 'T': p_y - min_y, 'B': max_y - p_y}
                closest = min(dists, key=dists.get)
                is_internal = dists[closest] > 7.62
                
                # 计算合并中心交点（Junction）并吸附到 1.27 栅格
                cx = snap(sum(x for x, y in pts) / len(pts))
                cy_pts = snap(sum(y for x, y in pts) / len(pts))
                
                short_len = 3.81   # 汇聚横线的引出距离 (3格)
                length = 15.24     # 主干线的延伸距离 (12格)
                if is_internal: length = 5.08

                # 判定横轴或纵轴结构
                if is_internal:
                    is_top = p_y < cy
                    sy = -short_len if is_top else short_len
                    dy = -length if is_top else length
                    is_vertical = True
                    la, just = (90, "left") if is_top else (270, "right")
                elif closest == 'T':
                    sy, dy = -short_len, -length
                    is_vertical = True
                    la, just = 90, "left"
                elif closest == 'B':
                    sy, dy = short_len, length
                    is_vertical = True
                    la, just = 270, "right"
                elif closest == 'L':
                    sx, dx = -short_len, -length
                    is_vertical = False
                    la, just = 180, "right"
                elif closest == 'R':
                    sx, dx = short_len, length
                    is_vertical = False
                    la, just = 0, "left"
                    
                # 绘制分叉结构
                if is_vertical:
                    base_y = snap(pts[0][1])
                    cross_y = base_y + sy
                    for px, py in pts:
                        # 1. 向外伸出一小段
                        content += f'  (wire (pts (xy {px:.2f} {py:.2f}) (xy {px:.2f} {cross_y:.2f})) (stroke (width 0) (type default)))\n'
                        # 2. 横向拉到中心点
                        content += f'  (wire (pts (xy {px:.2f} {cross_y:.2f}) (xy {cx:.2f} {cross_y:.2f})) (stroke (width 0) (type default)))\n'
                    # 3. 在中心放置交点
                    content += f'  (junction (at {cx:.2f} {cross_y:.2f}) (diameter 0) (color 0 0 0 0))\n'
                    # 4. 主干线向外延伸
                    content += f'  (wire (pts (xy {cx:.2f} {cross_y:.2f}) (xy {cx:.2f} {base_y+dy:.2f})) (stroke (width 0) (type default)))\n'
                    # 5. 挂载单一全局标签
                    content += f'  (global_label "{label}" (shape bidirectional) (at {cx:.2f} {base_y+dy:.2f} {la}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {just})))\n'
                else:
                    base_x = snap(pts[0][0])
                    cross_x = base_x + sx
                    for px, py in pts:
                        content += f'  (wire (pts (xy {px:.2f} {py:.2f}) (xy {cross_x:.2f} {py:.2f})) (stroke (width 0) (type default)))\n'
                        content += f'  (wire (pts (xy {cross_x:.2f} {py:.2f}) (xy {cross_x:.2f} {cy_pts:.2f})) (stroke (width 0) (type default)))\n'
                    content += f'  (junction (at {cross_x:.2f} {cy_pts:.2f}) (diameter 0) (color 0 0 0 0))\n'
                    content += f'  (wire (pts (xy {cross_x:.2f} {cy_pts:.2f}) (xy {base_x+dx:.2f} {cy_pts:.2f})) (stroke (width 0) (type default)))\n'
                    content += f'  (global_label "{label}" (shape bidirectional) (at {base_x+dx:.2f} {cy_pts:.2f} {la}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {just})))\n'
                    
        return content