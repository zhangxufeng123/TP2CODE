# filepath: show/scenes/s04_conclusion.py
from manim import *
from utils import create_header
from manim_voiceover import VoiceoverScene

def play_conclusion(scene: VoiceoverScene):
    """9. 结语"""
    header = create_header("终极愿景：测试工程师 (TE) 的角色蜕变")
    
    impact = VGroup(
        Text("🔧 过去：深陷繁琐的连线、查表、写模板代码 (代码实现者)", font_size=22, color=GRAY),
        Text("🧠 未来：聚焦于测试方法学、DFT 规划与良率优化 (架构设计者)", font_size=22, color=WHITE),
        Text("🚀 价值：开发周期缩短 80%，软硬强一致性，知识资产沉淀", font_size=22, color=YELLOW),
    ).arrange(DOWN, aligned_edge=LEFT, buff=0.8)

    with scene.voiceover(text="以上就是整个项目的全貌。我们的终极愿景是：解放测试工程师。让他们从繁琐连线、查表 和疯狂复制模板代码中 挣脱出来，彻底蜕变为 聚焦于测试方法学 和良率优化的架构设计者。"):
        scene.play(FadeIn(header))
        scene.play(FadeIn(impact, shift=UP))

    scene.play(FadeOut(impact), FadeOut(header))
    
    final_text = VGroup(
        Text("TP2Code 全景生态", font_size=36, color=BLUE_B),
        Text("引领半导体测试的自动化革命", font_size=36, color=BLUE_B)
    ).arrange(DOWN, buff=0.4)

    final_sub = Text("Thanks for watching", font_size=20, color=GRAY).next_to(final_text, DOWN, buff=1)
    
    with scene.voiceover(text="T P to Code 生态，旨在用软件和 AI，引领半导体测试的自动化革命。感谢您的观看。"):
        scene.play(Write(final_text))
        scene.play(FadeIn(final_sub))