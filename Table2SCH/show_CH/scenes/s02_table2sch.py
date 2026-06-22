# filepath: show/scenes/s02_table2sch.py
from manim import *
from utils import create_header
from manim_voiceover import VoiceoverScene

# ==========================================
# 行业规范与通用组件
# ==========================================
ZONES_DATA = [
    {"name": "1. Socket Fanout\n(芯片座扇出)", "color": GRAY, "w": 1.4, "h": 4.2, "pos": [-3.6, 0.2, 0.0]},
    {"name": "2. Relays Zone\n(Kelvin/MUX 继电器)", "color": ORANGE, "w": 2.8, "h": 2.2, "pos": [-1.3, 1.2, 0.0]},
    {"name": "3. Active Circuits\n(LDO/OPA 等辅助电路)", "color": GREEN, "w": 2.8, "h": 2.2, "pos": [1.7, 1.2, 0.0]},
    {"name": "4. Relay Coils\n(CBIT 线圈控制矩阵)", "color": RED, "w": 5.8, "h": 1.8, "pos": [0.2, -1.0, 0.0]},
    {"name": "5. Ground Ties\n(FL/SL 接地网络)", "color": PURPLE, "w": 1.2, "h": 4.2, "pos": [3.9, 0.2, 0.0]}
]

def draw_module(data):
    box = RoundedRectangle(width=data["w"], height=data["h"], color=data["color"], corner_radius=0.1, fill_opacity=0.1).move_to(data["pos"])
    label = Text(data["name"], font_size=12, color=WHITE).move_to(box.get_center())
    max_allowable_width = data["w"] * 0.9
    if label.width > max_allowable_width: label.width = max_allowable_width
    return VGroup(box, label)

