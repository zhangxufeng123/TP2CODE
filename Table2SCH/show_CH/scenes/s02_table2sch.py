from manim import *

class S02_PainPoints(Scene):
    def construct(self):
        # Pain points
        pain_title = Text("1.2 传统流程痛点", font_size=32, color=RED).to_edge(UP, buff=1)
        pain1 = Text("1. 效率低下：单板设计耗时3-7天", font_size=24).next_to(pain_title, DOWN, aligned_edge=LEFT)
        pain2 = Text("2. 错误频发：人工操作错误率15-20%", font_size=24).next_to(pain1, DOWN, aligned_edge=LEFT)
        pain3 = Text("3. 学习成本高：新员工需2-3个月培训", font_size=24).next_to(pain2, DOWN, aligned_edge=LEFT)
        pain4 = Text("4. 维护困难：设计变更难以追溯", font_size=24).next_to(pain3, DOWN, aligned_edge=LEFT)

        self.play(Write(pain_title))
        self.play(FadeIn(pain1), FadeIn(pain2), FadeIn(pain3), FadeIn(pain4))
        self.wait(2)

        self.play(FadeOut(pain_title, pain1, pain2, pain3, pain4))

        # Comparison
        comp_title = Text("1.3 方案对比 (AI 赋能)", font_size=32, color=GREEN).to_edge(UP, buff=1)

        table = Table(
            [["Testplan", "Testplan", ""],
             ["人工辨识引脚", "TP2SCH自动解析", "⚡ 自动化处理"],
             ["手动匹配引脚", "AI智能匹配算法", "🧠"],
             ["手动连线", "自动连线引擎", "🤖 全自动"],
             ["反复检查验证", "一键生成原理图及代码", "🎯 标准化"],
             ["3-7天", "10-30分钟", "🔥 效率提升20-30倍"]],
            col_labels=[Text("传统流程"), Text("AI赋能流程"), Text("改进点")],
            row_labels=[Text("输入"), Text("解析"), Text("匹配"), Text("连线"), Text("输出"), Text("耗时")],
            include_outer_lines=True,
            element_to_mobject=Text
        ).scale(0.4).next_to(comp_title, DOWN)

        self.play(Write(comp_title))
        self.play(FadeIn(table))
        self.wait(3)

        self.play(FadeOut(comp_title, table))
