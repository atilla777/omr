"""Four-second silent addition example; render from the project directory."""

from manim import Dot, FadeIn, Scene, Text, WHITE, config


config.frame_width = 14.2222
config.frame_height = 8
config.background_color = "#101820"


class Addition(Scene):
    def construct(self):
        first = Dot(point=(-1, 0, 0), radius=0.25, color="#66ddaa")
        second = Dot(point=(1, 0, 0), radius=0.25, color="#66ddaa")
        formula = Text("1 + 1 = 2", font="Noto Sans", font_size=40, color=WHITE)
        formula.move_to((0, -1.5, 0))

        self.play(FadeIn(first), run_time=0.5)
        self.wait(0.5)
        self.play(FadeIn(second), run_time=0.5)
        self.wait(0.5)
        self.play(FadeIn(formula), run_time=0.5)
        self.wait(0.5)
        self.wait(1)