# ==========================================
# 场景实现
# ==========================================
def play_smart_mapping(scene: VoiceoverScene):
    """1. 演示 SmartPinMapper 智能规则推理 (带有宏观架构图过渡)"""
    header = create_header("2. 局部聚焦 (Table2Sch)：SmartPinMapper 智能规则推理")
    
    # ==========================================
    # 🌟 新增：宏观架构图过渡动画 (先给地图，再走局部)
    # ==========================================
    box_tp = RoundedRectangle(width=2.5, height=1.5, color=PURPLE).shift(LEFT*4)
    lbl_tp = Text("Testplan / 需求", font_size=16).move_to(box_tp)
    
    box_ir = RoundedRectangle(width=2.0, height=3.0, color=YELLOW).shift(LEFT*0.5)
    lbl_ir = Text("中间映射表\n(Table)", font_size=18, color=YELLOW).move_to(box_ir)
    
    box_sch = RoundedRectangle(width=2.5, height=1.2, color=BLUE).shift(RIGHT*3 + UP*1)
    lbl_sch = Text("Table2Sch\n(原理图自动化)", font_size=16).move_to(box_sch)
    
    box_code = RoundedRectangle(width=2.5, height=1.2, color=GREEN).shift(RIGHT*3 + DOWN*1)
    lbl_code = Text("Table2Code\n(A T E 代码)", font_size=16).move_to(box_code)

    a1 = Arrow(box_tp.get_right(), box_ir.get_left(), buff=0.1)
    a2 = Arrow(box_ir.get_right(), box_sch.get_left(), buff=0.1)
    a3 = Arrow(box_ir.get_right(), box_code.get_left(), buff=0.1)

    macro_group = VGroup(box_tp, lbl_tp, box_ir, lbl_ir, box_sch, lbl_sch, box_code, lbl_code, a1, a2, a3)
    macro_group.shift(DOWN*0.5) # 整体下移，给标题留出空间

    # 1. 浮现全景架构
    with scene.voiceover(text="面对上述严峻的挑战， T P to Code 全景架构给出了它的答案。") as tracker:
        scene.play(FadeIn(header))
        scene.play(
            FadeIn(box_tp, shift=RIGHT), FadeIn(lbl_tp, shift=RIGHT),
            run_time=tracker.duration * 0.3
        )
        scene.play(
            GrowArrow(a1), FadeIn(box_ir, shift=UP), FadeIn(lbl_ir, shift=UP),
            run_time=tracker.duration * 0.3
        )
        scene.play(
            GrowArrow(a2), GrowArrow(a3),
            FadeIn(box_sch, shift=LEFT), FadeIn(lbl_sch, shift=LEFT),
            FadeIn(box_code, shift=LEFT), FadeIn(lbl_code, shift=LEFT),
            run_time=tracker.duration * 0.4
        )

    # 2. 锁定并高亮 Table2Sch
    focus_box = SurroundingRectangle(box_sch, color=RED, buff=0.1, stroke_width=4)
    with scene.voiceover(text="今天，我们先将目光聚焦在架构的右上角：底层的硬件原理图自动化生成，也就是 Table to Schematic 模块。") as tracker:
        scene.play(Create(focus_box))
        scene.play(Indicate(box_sch, color=BLUE_B, scale_factor=1.1))
        scene.wait(tracker.duration - 1.5)
        
    # 3. 清场，留下标题，平滑进入局部代码演示
    scene.play(FadeOut(macro_group), FadeOut(focus_box))


    # ==========================================
    # 原有的 SmartPinMapper 逻辑
    # ==========================================
    table_headers = VGroup(
        Text("Logical Net", font_size=18, color=BLUE),
        Text("Resources", font_size=18, color=YELLOW),
        Text("Connect Type", font_size=18, color=GREEN),
        Text("Active Circuits", font_size=18, color=ORANGE)
    ).arrange(RIGHT, buff=0.8).shift(UP * 1.5)
    
    row = VGroup(
        Text("VDD_CORE", font_size=16),
        Text("FPVIe", font_size=16, color=YELLOW),
        Text("Kelvin", font_size=16, color=GREEN),
        Text("ChargeRelease", font_size=16, color=ORANGE)
    ).arrange(RIGHT, buff=1.0).next_to(table_headers, DOWN, buff=0.5)

    rule_box = SurroundingRectangle(row, color=YELLOW, buff=0.2)
    rule_text = Text("Rule: If 'VDD' in NetName -> Force Kelvin + FPVIe + ChargeRelease", font_size=14, color=YELLOW).next_to(rule_box, DOWN)

    with scene.voiceover(text="系统内部搭载了 Smart Pin Mapper 智能引脚映射规则。例如，当它识别到网络名包含 V D D 的电源Pin时，会自动匹配大电流测试资源，强制使用 Kelvin 连接，并自动挂载 Charge Release 放电辅助电路。") as tracker:
        scene.play(Write(table_headers))
        scene.play(Write(row))
        scene.play(Create(rule_box), FadeIn(rule_text))
    
    scene.wait(1)
    scene.play(FadeOut(Group(*scene.mobjects)))


