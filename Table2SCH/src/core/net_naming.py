# filepath: src/core/net_naming.py
import re

class NetNamingManager:
    @staticmethod
    def get_base_net(display_pin, logical_net):
        """提取基础网络名 (PIN24_XXX)"""
        pin_match = re.search(r'(PIN\d+)', display_pin, re.IGNORECASE)
        clean_pin = pin_match.group(1).upper() if pin_match else display_pin.split()[0].upper().replace("/", "_").replace("\\", "_")
        net_name = logical_net.strip()
        return net_name if net_name.upper().startswith(clean_pin) else f"{clean_pin}_{net_name}", clean_pin

    @staticmethod
    def get_socket_net(base_net, connect_type, sheet_id):
        """Socket 端的最终网络名"""
        return f"{base_net}_F_{sheet_id}" if connect_type == "Kelvin" else f"{base_net}_{sheet_id}"

    @staticmethod
    def get_cascade_node_net(clean_pin, node_idx, sheet_id):
        """级联继电器之间的内部飞线"""
        return f"CASCADE_{clean_pin}_NODE{node_idx}_{sheet_id}"

    @staticmethod
    def get_cascade_main_net(clean_pin, sheet_id):
        """切断主资源的最终级联母线"""
        return f"CASCADE_{clean_pin}_MAIN_{sheet_id}"

    @staticmethod
    def get_fh_sh_nets(ate_net):
        """生成 Kelvin 仪器的 Force 和 Sense 靶向网络"""
        ate_f = ate_net.replace("_CH", "_FH") if "_CH" in ate_net else f"{ate_net}_FH"
        ate_s = ate_net.replace("_CH", "_SH") if "_CH" in ate_net else f"{ate_net}_SH"
        return ate_f, ate_s