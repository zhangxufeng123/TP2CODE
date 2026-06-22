# filepath: show/scenes/s01_intro.py
from manim import *
from utils import create_header
from manim_voiceover import VoiceoverScene

def play_intro(scene: VoiceoverScene):
    """1. 封面与项目定位"""
    title = Text("TP to Code: 测试开发全流程自动化系统Demo架构演示", color=BLUE_B).scale(0.8)
    subtitle = Text("从 Test plan 到 原理图(Handler Board) 与 A T E Code 的一键生成", font_size=24, color=GRAY).next_to(title, DOWN, buff=0.3)
    author = Text("架构演进与核心技术演示", font_size=20, color=YELLOW).to_edge(DOWN, buff=1)
    
    with scene.voiceover(text="欢迎观看 TP to Code，测试开发全流程自动化系统演示。本系统旨在实现从芯片测试方案到原理图，再到 A T E 软件代码的一键生成。") as tracker:
        scene.play(Write(title))
        scene.play(FadeIn(subtitle, shift=UP))
        scene.play(FadeIn(author))
    
    scene.play(FadeOut(title, subtitle, author))

def play_pain_points(scene: VoiceoverScene):
    """2. 行业痛点"""
    header = create_header("1. 行业痛点：SoC 复杂度爆发下的测试困境")
    
    pain_points = VGroup(
        Text("• 流程割裂：Testplan → 原理图(HB) → ATE Code 高度依赖人工转换", font_size=20),
        Text("• 效率极低：上万测试项，人工绘制原理图耗时数周", font_size=20),
        Text("• 资源冲突：ATE 资源复杂，脑内映射(Mental Mapping)极易失效", font_size=20),
        Text("• 检查低效：目前工作流严重依赖 Checklist 人工核对，费时费力", font_size=20, color=RED_B),
        Text("• 极易出错：海量 Net 名称极度相似（仅位号不同），人工 Review 极易漏错", font_size=20, color=RED_B),
        Text("• 知识流失：缺乏“测试知识抽象层”，老工程师经验难以标准化复用", font_size=20, color=YELLOW),
    ).arrange(DOWN, aligned_edge=LEFT, buff=0.45).shift(DOWN * 0.3)
    
    scene.play(FadeIn(header))
    
    with scene.voiceover(text="在 S O C 复杂度爆发的今天，传统的测试开发面临着严峻的困境。工作流程割裂、画图效率极低、机台资源极易冲突，并且严重依赖人工核对 Check list，非常容易出现网络名相似导致的短路或开路错误。老工程师的宝贵经验也难以沉淀复用。") as tracker:
        scene.play(LaggedStart(*[FadeIn(line, shift=RIGHT) for line in pain_points], lag_ratio=0.3), run_time=tracker.duration)
    
    scene.play(FadeOut(pain_points, header))