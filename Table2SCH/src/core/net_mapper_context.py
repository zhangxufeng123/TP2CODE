# filepath: src/core/net_mapper_context.py
import json

class PinContext:
    def __init__(self, pin_data, site_idx, sheet_id, global_state):
        self.pin_data = pin_data
        self.site_idx = site_idx
        self.sheet_id = sheet_id
        
        # 全局状态
        self.placed_shared_groups = global_state['placed_shared_groups']
        self.placed_qtmu_buses = global_state['placed_qtmu_buses']
        self.used_instruments = global_state['used_instruments']
        self.mux_eng_exists = global_state['mux_eng_exists']
        self.sys_5v = global_state['sys_5v']
        
        # 解析后的Pin数据
        self.params = self._safe_json_load(pin_data.parameters)
        self.base_net, self.clean_pin = self._get_base_net()
        self.logical_net = pin_data.logical_net.strip()
        self.primary_socket_net = self._get_socket_net()
        self.fl_net = f"FL_{sheet_id}"
        self.chan_map = self._extract_site_channels(pin_data.channel_allocations, [pin_data.resource_type] if pin_data.resource_type else [])
        
        # 默认值，会被 instrument_router 更新
        self.fallback_ate_f = "NC_CH0"
        self.active_circuits = pin_data.active_circuits or []

    def _safe_json_load(self, text):
        try: return json.loads(text) if text else {}
        except: return {}

    def _get_base_net(self):
        import re
        pin_match = re.search(r'(PIN\d+)', self.pin_data.display_pin, re.IGNORECASE)
        clean_pin = pin_match.group(1).upper() if pin_match else self.pin_data.display_pin.split()[0].upper().replace("/", "_").replace("\\", "_")
        net_name = self.pin_data.logical_net.strip()
        base = net_name if net_name.upper().startswith(clean_pin) else f"{clean_pin}_{net_name}"
        return base, clean_pin
        
    def _get_socket_net(self):
        return f"{self.base_net}_F_{self.sheet_id}" if self.pin_data.connect_type == "Kelvin" else f"{self.base_net}_{self.sheet_id}"
    
    def _extract_site_channels(self, raw_str, pin_resources):
        import re
        res_map = {}
        if not raw_str: return res_map
        raw_str = str(raw_str).strip()
        site_block = re.search(rf'Site{self.site_idx}\((.*?)\)', raw_str)
        if site_block:
            inner_str = site_block.group(1)
            items = re.findall(r'([A-Za-z0-9_]+)\[(.*?)\]', inner_str)
            if items:
                for res_name, res_net in items:
                    res_net = res_net.strip()
                    if res_name.upper() in ["ACM200", "FPVIE", "FXVIE", "HPSM"]:
                        m = re.match(r'(S\d+)_(.*)', res_net)
                        if m: res_net = f"{m.group(1)}_{res_name}_{m.group(2)}"
                    res_map[res_name] = res_net
            elif pin_resources: res_map[pin_resources[0]] = inner_str.strip()
        else:
            if pin_resources: res_map[pin_resources[0]] = raw_str
        return res_map