def play_mux_routing(scene: VoiceoverScene):
    header = create_header("3. 局部聚焦 (Table2Sch)：从 Mapping 配置到 MUX 路由")
    scene.play(FadeIn(header))

    table_win = RoundedRectangle(width=9, height=2.5, color=WHITE, fill_opacity=0.1).shift(UP*1)
    win_title = Text("Pin Mapping Table", font_size=16, color=BLUE).next_to(table_win, UP, aligned_edge=LEFT)
    headers = VGroup(Text("Pin Name", font_size=14, color=GRAY), Text("Resource Types", font_size=14, color=GRAY), Text("Connect Type", font_size=14, color=GRAY)).arrange(RIGHT, buff=1.5).shift(UP*1.5)
    row = VGroup(Text("PIN_A1", font_size=16), Text("[ACM200, QTMU]", font_size=16, color=YELLOW), Text("Relay", font_size=16, color=GREEN)).arrange(RIGHT, buff=1.5).next_to(headers, DOWN, buff=0.5)
    hl_res = SurroundingRectangle(row[1:3], color=YELLOW, buff=0.1)
    desc_gui = Text("当一个 Pin 勾选了多个并行资源 (如 ACM200 和 QTMU) 时...", font_size=18).to_edge(DOWN)

    with scene.voiceover(text="在图形界面中，当用户为一个引脚勾选了多个并行的机台资源，比如同时勾选了 A C M 200 和 QTMU 时。"):
        scene.play(Create(table_win), Write(win_title), FadeIn(headers))
        scene.play(Write(row))
        scene.play(Create(hl_res), Write(desc_gui))

    scene.play(FadeOut(table_win, win_title, headers, hl_res, desc_gui), row.animate.shift(UP*1.5).scale(0.8))
    
    socket = Dot(LEFT * 5, color=WHITE, radius=0.15)
    lbl_socket = Text("Socket Pin\n(PIN_A1)", font_size=14).next_to(socket, LEFT)
    mux_relay = Rectangle(height=2, width=1.2, color=ORANGE).shift(LEFT * 1)
    lbl_mux = Text("MUX\nRelay", font_size=14).move_to(mux_relay)
    inst_acm = Rectangle(height=1.2, width=1.8, color=BLUE).shift(RIGHT * 3 + UP * 1.5)
    lbl_acm = Text("Board: ACM200", font_size=14).move_to(inst_acm)
    inst_qtmu = Rectangle(height=1.2, width=1.8, color=GREEN).shift(RIGHT * 3 + DOWN * 1.5)
    lbl_qtmu = Text("Board: QTMU", font_size=14).move_to(inst_qtmu)
    l_soc_mux = Line(socket.get_right(), mux_relay.get_left())
    l_mux_acm = Line(mux_relay.get_corner(UR), inst_acm.get_left(), color=GRAY)
    l_mux_qtmu = Line(mux_relay.get_corner(DR), inst_qtmu.get_left(), color=GRAY)

    with scene.voiceover(text="系统会自动在原理图中插入多路复用继电器。"):
        scene.play(
            TransformFromCopy(row[0], socket), Write(lbl_socket),
            TransformFromCopy(row[2], mux_relay), Write(lbl_mux),
            TransformFromCopy(row[1], inst_acm), Write(lbl_acm),
            TransformFromCopy(row[1], inst_qtmu), Write(lbl_qtmu)
        )
        scene.play(Create(l_soc_mux), Create(l_mux_acm), Create(l_mux_qtmu))
        scene.play(FadeOut(row))

    signal = Dot(color=YELLOW, radius=0.1)
    desc_mux1 = Text("系统自动插入 MUX Relay，默认导通 ACM200", font_size=18, color=BLUE).to_edge(DOWN)
    with scene.voiceover(text="默认情况下，信号会导通向主要的供电或测量通道。"):
        scene.play(Write(desc_mux1))
        l_mux_acm.set_color(BLUE)
        scene.add(signal)
        scene.play(MoveAlongPath(signal, l_soc_mux), run_time=0.4)
        scene.play(MoveAlongPath(signal, Line(mux_relay.get_corner(UR), inst_acm.get_left())), run_time=0.4)
        scene.play(Indicate(inst_acm))
        scene.play(FadeOut(signal))

    desc_mux2 = Text("测试程序(ATE Code)控制 Relay，动态切换至 QTMU 通路", font_size=18, color=GREEN).to_edge(DOWN)
    with scene.voiceover(text="在代码执行期间，测试程序可以直接向该继电器发送控制指令，将物理通路动态无缝切换到 QTMU 等其他测试板卡上。"):
        scene.play(Transform(desc_mux1, desc_mux2))
        l_mux_acm.set_color(GRAY)
        l_mux_qtmu.set_color(GREEN)
        signal2 = Dot(color=GREEN, radius=0.1).move_to(socket.get_right())
        scene.add(signal2)
        scene.play(MoveAlongPath(signal2, l_soc_mux), run_time=0.4)
        scene.play(MoveAlongPath(signal2, Line(mux_relay.get_corner(DR), inst_qtmu.get_left())), run_time=0.4)
        scene.play(Indicate(inst_qtmu))
    
    scene.play(FadeOut(Group(*scene.mobjects)))


