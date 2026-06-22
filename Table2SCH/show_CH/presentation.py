# filepath: show/presentation.py
import os
import sys

# =====================================================================
# 🌟 终极必杀技：在所有包导入之前，强行绑定环境变量！
# 这样底层无论怎么调用，都只会去硅基流动，彻底屏蔽你电脑系统的干扰。
# =====================================================================
os.environ["OPENAI_API_KEY"] = "sk-qpizcnxobiyaktpetewcgbqpsqbdellpumfnayxsdvorozrh"
os.environ["OPENAI_BASE_URL"] = "https://api.siliconflow.cn/v1"

from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.openai import OpenAIService 

# 路径注入
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入拆分好的各个场景模块
from scenes.s01_intro import play_intro, play_pain_points
from scenes.s02_table2sch import (
    play_smart_mapping, 
    play_mux_routing, 
    play_auto_numbering, 
    play_layout_engine, 
    play_hierarchical_sheets
)
from scenes.s03_tp2code import play_macro_transition, play_llm_tp2table, play_ate_code_gen, play_auto_debug_ttr
from scenes.s04_conclusion import play_conclusion

class Table2SchPresentation(VoiceoverScene):
    def construct(self):
        # 🌟 修复：硅基流动的 voice 参数必须带有模型前缀
        self.set_speech_service(
            OpenAIService(
                model="FunAudioLLM/CosyVoice2-0.5B", 
                voice="FunAudioLLM/CosyVoice2-0.5B:charles",  # 👈 这里改成了完整的音色 ID
                transcription_model=None # 禁用本地转录防报错
            )
        )

        # 1. 序章
        play_intro(self)
        play_pain_points(self)
        
        # 2. 局部聚焦 (Table2Sch)
        play_smart_mapping(self)
        play_mux_routing(self)
        play_auto_numbering(self)
        play_layout_engine(self)
        play_hierarchical_sheets(self) 

        # 3. 视角拉升 (TP2Code)
        play_macro_transition(self)
        play_llm_tp2table(self)
        play_ate_code_gen(self)
        play_auto_debug_ttr(self) 
        
        # 4. 终章
        play_conclusion(self)

if __name__ == "__main__":
    # 运行此文件即可生成完整视频
    os.system("manim -pqh show/presentation.py Table2SchPresentation")