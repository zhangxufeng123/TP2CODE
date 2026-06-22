# filepath: show/scenes/s03_tp2code.py
from manim import *
from utils import create_header
from manim_voiceover import VoiceoverScene

def play_macro_transition(scene: VoiceoverScene):
    transition_text = VGroup(
        Text("但 Table2Sch 只是硬件侧的实现...", font_size=24, color=YELLOW),
        Text("如果我们将视角拉升？", font_size=24, color=YELLOW)
    ).arrange(DOWN, buff=0.4)
    
    with scene.voiceover(text="但刚才演示的这一切，仅仅只是硬件侧的实现。如果我们彻底拉升视角，来看一看全局生态呢？"):
        scene.play(Write(transition_text))
    scene.play(FadeOut(transition_text))

    header = create_header("5. 视角拉升：Testplan2Code (TP2Code) 全景架构")
    scene.play(FadeIn(header))

    # --- 左侧：解析层 ---
    box_tp2table = RoundedRectangle(width=2.8, height=1.8, color=PURPLE).shift(LEFT*4.5)
    lbl_tp2table = Text("TP2Table\n(LLM 智能解析)", font_size=18).move_to(box_tp2table)

    # --- 🌟 融合逻辑：双轨中间态 (保留了你的左右位置布局) ---
    box_ir_bg = RoundedRectangle(width=2.8, height=4.2, color=GRAY, fill_opacity=0.05).shift(LEFT*1.0)
    lbl_ir_main = Text("双轨中间表示层 (IR Database)", font_size=14, color=WHITE).next_to(box_ir_bg, UP, buff=0.1)

    box_ir_hw = RoundedRectangle(width=2.4, height=1.4, color=YELLOW).move_to(box_ir_bg).shift(UP*1.1)
    lbl_ir_hw = Text("HW 映射表\n(Pin 与机台资源)", font_size=16, color=YELLOW).move_to(box_ir_hw)

    box_ir_sw = RoundedRectangle(width=2.4, height=1.4, color=ORANGE).move_to(box_ir_bg).shift(DOWN*1.1)
    lbl_ir_sw = Text("SW 测试表\n(上电与寄存器信息)", font_size=16, color=ORANGE).move_to(box_ir_sw)

    ir_group = VGroup(box_ir_bg, lbl_ir_main, box_ir_hw, lbl_ir_hw, box_ir_sw, lbl_ir_sw)

    # --- 右侧：软硬件产物 (保留了你的布局和文本) ---
    box_hw = RoundedRectangle(width=2.8, height=1.5, color=BLUE).shift(RIGHT*2.5 + UP*1.2)
    lbl_hw = Text("Table2Sch\n(硬件原理图)", font_size=18).move_to(box_hw)
    hw_highlight = SurroundingRectangle(box_hw, color=YELLOW, buff=0.1)
    hw_desc = Text("刚才演示的部分", font_size=12, color=YELLOW).next_to(hw_highlight, UP)
    box_sw = RoundedRectangle(width=2.8, height=1.5, color=GREEN).shift(RIGHT*2.5 + DOWN*1.2)
    lbl_sw = Text("Table2Code\n(ATE 软件代码)", font_size=18).move_to(box_sw)

    spec_data = VGroup(
        Text("• 芯片封装 (Package)", font_size=12), Text("• 寄存器地址 (Reg Map)", font_size=12),
        Text("• Datasheet 特性", font_size=12), Text("• Testplan 核心参数", font_size=12)
    ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).next_to(box_sw, RIGHT, buff=0.5)
    spec_box = SurroundingRectangle(spec_data, color=GRAY, buff=0.2, fill_opacity=0.1)
    spec_title = Text("多源输入数据", font_size=12, color=GRAY_B).next_to(spec_box, UP, aligned_edge=LEFT, buff=0.15)

    # --- 箭头指向对应的双轨表 ---
    a1 = Arrow(box_tp2table.get_right(), box_ir_bg.get_left(), buff=0.1)
    a2 = Arrow(box_ir_hw.get_right(), box_hw.get_left(), buff=0.1, color=YELLOW)
    a3 = Arrow(box_ir_sw.get_right(), box_sw.get_left(), buff=0.1, color=ORANGE)
    a_hw2sw = CurvedArrow(box_hw.get_bottom(), box_sw.get_top(), angle=-TAU/4, color=BLUE_B, stroke_width=2)
    lbl_consistency = Text("基于原理图反馈 (软硬一致)", font_size=10, color=BLUE_B).next_to(a_hw2sw, RIGHT, buff=-0.2).shift(RIGHT*0.5)
    a_spec2sw = Arrow(spec_box.get_left(), box_sw.get_right(), color=GRAY_B)

    with scene.voiceover(text="这便是 Test plan to Code 的宏观全景架构。为了解决软硬件的数据需求差异，我们将核心枢纽解耦为“双轨模式”：上方是专供硬件的管脚和机台资源映射表，下方则是专供软件的上电时序与寄存器配置表。右上角是刚才演示的原理图自动化板块。"):
        scene.play(Create(box_tp2table), Write(lbl_tp2table))
        scene.play(GrowArrow(a1))
        scene.play(FadeIn(ir_group, shift=UP))
        scene.play(GrowArrow(a2), GrowArrow(a3))
        scene.play(Create(box_hw), Write(lbl_hw), Create(box_sw), Write(lbl_sw))
        scene.play(Create(hw_highlight), Write(hw_desc))
        scene.play(FadeOut(hw_highlight, hw_desc))

    desc = Text("ATE 代码生成融合了原理图拓扑、芯片封装、寄存器映射与 Datasheet，实现真正的软硬协同", font_size=16, color=GRAY).to_edge(DOWN)
    
    with scene.voiceover(text="更强大的是，下方的 A T E 代码生成，不仅读取了软件测试表，还会直接融合刚才生成的原理图真实拓扑结构、芯片封装和寄存器映射。实现真正的一键生成，软硬件强一致性。"):
        scene.play(Create(spec_box), Write(spec_title), LaggedStart(*[Write(d) for d in spec_data], lag_ratio=0.2))
        scene.play(GrowArrow(a_spec2sw))
        scene.play(Create(a_hw2sw), Write(lbl_consistency))
        scene.play(Indicate(box_sw, color=GREEN_A))
        scene.play(Write(desc))

    scene.play(FadeOut(Group(*scene.mobjects)))


