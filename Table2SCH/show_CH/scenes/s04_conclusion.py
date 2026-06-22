from manim import *

class S04_Conclusion(Scene):
    def construct(self):
        # 4. Results & Value
        val_title = Text("1.6 实践价值", font_size=36, color=BLUE).to_edge(UP)

        table = Table(
            [["3-7天/板", "10-30分钟/板", "80-100倍 ⚡"],
             ["15-20%", "1-2%", "85%降低 ✅"],
             ["基本为0", "80%以上", "显著提升 🔄"],
             ["2-3个月", "3天", "90%缩短 📚"]],
            col_labels=[Text("改进前 (传统)"), Text("改进后 (AI赋能)"), Text("提升幅度")],
            row_labels=[Text("设计时间"), Text("错误率"), Text("复用率"), Text("培训周期")],
            include_outer_lines=True,
            element_to_mobject=Text
        ).scale(0.4).next_to(val_title, DOWN, buff=0.5)

        self.play(Write(val_title))
        self.play(FadeIn(table))
        self.wait(4)
        self.play(FadeOut(val_title, table))

        # 5. Security & Conclusion
        sec_title = Text("2. 信息安全 & 3. 可推广性", font_size=36, color=BLUE).to_edge(UP)

        sec_content = Text("🔒 核心技术资产隔离：所有AI操作均在本地离线执行，禁止上传外部AI。", font_size=24, color=RED).next_to(sec_title, DOWN, buff=1)
        fut_content = Text("🚀 可推广性分析：基于SystemC模型的跨部门协同仿真框架，\n实现DE仿真模型复用和打板前联合仿真闭环。", font_size=24, color=GREEN).next_to(sec_content, DOWN, buff=1)

        self.play(Write(sec_title))
        self.play(FadeIn(sec_content))
        self.play(FadeIn(fut_content))
        self.wait(4)
        self.play(FadeOut(sec_title, sec_content, fut_content))

        # End
        end_text = Text("感谢您的聆听！", font_size=48, color=YELLOW)
        self.play(Write(end_text))
        self.wait(3)
