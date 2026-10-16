# УЧЕБНЫЙ реестр ресурсов

- Внешних изображений, видео и аудио нет. Все надписи созданы Manim CE 0.22.0
  через Pango (`Text` / `MarkupText`) в `src/manim/leap_year.py`.
- Тексты, размеры, координаты и цвета взяты из текущего `script.md`.
- Используется установленный **Noto Sans Regular**; `fc-match 'Noto Sans'`
  возвращает `NotoSans-Regular.ttf`, Pango подтверждает семейство `Noto Sans`.
  Шрифт не копируется в проект; Noto распространяется по SIL Open Font License 1.1,
  сведения о семействе: <https://fonts.google.com/noto/specimen/Noto+Sans>.
  Страница при производстве не открывалась, внешние файлы не скачивались.
- Звук по сценарию отсутствует.
- Воспроизведение из папки `demo`:

```bash
manim --renderer cairo --media_dir renders/manim --resolution 640,360 --fps 30 --disable_caching src/manim/leap_year.py LeapYearComparison
ffmpeg -y -i renders/manim/videos/leap_year/360p30/LeapYearComparison.mp4 -map 0:v:0 -c:v copy -an -movflags +faststart out/video.mp4
```