def play_llm_tp2table(scene: VoiceoverScene):
    """7. 上游拓展：LLM 驱动的 TP2Table (带导航图过渡)"""
    header = create_header("6. 架构向左：TP2Table (大语言模型引入)")
    
    # ==========================================
    # 🌟 微缩导航图 (向左溯源) - 引入双轨概念
    # ==========================================
    nav_tp = RoundedRectangle(width=2, height=1, color=PURPLE).shift(LEFT*3.5)
    nav_lbl_tp = Text("Testplan", font_size=14).move_to(nav_tp)
    nav_ir = RoundedRectangle(width=2, height=1, color=YELLOW).shift(ORIGIN)
    nav_lbl_ir = Text("双轨 Table", font_size=14, color=YELLOW).move_to(nav_ir)
    nav_out = RoundedRectangle(width=2, height=1, color=GRAY).shift(RIGHT*3.5)
    nav_lbl_out = Text("产物 (Sch/Code)", font_size=14, color=GRAY).move_to(nav_out)

    nav_a1 = Arrow(nav_tp.get_right(), nav_ir.get_left(), buff=0.1)
    nav_a2 = Arrow(nav_ir.get_right(), nav_out.get_left(), buff=0.1, color=GRAY)
    
    mini_map = VGroup(nav_tp, nav_lbl_tp, nav_ir, nav_lbl_ir, nav_out, nav_lbl_out, nav_a1, nav_a2).shift(DOWN*0.5)

    with scene.voiceover(text="回到刚才的全景架构。如果我们以中间的双轨 Table 数据为锚点，向左侧，也就是向上游的原始需求端拓展。") as tracker:
        scene.play(FadeIn(header))
        scene.play(FadeIn(mini_map))

    focus_box = SurroundingRectangle(VGroup(nav_tp, nav_ir), color=RED, buff=0.2, stroke_width=4)
    with scene.voiceover(text="我们会遇到第一个难点：如何将人类编写的自然语言测试方案，自动分类转换成机器可读的 Table？这就需要大语言模型的介入。") as tracker:
        scene.play(Create(focus_box))
        scene.play(Indicate(nav_tp, color=PURPLE_B))
        scene.wait(tracker.duration - 1.5)

    scene.play(FadeOut(mini_map), FadeOut(focus_box))


    # ==========================================
    # 原有的 LLM TP2Table 逻辑
    # ==========================================
    raw_box = RoundedRectangle(width=4, height=1.5, color=GRAY).shift(LEFT*3.5 + UP*1)
    raw_lines = ['Spec: "Vth Test, Vds=10V,', 'force 250uA on Drain"']
    raw_text = VGroup(*[Text(line, font_size=16) for line in raw_lines]).arrange(DOWN, aligned_edge=LEFT).move_to(raw_box)
    ai_node = Circle(radius=1, color=PURPLE_A, fill_opacity=0.2).shift(RIGHT*0 + DOWN*1)
    ai_text = Text("LLM Engine\n(Qwen/DeepSeek)\n+ CoT 规则", font_size=14).move_to(ai_node)
    table_box = RoundedRectangle(width=4, height=2, color=YELLOW).shift(RIGHT*3.5 + UP*1)
    table_lines = ["Pin: Drain", "Force: 250uA", "Measure: V", "Connect: Short D-G"]
    table_text = VGroup(*[Text(line, font_size=14, color=YELLOW_C) for line in table_lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to(table_box)

    arrow1 = Arrow(raw_box.get_bottom(), ai_node.get_left(), path_arc=0.5)
    arrow2 = Arrow(ai_node.get_right(), table_box.get_bottom(), path_arc=0.5)
    desc = Text("将自然语言 Testplan 与 Datasheet 精准转化为机器可读的 Table 中间态", font_size=18).to_edge(DOWN)

    with scene.voiceover(text="如图所示，通过引入大语言模型引擎。它可以将人类工程师用自然语言编写的原始 Test plan 需求，精准推理并翻译成机器可读的 Table 中间态。"):
        scene.play(Create(raw_box), FadeIn(raw_text))
        scene.play(Create(arrow1))
        scene.play(Create(ai_node), Write(ai_text))
        scene.play(ai_node.animate.set_fill(PURPLE, opacity=0.6), run_time=1)
        scene.play(Create(arrow2))
        scene.play(Create(table_box), FadeIn(table_text))
        scene.play(Write(desc))

    scene.play(FadeOut(Group(*scene.mobjects)))


def play_ate_code_gen(scene: VoiceoverScene):
    """8. 下游拓展：ATE Code 自动生成 (带导航图过渡)"""
    header = create_header("7. 架构向右：Table2Code (ATE 软件代码自动生成)")
    
    # ==========================================
    # 🌟 微缩导航图 (向右衍生) - 融合你的修改
    # ==========================================
    nav_ir = RoundedRectangle(width=2, height=1, color=ORANGE).shift(LEFT*3.5)
    nav_lbl_ir = Text("SW 测试表", font_size=14, color=ORANGE).move_to(nav_ir)
    nav_hw = RoundedRectangle(width=2, height=1, color=BLUE).shift(RIGHT*1.5 + UP*1)
    nav_lbl_hw = Text("物理拓扑\nHB原理图", font_size=14, color=BLUE).move_to(nav_hw)
    nav_sw = RoundedRectangle(width=2, height=1, color=GREEN).shift(RIGHT*1.5 + DOWN*1)
    nav_lbl_sw = Text("A T E 代码", font_size=14, color=GREEN).move_to(nav_sw)

    nav_a1 = Arrow(nav_ir.get_right(), nav_hw.get_left(), buff=0.1, color=GRAY)
    nav_a2 = Arrow(nav_ir.get_right(), nav_sw.get_left(), buff=0.1, color=GREEN)
    nav_a3 = Arrow(nav_hw.get_bottom(), nav_sw.get_top(), buff=0.1, color=BLUE)

    mini_map = VGroup(nav_ir, nav_lbl_ir, nav_hw, nav_lbl_hw, nav_sw, nav_lbl_sw, nav_a1, nav_a2, nav_a3).shift(DOWN*0.5)

    with scene.voiceover(text="同理，再次回到全景架构。如果我们以提取好的 SW 测试表为基础，向右侧也就是产物端拓展。") as tracker:
        scene.play(FadeIn(header))
        scene.play(FadeIn(mini_map))

    focus_box = SurroundingRectangle(nav_sw, color=RED, buff=0.2, stroke_width=4)
    with scene.voiceover(text="由于硬件原理图的自动化我们已经实现，现在把目光聚焦在右下角，也就是 A T E 软件测试代码的自动生成上。") as tracker:
        scene.play(Create(focus_box))
        scene.play(Indicate(nav_sw, color=GREEN_B))
        scene.wait(tracker.duration - 1.5)

    scene.play(FadeOut(mini_map), FadeOut(focus_box))

    # ==========================================
    # ATE Code 生成逻辑 (保留你手工修改的代码文本与大小)
    # ==========================================
    ir_box = RoundedRectangle(width=3.2, height=1.6, color=ORANGE).shift(LEFT*4 + UP*1.5)
    ir_text = Text("SW 测试表\n(上电时序/测试向量/寄存器)", font_size=14).move_to(ir_box)
    dt_box = RoundedRectangle(width=3.2, height=1.6, color=BLUE).shift(LEFT*4 + DOWN*1.5)
    dt_text = Text("Tester 数字孪生模型\n(API 约束与物理拓扑)", font_size=14).move_to(dt_box)
    engine = RegularPolygon(n=6, color=GREEN, fill_opacity=0.2).scale(1.5).shift(ORIGIN)
    eng_text = Text("Jinja2\n模板引擎", font_size=18).move_to(engine)
    
    code_box = RoundedRectangle(width=4.4, height=3, color=WHITE).shift(RIGHT*4)
    
    # 🌟 完美保留你微调的代码文本
    code_lines = [
        "void Vth_Test() {", 
        "  // Auto-Generated", 
        "  Connect_Relay(K1_B);", 
        "  ACM200.ForceI(FV/FI, Value，VRange,IRange);", 
        "  ACM200.MeasureV();", 
        "}"
    ]
    code_text = VGroup(*[Text(line, font_size=14, color=GREEN_C) for line in code_lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to(code_box)

    # 🌟 修复点 2：统一设置箭头的 stroke_width=4，确保粗细完全一致
    a1 = Arrow(ir_box.get_right(), engine.get_left(), color=ORANGE, stroke_width=4)
    a2 = Arrow(dt_box.get_right(), engine.get_left(), color=BLUE, stroke_width=4)
    a3 = Arrow(engine.get_right(), code_box.get_left(), color=WHITE, stroke_width=4)
    
    desc = Text("结合硬件 Table 与机台 API 数字孪生，一键生成强一致性、免 Debug 的 C++/C# 测试程序", font_size=18, color=GREEN).to_edge(DOWN)

    with scene.voiceover(text="通过读取专供软件层的上电测试表，并结合测试机台的 A P I 数字孪生模型，金家兔 模板引擎可以在瞬间，自动生成可以直接在机台上跑的 C加加 代码，彻底消除人工手写的隐患。"):
        scene.play(Create(ir_box), Write(ir_text), Create(dt_box), Write(dt_text))
        scene.play(GrowArrow(a1), GrowArrow(a2))
        scene.play(Create(engine), Write(eng_text))
        scene.play(engine.animate.rotate(PI/2), run_time=1)
        scene.play(GrowArrow(a3))
        scene.play(Create(code_box), FadeIn(code_text))
        scene.play(Write(desc))

    scene.play(FadeOut(Group(*scene.mobjects)))


def play_auto_debug_ttr(scene: VoiceoverScene):
    header = create_header("8. 架构闭环：LLM 驱动的机台自动化 Debug")
    scene.play(FadeIn(header))

    # 🌟 完美保留你微调的高度 2.1
    code_box = RoundedRectangle(width=4.8, height=2.1, color=WHITE, fill_color=BLACK, fill_opacity=1).shift(UP*1.5 + LEFT*3.5)
    code_title = Text("ATE Code (Debug 模式)", font_size=14, color=GRAY).next_to(code_box, UP, buff=0.1)
    code_text_1 = Text("ACM200.ForceV(5.0); Connect_Relay(K1);", font_size=13, color=RED_B) 
    code_text_2 = Text("Wait(10.0 ms);", font_size=13, color=WHITE)
    code_text_3 = Text("float v = ACM200.MeasureV();", font_size=13, color=WHITE)
    code_lines = VGroup(code_text_1, code_text_2, code_text_3).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(code_box).shift(LEFT*0.2)

    # 🌟 完美保留你微调的半径 1.15
    llm_box = Circle(radius=1.15, color=PURPLE, fill_opacity=0.1).shift(UP*1.5 + RIGHT*3.5)
    llm_title = Text("LLM Agent 大脑", font_size=16, color=PURPLE).move_to(llm_box).shift(UP*0.7)

    tester_box = RoundedRectangle(width=6.5, height=3.2, color=BLUE).shift(DOWN*1.5)
    tester_title = Text("Tester API & Scope 波形采集", font_size=14, color=BLUE_B).move_to(tester_box.get_corner(UL) + RIGHT*1.5 + DOWN*0.4)
    scope_screen = Rectangle(width=6.0, height=2.0, color=GRAY, fill_color="#001100", fill_opacity=1).move_to(tester_box).shift(DOWN*0.2 + RIGHT*0.1)

    arrow_c2s = Arrow(code_box.get_bottom() + RIGHT*1.0, tester_box.get_top() + LEFT*1.5, path_arc=0.4, color=BLUE_B, stroke_width=4)
    lbl_c2s = Text("执行 API 下发机台", font_size=13, color=BLUE_B).next_to(arrow_c2s, LEFT, buff=0.1).shift(UP*0.05)
    arrow_s2l = Arrow(tester_box.get_top() + RIGHT*1.5, llm_box.get_bottom() + LEFT*0.3, path_arc=0.4, color=PURPLE_B, stroke_width=4)
    lbl_s2l = Text("采集波形 送入模型", font_size=13, color=PURPLE_B).next_to(arrow_s2l, RIGHT, buff=0.1)
    arrow_l2c = Arrow(llm_box.get_left(), code_box.get_right(), path_arc=0.2, color=GREEN, stroke_width=4)
    lbl_l2c = Text("重写控制代码", font_size=13, color=GREEN).next_to(arrow_l2c, UP, buff=0.1)

    # 🌟 完美保留你写的中文谐音 "滴bug"
    with scene.voiceover(text="最后是全景生态的最核心：Large Language Model 驱动的闭环自动 滴bug 技术。左侧是测试代码，右侧是充当大脑的大语言模型，下方是机台的示波器采集端。"):
        scene.play(Create(code_box), Write(code_title), FadeIn(code_lines))
        scene.play(Create(tester_box), Write(tester_title), Create(scope_screen))
        scene.play(Create(llm_box), Write(llm_title))
        
    with scene.voiceover(text="代码下发给机台执行，通过接口抓取真实波形数据送入 AI 大脑，由 AI 分析后再去重构代码，这就形成了一个极速的数据飞轮。"):
        scene.play(Create(arrow_c2s), FadeIn(lbl_c2s))
        scene.play(Create(arrow_s2l), FadeIn(lbl_s2l))
        scene.play(Create(arrow_l2c), FadeIn(lbl_l2c))

    # Case A: Deglitch
    stage1_title = Text("Case 1: 自动去毛刺 (排除继电器带电热切)", font_size=18, color=RED_A).to_edge(DOWN, buff=0.5)
    p0 = scope_screen.get_bottom() + LEFT*2.8 + UP*0.2; p1 = p0 + RIGHT*0.5; p2 = p1 + UP*1.4 
    p3 = p2 + RIGHT*0.2 + DOWN*0.8; p4 = p3 + RIGHT*0.2 + UP*1.0; p5 = p4 + RIGHT*0.6 + DOWN*0.2; p6 = scope_screen.get_bottom() + RIGHT*2.8 + UP*1.4 
    wave_glitch = VMobject(color=YELLOW).set_points_as_corners([p0, p1, p2, p3, p4, p5, p6])
    glitch_mark = Circle(radius=0.3, color=RED).move_to(p3 + UP*0.4)
    glitch_lbl = Text("带电热切导致致命毛刺", font_size=12, color=RED).next_to(glitch_mark, UP)

    with scene.voiceover(text="我们来看案例一。当前的程序时序由于先加电压、后关继电器，在示波器上出现了极其危险的热切毛刺。"):
        scene.play(Write(stage1_title))
        scene.play(Indicate(code_lines[0], color=RED))
        scene.play(Create(wave_glitch), run_time=1.5)
        scene.play(Create(glitch_mark), Write(glitch_lbl))

    llm_t1 = Text("1. 发现异常电压尖峰", font_size=12, color=RED_A)
    llm_t2 = Text("2. 排查: 存在继电器带电热切", font_size=12, color=WHITE)
    llm_t3 = Text("3. 决策: 重构时序为冷切", font_size=12, color=GREEN)
    llm_thoughts1 = VGroup(llm_t1, llm_t2, llm_t3).arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to(llm_box).shift(DOWN*0.1)
    new_code_1 = Text("Connect_Relay(K1); ACM200.ForceV(5.0); // AI:冷切", font_size=13, color=GREEN).move_to(code_lines[0], aligned_edge=LEFT)
    f_p0 = p0; f_p1 = p0 + RIGHT*0.4; f_p2 = f_p1 + UP*1.2; f_p3 = f_p2 + RIGHT*0.6 + UP*0.2; f_p4 = scope_screen.get_bottom() + RIGHT*2.8 + UP*1.4 
    wave_smooth = VMobject(color=GREEN).set_points_as_corners([f_p0, f_p1, f_p2, f_p3, f_p4])

    with scene.voiceover(text="大语言模型识别到尖峰特征，精准诊断出破坏性的继电器带电热切换，并瞬间主动重写底层代码，将时序倒转为冷切。可以明显看到，再次执行后波形变得非常平滑。"):
        scene.play(FadeIn(llm_thoughts1, shift=UP*0.2))
        scene.play(llm_box.animate.set_fill(PURPLE, opacity=0.3), run_time=0.5)
        scene.play(Transform(code_lines[0], new_code_1))
        scene.play(Transform(wave_glitch, wave_smooth), FadeOut(glitch_mark), FadeOut(glitch_lbl))

    scene.play(FadeOut(stage1_title), FadeOut(llm_thoughts1), llm_box.animate.set_fill(PURPLE, opacity=0.1))

    # Case B: TTR
    stage2_title = Text("Case 2: 极限测试时间压缩 (TTR)", font_size=18, color=BLUE_A).to_edge(DOWN, buff=0.5)
    sample_line_10ms = DashedLine(f_p4 + LEFT*0.5 + UP*0.5, f_p4 + LEFT*0.5 + DOWN*1.5, color=GRAY)
    sample_lbl_10ms = Text("MeasureV() @10.0ms (人工保守延时, 时间浪费!)", font_size=12, color=GRAY).next_to(sample_line_10ms, LEFT).align_to(sample_line_10ms, DOWN).shift(RIGHT*0.2, UP*0.2)
    
    with scene.voiceover(text="但这还不够。在案例二中，波形虽然平滑了，但原代码里工程师出于保守，设置了长达 10 毫秒的死区等待时间，这是测试量产的巨大浪费。"):
        scene.play(Write(stage2_title))
        scene.play(Indicate(code_lines[1], color=YELLOW))
        scene.play(Create(sample_line_10ms), Write(sample_lbl_10ms))

    llm_t4 = Text("1. 建立时间极短 (已去毛刺)", font_size=12, color=BLUE_A)
    llm_t5 = Text("2. Wait(10ms) 存在 90% 冗余", font_size=12, color=WHITE)
    llm_t6 = Text("3. 决策: 执行极限 TTR 压缩", font_size=12, color=GREEN)
    llm_thoughts2 = VGroup(llm_t4, llm_t5, llm_t6).arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to(llm_box).shift(DOWN*0.1)
    new_code_2 = Text("Wait(1.0 ms);  // AI: 极限 TTR 压缩", font_size=13, color=GREEN).move_to(code_lines[1], aligned_edge=LEFT)
    sample_line_1ms = DashedLine(f_p2 + RIGHT*0.2 + UP*0.5, f_p2 + RIGHT*0.2 + DOWN*1.5, color=GREEN)
    sample_lbl_1ms = Text("MeasureV() @1.0ms (最快切入点)", font_size=12, color=GREEN).next_to(sample_line_1ms, RIGHT).align_to(sample_line_1ms, DOWN).shift(UP*0.2)

    with scene.voiceover(text="此时，AI 大脑发现波形建立极快，自动执行极限时间压缩。瞬间将采样点提前到了刚刚达到稳定的最佳切入点，实现量产时间压缩收益的最大化。"):
        scene.play(FadeIn(llm_thoughts2, shift=UP*0.2))
        scene.play(llm_box.animate.set_fill(PURPLE, opacity=0.3), run_time=0.5)
        scene.play(Transform(code_lines[1], new_code_2))
        scene.play(Transform(sample_line_10ms, sample_line_1ms), Transform(sample_lbl_10ms, sample_lbl_1ms))

    scene.play(FadeOut(Group(*scene.mobjects)))