class LayoutEngine:
    def __init__(self, margin_x=30, margin_y=30, spacing_y=20):
        self.modules_to_place = []
        self.margin_x = margin_x
        self.margin_y = margin_y
        self.spacing_y = spacing_y # 模块之间的垂直间距

    def add_module(self, module_instance, io_kwargs):
        """
        添加一个实例到排版队列
        :param io_kwargs: 保存网络连线的字典，画图和逻辑连线都要用
        """
        self.modules_to_place.append({
            "mod": module_instance,
            "kwargs": io_kwargs
        })

    def _determine_paper_size(self, total_height: float) -> str:
        """根据所有模块的总高度，智能选择 KiCad 图纸尺寸"""
        if total_height < 180: return "A4"       # A4: 297x210
        elif total_height < 270: return "A3"     # A3: 420x297
        elif total_height < 390: return "A2"     # A2: 594x420
        elif total_height < 560: return "A1"     # A1: 841x594
        else: return "A0"                        # A0: 1189x841

    def execute_all(self, sch_api):
        """
        执行终极计算：不仅计算出每个模块的 ox, oy 让它画出来，
        还会调用它底层的 skidl 逻辑！
        """
        current_y = self.margin_y
        max_width = 0

        print(f"📐 开始排版计算... 共 {len(self.modules_to_place)} 个模块。")

        for item in self.modules_to_place:
            mod = item["mod"]
            kwargs = item["kwargs"]
            
            # 1. 记录最大宽度
            if mod.width > max_width:
                max_width = mod.width


            # 2. 执行【逻辑轨】：构建 Skidl 网表 (传入 sch_api)
            mod.build_logic(sch_api, **kwargs)

            # 3. 执行【视图轨】：计算绝对坐标并画到 KiCad
            ox = self.margin_x
            oy = current_y
            mod.draw_visual(sch_api, ox=ox, oy=oy, **kwargs)

            # 4. Y轴向下移动：当前模块高度 + 预设间距
            current_y += mod.height + self.spacing_y

        # 计算完毕，算出总高度并动态调整图纸大小！
        paper_size = self._determine_paper_size(current_y)
        sch_api.page_size = paper_size
        print(f"📄 自动计算完毕！图纸尺寸确定为: {paper_size}, 总高度占用: {current_y}mm")