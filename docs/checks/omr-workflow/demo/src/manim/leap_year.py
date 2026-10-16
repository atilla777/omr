"""УЧЕБНЫЙ ролик: два статичных экрана по текущему script.md."""

from manim import BLACK, WHITE, MarkupText, Scene, Text, config


class LeapYearComparison(Scene):
    def construct(self):
        self.camera.background_color = BLACK
        units_per_pixel = config.frame_height / config.pixel_height

        def place(text, height_px, x_px, y_px):
            text.height = height_px * units_per_pixel
            if text.width > 560 * units_per_pixel:
                text.scale_to_fit_width(560 * units_per_pixel)
            text.move_to(
                [
                    (x_px - config.pixel_width / 2) * units_per_pixel,
                    (config.pixel_height / 2 - y_px) * units_per_pixel,
                    0,
                ]
            )
            return text

        style = dict(font="Noto Sans", color=WHITE, font_size=48)
        ordinary = place(Text("Обычный год: 365 дней", **style), 28, 320, 180)
        leap = place(
            MarkupText(
                'Високосный год: <span foreground="#FFFF00">366</span> дней',
                **style,
            ),
            28,
            320,
            150,
        )
        date = place(Text("+ 29 февраля", **style), 24, 320, 210)

        self.add(ordinary)
        self.wait(2, frozen_frame=True)
        self.remove(ordinary)
        self.add(leap, date)
        self.wait(2, frozen_frame=True)
