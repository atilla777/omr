from manim import Dot, Scene, config, smooth

config.background_color = "#101820"
config.frame_width = 14.2222
config.frame_height = 8


class PairInsert(Scene):
    def construct(self):
        left = Dot((-2, 0, 0), radius=0.3, color="#66ddaa")
        right = Dot((2, 0, 0), radius=0.3, color="#66ddaa")
        self.add(left, right)
        self.wait(0.5)
        self.play(
            left.animate.move_to((-0.5, 0, 0)),
            right.animate.move_to((0.5, 0, 0)),
            run_time=1,
            rate_func=smooth,
        )
        self.wait(0.5)
