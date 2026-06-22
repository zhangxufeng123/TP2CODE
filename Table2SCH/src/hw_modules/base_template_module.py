# filepath: src/hw_modules/base_template_module.py

class TemplateHWModule:
    """
    基于 KiCad 模板替换引擎的硬件模块基类
    所有独立的电路模块 (如 OPA189, 继电器级联) 都应继承此类。
    """
    @classmethod
    def get_module_name(cls) -> str:
        raise NotImplementedError("子类必须提供模块名称")

    @classmethod
    def process(cls, context, res_manager, grouped_modules):
        """
        处理引脚逻辑，并将生成的【模板替换字典】追加到 grouped_modules 中。
        context: 包含当前 Pin 信息的上下文对象
        res_manager: 统筹分配 R/C/U 编号及继电器
        grouped_modules: 最终输出的图纸字典
        """
        raise NotImplementedError("子类必须实现 process 逻辑")