from skidl import Net
from .base_module import BaseHardwareModule

class DirectModule(BaseHardwareModule):
    def __init__(self, module_id: str, params: dict = None, overrides: dict = None):
        super().__init__(module_id, params, overrides)
        self.width = 60
        self.height = 20

    def build_logic(self, sch_api, net_in: str, net_out: str):
        print(f"[SKIDL] 构建 {self.module_id} Direct 直连逻辑...")
        # 🌟 修复语法报错：先实例化给一个变量，然后再进行 += 合并
        n_in = Net(net_in)
        n_in += Net(net_out)

    def draw_visual(self, sch_api, ox: float, oy: float, net_in: str, net_out: str):
        # 【视图轨】绘制直连测试电路：一根线直接从左边拉到右边
        sch_api.add_wire([(ox, oy), (ox + 40, oy)])
        
        # 两端放上网络标签
        sch_api.add_global_label(net_in, ox, oy)
        sch_api.add_global_label(net_out, ox + 40, oy, angle=180)