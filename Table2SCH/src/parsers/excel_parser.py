import pandas as pd
import re

class HardwareExcelParser:
    @staticmethod
    def parse(filepath: str) -> tuple:
        """返回 (slot_map, channels_per_board)"""
        df = pd.read_excel(filepath)
        slot_map = {}
        channels_per_board = {}
        
        cols = df.columns.astype(str).str.lower()
        slot_col = df.columns[cols.str.contains('slot') & ~cols.str.contains('cbit')][0]
        site_col = df.columns[cols.str.contains('site')][0]
        res_col = df.columns[cols.str.contains('res')][0]
        chan_col = df.columns[cols.str.contains('chan')][0]

        for _, row in df.iterrows():
            slot, site_str, res, chans = str(row[slot_col]), str(row[site_col]), str(row[res_col]), int(row[chan_col])
            channels_per_board[res] = chans
            target_sites = ["1", "2", "3", "4"] if 'shared' in site_str.lower() else re.findall(r'\d+', site_str)

            for s in target_sites:
                if s not in slot_map: slot_map[s] = {}
                if res not in slot_map[s]: slot_map[s][res] = []
                if slot not in slot_map[s][res]: slot_map[s][res].append(slot)
                
        return slot_map, channels_per_board