def play_auto_numbering(scene: VoiceoverScene):
    header = create_header("4. 局部聚焦 (Table2Sch)：网络命名、自动打标与防错")
    scene.play(FadeIn(header))

    step1_title = Text("1. 器件自动位号 (Site 隔离)", font_size=20, color=BLUE_B).to_edge(UP).shift(DOWN*1.2)
    ic_box = Rectangle(height=1.2, width=1.5, color=BLUE_C).shift(LEFT * 2)
    ic_label = Text("LDO", font_size=16).move_to(ic_box)
    ref_ic_raw = Text("U?", font_size=24, color=RED).next_to(ic_box, UP)
    res_box = Rectangle(height=0.6, width=1.5, color=GREEN_C).shift(RIGHT * 2)
    res_label = Text("Resistor", font_size=14).move_to(res_box)
    ref_res_raw = Text("R?", font_size=24, color=RED).next_to(res_box, UP)

    with scene.voiceover(text="接下来是极其重要的网络打标与防错机制。我们知道，A T E 载板设计最怕的就是人工复制粘贴造成的位号和网络冲突。"):
        scene.play(Write(step1_title))
        scene.play(Create(ic_box), Write(ic_label), FadeIn(ref_ic_raw), Create(res_box), Write(res_label), FadeIn(ref_res_raw))

    ref_ic_new = Text("U1_S1", font_size=24, color=GREEN).move_to(ref_ic_raw)
    ref_res_new = Text("R1_S1", font_size=24, color=GREEN).move_to(ref_res_raw)
    subtitle1 = Text("根据 Site 自动分配独立位号，避免冲突", font_size=16, color=YELLOW).to_edge(DOWN, buff=1.0)
    with scene.voiceover(text="系统会自动为所有生成的元器件注入当前所属的 Site 后缀，并执行自增编号，完美实现器件的物理隔离。"):
        scene.play(Transform(ref_ic_raw, ref_ic_new), Transform(ref_res_raw, ref_res_new))
        scene.play(Write(subtitle1))
    scene.play(FadeOut(VGroup(step1_title, subtitle1, ic_box, ic_label, ref_ic_raw, res_box, res_label, ref_res_raw)))

    step2_title = Text("2. 智能网络分配 (Direct vs Kelvin)", font_size=20, color=BLUE_B).to_edge(UP).shift(DOWN*1.2)
    net_raw = Text("Base Net: VDD_CORE", font_size=20, color=WHITE).shift(UP * 1)
    dir_arrow = Arrow(net_raw.get_bottom(), LEFT*3 + DOWN*0.5, color=GRAY)
    dir_text = Text("Direct Mode", font_size=14, color=GRAY).next_to(dir_arrow, LEFT)
    dir_net = Text("VDD_CORE_S1", font_size=18, color=GREEN).next_to(dir_arrow, DOWN).shift(LEFT*2)
    kel_arrow = Arrow(net_raw.get_bottom(), RIGHT*3 + DOWN*0.5, color=YELLOW)
    kel_text = Text("Kelvin Mode", font_size=14, color=YELLOW).next_to(kel_arrow, RIGHT)
    kel_f_net = Text("VDD_CORE_F_S1 (Force)", font_size=18, color=ORANGE).next_to(kel_arrow, DOWN).shift(RIGHT*1)
    kel_s_net = Text("VDD_CORE_S_S1 (Sense)", font_size=18, color=BLUE_C).next_to(kel_f_net, DOWN)
    subtitle2 = Text("F/S 网络自动分离，精准打通大电流与电压采样路径", font_size=16, color=YELLOW).to_edge(DOWN, buff=1.0)

    with scene.voiceover(text="在网络命名方面，如果是普通的 Direct 连接，系统会直接打上网络标签。如果是 Kelvin 连线，系统则会自动将网络分离为 Force 和 Sense 两条相互独立的走线。"):
        scene.play(Write(step2_title), FadeIn(net_raw))
        scene.play(GrowArrow(dir_arrow), Write(dir_text), FadeIn(dir_net))
        scene.play(GrowArrow(kel_arrow), Write(kel_text), FadeIn(kel_f_net), FadeIn(kel_s_net))
        scene.play(Write(subtitle2))
    scene.play(FadeOut(step2_title), FadeOut(subtitle2), FadeOut(dir_arrow), FadeOut(dir_text), FadeOut(dir_net), FadeOut(net_raw), FadeOut(kel_arrow), FadeOut(kel_text))

    kel_group = VGroup(kel_f_net, kel_s_net)
    scene.play(kel_group.animate.arrange(DOWN, aligned_edge=RIGHT).move_to(LEFT * 3.5 + DOWN * 1.0))
    step3_title = Text("3. 接口对齐与防 Open (开路) 校验", font_size=20, color=BLUE_B).to_edge(UP).shift(DOWN*0.7)
    pogo_box = Rectangle(height=2.5, width=2, color=PURPLE).move_to(RIGHT * 3.0 + DOWN * 1.0)
    pogo_label = Text("Pogo\nConnector", font_size=16).move_to(pogo_box)
    l1 = Line(kel_f_net.get_right(), pogo_box.get_left() + UP*0.3, color=ORANGE)
    l2 = Line(kel_s_net.get_right(), pogo_box.get_left() + DOWN*0.3, color=BLUE_C)
    csv_box = RoundedRectangle(height=1.5, width=4.5, color=WHITE, fill_opacity=0.1).move_to(UP * 1.1 + RIGHT * 1.0)
    csv_title = Text("Pogo_Netlist.csv (Reference)", font_size=14, color=YELLOW).next_to(csv_box, UP, buff=0.1)
    csv_item1 = Text("VDD_CORE_F_S1", font_size=12, color=WHITE)
    csv_item2 = Text("VDD_CORE_S_S1", font_size=12, color=WHITE)
    csv_content = VGroup(csv_item1, csv_item2).arrange(DOWN, aligned_edge=LEFT).move_to(csv_box)

    with scene.voiceover(text="所有生成的网络名会直接导出为 C S V 文件清单，用于和机台端的 Pogo 连接器进行精确的 字符串 交叉比对。这能够百分之百拦截引脚悬空和漏连等低级错误。"):
        scene.play(Write(step3_title))
        scene.play(Create(pogo_box), Write(pogo_label), Create(l1), Create(l2))
        scene.play(Create(csv_box), Write(csv_title), FadeIn(csv_content))
        scan_line = Line(csv_box.get_left(), csv_box.get_right(), color=GREEN).move_to(csv_box.get_top())
        scene.add(scan_line)
        scene.play(scan_line.animate.move_to(csv_box.get_bottom()), run_time=1.5)
        scene.remove(scan_line)
        match1 = Text("  ✅ MATCH", font_size=12, color=GREEN).next_to(csv_item1, RIGHT)
        match2 = Text("  ✅ MATCH", font_size=12, color=GREEN).next_to(csv_item2, RIGHT)
        scene.play(Write(match1), Write(match2))
        subtitle3 = Text("预导出 CSV 进行 Netlist 交叉比对，100% 拦截引脚悬空错漏", font_size=18, color=GREEN).to_edge(DOWN, buff=1.0)
        scene.play(Write(subtitle3))
    scene.play(FadeOut(Group(*scene.mobjects)))


