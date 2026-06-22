import pandas as pd
import re

class TestPlanParser:
    @staticmethod
    def parse_tp_pins(filepath: str, max_rows: int = 30) -> list:
        """
        智能解析 TP Excel：使用“锚点扫荡法”提取引脚。
        1. 锁定包含最多 PINx 的行作为表头。
        2. 找到第一个 PINx 所在的列作为起点。
        3. 从该起点向右扫荡，提取所有引脚（包括不带 PIN 关键字的 Thermal Pad 等）。
        """
        df_raw = pd.read_excel(filepath, header=None, nrows=max_rows)
        
        # 匹配 "PIN" 后跟可选空格和数字的模式 (忽略大小写)
        pin_pattern = re.compile(r'PIN\s*\d+', re.IGNORECASE)
        
        best_row_idx = -1
        max_pin_count = 0
        
        # 🌟 1. 寻找“锚点行”：包含最多 PIN+数字 格式的行
        for idx, row in df_raw.iterrows():
            # 统计这一行里有几个标准的 PINx
            count = sum(1 for val in row if pd.notna(val) and pin_pattern.search(str(val)))
            if count > max_pin_count:
                max_pin_count = count
                best_row_idx = idx
                
        if best_row_idx == -1:
            raise ValueError("未能找到包含 'PIN1', 'PIN2' 格式的表头行，请检查 TP Excel 格式！")
            
        target_row = df_raw.iloc[best_row_idx]
        
        # 🌟 2. 定位起点：找到第一个 PINx 所在的列索引
        start_col_idx = -1
        for col_idx, val in enumerate(target_row):
            if pd.notna(val) and pin_pattern.search(str(val)):
                start_col_idx = col_idx
                break
                
        extracted_pins = []
        
        # 可选的防误触黑名单：如果引脚区右侧还有大段备注列，遇到这些词停止扫荡
        stop_keywords = ['REMARK', 'NOTE', 'COMMENT']
        
        # 🌟 3. 向右扫荡：从第一个 PIN1 开始，把右边所有的格子都当做引脚抓取！
        for col_idx in range(start_col_idx, len(target_row)):
            val = target_row.iloc[col_idx]
            
            # 跳过合并单元格产生的 NaN
            if pd.isna(val):
                continue
                
            s = str(val).strip()
            s_up = s.upper()
            
            if not s or s_up == 'NAN':
                continue
                
            # 触碰防误触黑名单，且该格本身不是合法 PIN 时，停止扫荡
            if any(kw in s_up for kw in stop_keywords) and not pin_pattern.search(s):
                break
                
            # 🌟 4. 数据清洗：将特殊字符替换为下划线
            # 例如 "Thermal pad GND(Thermal)" -> "Thermal_pad_GND_Thermal"
            clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', s)
            clean_name = re.sub(r'_+', '_', clean_name).strip('_')
            
            if clean_name:
                extracted_pins.append(clean_name)
                
        return extracted_pins