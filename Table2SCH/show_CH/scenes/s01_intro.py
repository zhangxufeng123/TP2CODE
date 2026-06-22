from manim import *

class S01_Intro(Scene):
    def construct(self):
        title = Text("TE: ATE 原理图自动 | 提高测试开发效率", font_size=40).to_edge(UP)
        keywords = Text("关键词：Testplan解析，原理图生成，ATE Mapping，原理图生成流程优化", font_size=24).next_to(title, DOWN)

        overview_title = Text("项目概览", font_size=32, color=BLUE).next_to(keywords, DOWN, buff=0.5)
        overview_content = Text("TP2SCH是一款基于AI技术的ATE硬件自动配置系统，实现测试板设计的全面自动化，\n显著提升半导体测试行业的工作效率。\n适用部门：TE, PTE\n项目成员：张旭峰, 操龙平 Longping Cao", font_size=20).next_to(overview_title, DOWN)

        self.play(Write(title))
        self.play(FadeIn(keywords))
        self.play(Write(overview_title))
        self.play(FadeIn(overview_content))
        self.wait(3)
        self.play(FadeOut(title, keywords, overview_title, overview_content))

        # Project Practice Intro
        intro_title = Text("1. 项目实践介绍", font_size=36).to_edge(UP)

        bg_title = Text("1.1.1 项目背景", font_size=28, color=YELLOW).next_to(intro_title, DOWN, aligned_edge=LEFT)
        bg_content = Text("根据Testplan和测试机型号设计测试原理图是核心工作环节，当前面临多个产品并行开发的压力。", font_size=20).next_to(bg_title, DOWN, aligned_edge=LEFT)

        goal_title = Text("1.1.2 项目最终目标", font_size=28, color=YELLOW).next_to(bg_content, DOWN, aligned_edge=LEFT)
        goal_content = Text("基于原理图自动生成，完成Pre-Silicon验证。", font_size=20).next_to(goal_title, DOWN, aligned_edge=LEFT)

        proj_intro_title = Text("1.1.3 项目介绍", font_size=28, color=YELLOW).next_to(goal_content, DOWN, aligned_edge=LEFT)
        proj_intro_content = Text("创新性地开发了一套AI驱动自动化系统。基于Testplan、POD、Datasheet等实现智能绘制。", font_size=20).next_to(proj_intro_title, DOWN, aligned_edge=LEFT)

        self.play(Write(intro_title))
        self.play(Write(bg_title), FadeIn(bg_content))
        self.play(Write(goal_title), FadeIn(goal_content))
        self.play(Write(proj_intro_title), FadeIn(proj_intro_content))
        self.wait(2)

        self.play(FadeOut(intro_title, bg_title, bg_content, goal_title, goal_content, proj_intro_title, proj_intro_content))