def play_layout_engine(scene: VoiceoverScene):
    header = create_header("5. 局部聚焦 (Table2Sch)：LayoutEngine 有序渲染过程")
    scene.play(FadeIn(header))

    sheet = Rectangle(height=5.5, width=9.5, color=WHITE, fill_opacity=0.05).shift(DOWN*0.2)
    sheet_label = Text("Site_1.kicad_sch", font_size=14, color=WHITE).next_to(sheet, UP, aligned_edge=LEFT,buff=0.15)
    desc = Text("有序渲染：Socket Pin扇出 -> 继电器 -> 辅助电路 -> 线圈 -> 接地", font_size=16, color=YELLOW_A).to_edge(DOWN)

    with scene.voiceover(text="底层引擎生成原理图时，并不会随意摆放器件。Lay Out Engine 会严格遵守 A T E 硬件工程师的排版规范，从左到右依次有序渲染：引脚扇出、切换继电器、辅助有源电路、控制线圈，最后是统一的接地网。该部分布局算法可优化至根据T E工作习惯保持一致") as tracker:
        scene.play(Create(sheet), Write(sheet_label))
        for z_data in ZONES_DATA:
            mod = draw_module(z_data)
            scene.play(FadeIn(mod, shift=UP*0.2), run_time=0.6)
        scene.play(Write(desc))
        
    scene.play(FadeOut(Group(*scene.mobjects)))


