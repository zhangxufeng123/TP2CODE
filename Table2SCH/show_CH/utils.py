# filepath: show/utils.py
from manim import *

def create_header(text_str):
    """辅助函数：创建统一风格的标题"""
    header = Text(text_str, color=BLUE_B, font_size=28).to_edge(UP)
    underline = Line(LEFT, RIGHT, color=BLUE_B).scale(6).next_to(header, DOWN, buff=0.1)
    return VGroup(header, underline)