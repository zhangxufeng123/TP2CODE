class BaseHardwareModule:
    def __init__(self, module_id: str, params: dict = None, overrides: dict = None):
        """
        :param module_id: 模块的唯一标识符
        :param params: 当前引脚的局部参数 (如电阻值)
        :param overrides: 全局器件覆写配置 (如 {"Relay": "G6K", "Diode": "SS14"})
        """
        self.module_id = module_id
        self.params = params or {}
        self.overrides = overrides or {}
        
        self.width = 100
        self.height = 40

    def get_symbol_keyword(self, role: str, default_keyword: str) -> str:
        """
        🌟 核心魔法：获取器件的搜索关键字
        优先查找用户覆写字典，找不到则使用模块自带的默认关键字
        """
        user_choice = self.overrides.get(role, "").strip()
        if user_choice:
            return user_choice
        return default_keyword

    def build_logic(self, sch_api, **kwargs):
        raise NotImplementedError("子类必须实现 build_logic() 逻辑连线方法！")

    def draw_visual(self, sch_api, ox: float, oy: float, **kwargs):
        raise NotImplementedError("子类必须实现 draw_visual() 绘图方法！")