def play_hierarchical_sheets(scene: VoiceoverScene):
    header = create_header("6. 宏观项目：SchGenerator 层次原理图架构")
    scene.play(FadeIn(header))

    t1 = Text("GUI Setup Input: Total Sites = ", font_size=20, color=YELLOW)
    t2 = Text("4", font_size=20, color=YELLOW)
    config_val = VGroup(t1, t2).arrange(RIGHT, buff=0.1).to_edge(UP).shift(DOWN*1.2)
    master = Rectangle(width=3.5, height=1.5, color=GOLD).shift(UP * 0.5)
    lbl_master = Text("Master_Project.sch (Root)", font_size=14).move_to(master)
    pogo_group = VGroup(*[VGroup(Rectangle(width=2.5, height=0.6, color=PURPLE), Text("Pogo_Resource.sch", font_size=10)) for _ in range(2)]).arrange(DOWN, buff=0.2).shift(RIGHT * 4 + UP * 0.5)
    dots = Text("...", font_size=24, color=PURPLE).next_to(pogo_group, DOWN, buff=0.1)
    a_pogo = Arrow(master.get_right(), pogo_group.get_left(), color=PURPLE)
    sites = VGroup(*[Rectangle(width=1.8, height=1, color=BLUE) for _ in range(4)]).arrange(RIGHT, buff=0.4).shift(DOWN * 2)
    lbl_sites = VGroup(*[Text(f"Site_{i+1}.sch", font_size=10) for i in range(4)])
    for i, s in enumerate(sites): lbl_sites[i].move_to(s)
    a_sites = Arrow(master.get_bottom(), sites.get_top(), color=BLUE)

    desc_text1 = Text("假设在 GUI Setup Config 中设置 Total Sites 为 4", font_size=18, color=YELLOW)
    desc_text2 = Text("SchGenerator 将自动生成 4 份独立的 Site 子图纸，并与公用 Pogo 库挂载至 Master 主树", font_size=16, color=WHITE)
    desc_group = VGroup(desc_text1, desc_text2).arrange(DOWN, buff=0.2).to_edge(DOWN, buff=0.5)

    with scene.voiceover(text="以 华锋 S T S 8 3 0 0 测试机台为例，在完成了局部渲染后，我们来到宏观项目架构。假设用户在图形界面的Set Up 配置的 G U I 里，将 Total Sites 设置为四 site。"):
        scene.play(Write(config_val))
        scene.play(Indicate(t2, color=ORANGE, scale_factor=1.5))
        scene.play(Write(desc_group))

    with scene.voiceover(text="系统将创建一个 Master 根文件。首先，它会自动向右侧挂载测试机台公用的 Pogo 接口库图纸。"):
        scene.play(Create(master), Write(lbl_master))
        scene.play(GrowArrow(a_pogo), Create(pogo_group), FadeIn(dots))

    with scene.voiceover(text="紧接着，最核心的一步：它会批量生成刚才演示的 4 份相互独立的硬件子图纸，并将它们完美索引至主层级网络中。整个复杂的硬件项目结构瞬间构清晰完毕。"):
        scene.play(GrowArrow(a_sites), Create(sites), Write(lbl_sites))

    scene.play(FadeOut(Group(*scene.mobjects)))