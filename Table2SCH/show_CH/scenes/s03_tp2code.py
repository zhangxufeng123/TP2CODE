from manim import *

class S03_TechDetails(Scene):
    def construct(self):
        # Technical Details
        tech_title = Text("1.4 技术突破", font_size=32, color=BLUE).to_edge(UP, buff=1)
        tech1 = Text("1. 智能引脚映射：命名规则+物理布局混合匹配", font_size=24).next_to(tech_title, DOWN, aligned_edge=LEFT)
        tech2 = Text("2. 伪代码生成：常见测试语言规则（如FV, RampV, Monitor）", font_size=24).next_to(tech1, DOWN, aligned_edge=LEFT)
        tech3 = Text("3. MUX资源优化：自动识别并复用硬件资源（继电器切换）", font_size=24).next_to(tech2, DOWN, aligned_edge=LEFT)
        tech4 = Text("4. 参数化配置系统：模块化电路灵活配置", font_size=24).next_to(tech3, DOWN, aligned_edge=LEFT)
        tech5 = Text("5. 实时错误检测：设计过程实时验证接口匹配", font_size=24).next_to(tech4, DOWN, aligned_edge=LEFT)

        self.play(Write(tech_title))
        self.play(FadeIn(tech1), FadeIn(tech2), FadeIn(tech3), FadeIn(tech4), FadeIn(tech5))
        self.wait(4)
        self.play(FadeOut(tech_title, tech1, tech2, tech3, tech4, tech5))

        # Core Workflow
        arch_title = Text("核心工作流 & 功能架构", font_size=36, color=BLUE).to_edge(UP)

        step1 = Text("1. Testplan (JSON)", font_size=24)
        step2 = Text("2. AI Agent (Skill 解析与匹配)", font_size=24, color=YELLOW)
        step3 = Text("3. Table2SCH/STS8300_LB_from_JSON.csv", font_size=24)
        step4 = Text("4. json_to_schematic.py (配置解析)", font_size=24, color=GREEN)
        step5 = Text("5. 自动化生成 KiCad 原理图", font_size=24, color=RED)

        flow_group = VGroup(step1, step2, step3, step4, step5).arrange(DOWN, buff=0.5).next_to(arch_title, DOWN, buff=0.5)
        arrows = VGroup(*[Arrow(flow_group[i].get_bottom(), flow_group[i+1].get_top()) for i in range(len(flow_group)-1)])

        self.play(Write(arch_title))
        self.play(FadeIn(step1))
        for i in range(len(arrows)):
            self.play(GrowArrow(arrows[i]), FadeIn(flow_group[i+1]))
        self.wait(3)
        self.play(FadeOut(arch_title, flow_group, arrows))
