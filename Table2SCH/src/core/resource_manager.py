# filepath: src/core/resource_manager.py

class ComponentAllocator:
    """管理 R, C, U, D, TP 等器件的自增编号"""
    def __init__(self, sheet_id):
        self.sheet_id = sheet_id
        self.counters = {"R": 1, "C": 1, "U": 1, "D": 1, "TP": 1}

    def get_next(self, prefix, count=1):
        if count == 1:
            val = f"{prefix}{self.counters[prefix]}_{self.sheet_id}"
            self.counters[prefix] += 1
            return val
        result = [f"{prefix}{self.counters[prefix] + i}_{self.sheet_id}" for i in range(count)]
        self.counters[prefix] += count
        return result

class RelayPacker:
    """管理继电器打包 (双刀双掷 A/B/C) 和线圈资源"""
    def __init__(self, sheet_id):
        self.sheet_id = sheet_id
        self.k_idx = 1
        self.groups = {}
        
    def get_switch(self, group_name=None):
        if not group_name:
            idx = self.k_idx
            self.k_idx += 1
            return f"K{idx}_{self.sheet_id}B"
            
        if group_name not in self.groups:
            self.groups[group_name] = {"idx": self.k_idx, "used": 0}
            self.k_idx += 1
            
        grp = self.groups[group_name]
        if grp["used"] == 0:
            grp["used"] = 1
            return f"K{grp['idx']}_{self.sheet_id}B"
        else:
            grp["used"] = 2
            res = f"K{grp['idx']}_{self.sheet_id}C"
            del self.groups[group_name]
            return res

    def get_pair(self):
        idx = self.k_idx
        self.k_idx += 1
        return f"K{idx}_{self.sheet_id}"