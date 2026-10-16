# Проверка производства Manim

Дата: 2026-10-16. Проект: `docs/checks/omr-render/manim` относительно корня OMR.
Все команды ниже выполнены из выбранного проекта.

## Входы и ограничения

- Использованы `requirements.md`, `content/index.md`, `script.md`; входы не изменены.
- Загружены через `skill`: `omr-render`, `manim`, `manim-local`.
- Чистый Manim CE, одна Scene; внешние ресурсы, голос, музыка, эффекты не нужны.
- Использовано существующее окружение `uv tool`, без установки и изменения зависимостей.
- Делегирования не было. GUI, desktop-приложения и плеер не запускались.
- Проверка изображений выполнена инструментом `read`, открывающим реальные PNG.

## Окружение

- `manim`: `/home/aleksei/.local/bin/manim`, Community v0.22.0.
- Python окружения: `/home/aleksei/.local/share/uv/tools/manim/bin/python`, 3.13.16.
- `uv`: `/home/aleksei/.local/bin/uv`; `uv tool list` подтвердил Manim v0.22.0.
- FFmpeg и FFprobe: `/usr/bin/ffmpeg`, `/usr/bin/ffprobe`, n9.0.1.
- `fc-match 'Noto Sans'`: NotoSans-Regular.ttf, Noto Sans Regular.
- `latex` и `dvisvgm` доступны в `/usr/bin/`; отдельный CLI `typst` в PATH
  не найден, Python-модуль `typst` доступен в окружении Manim. Для этой сцены
  используются только `Text`/Pango: TeX и Typst не требовались и не компилировались.
- Импорт и исполнение сцены подтверждены успешными рендерами в указанном окружении.

Команды проверки окружения:

```bash
pwd
command -v manim uv ffmpeg ffprobe
manim --version
uv tool list
fc-match 'Noto Sans'
command -v typst
command -v latex
command -v dvisvgm
/home/aleksei/.local/share/uv/tools/manim/bin/python -c "import sys, manim, importlib.util; print(sys.version); print('manim', manim.__version__); print('typst Python binding:', importlib.util.find_spec('typst') is not None)"
ffmpeg -version
ffprobe -version
```

## Реализация и воспроизведение

Исходник: `src/manim/scene.py`, класс `Addition`.
Камера 14.2222 × 8, фон `#101820`, точки радиуса 0.25 цвета `#66ddaa`
в (-1, 0) и (1, 0). Белый Text `1 + 1 = 2`, Noto Sans, font_size 40,
центр (0, -1.5). Три FadeIn по 0.5 с и ожидания 0.5 + 0.5 + 0.5 + 1 с:
всего 4 с / 120 кадров. Звук в сцену не добавляется.

Сначала выполнен still-рендер в целевом размере:

```bash
manim -s --renderer cairo --resolution 640,360 --fps 30 --media_dir renders/still --disable_caching src/manim/scene.py Addition
```

Просмотрен `renders/still/images/scene/Addition_ManimCE_v0.22.0.png`:
две точки и читаемая формула, достаточные поля, без обрезаний и наложений.
С учётом малого целевого размера полный ролик сразу рендерился в заданных параметрах.

Команда повторного рендера и доставки результата:

```bash
manim --renderer cairo --resolution 640,360 --fps 30 --media_dir renders --disable_caching --format mp4 -o video src/manim/scene.py Addition
mkdir -p out
cp renders/videos/scene/360p30/video.mp4 out/video.mp4
```

## Проверка итогового MP4

Первичная проверка:

```bash
ffprobe -v error -count_frames -show_streams -show_format -of json out/video.mp4
ffmpeg -v error -i out/video.mp4 -f null -
```

Повторяемая проверка, сохранение параметров, извлечение кадров и контактный лист:

```bash
/home/aleksei/.local/share/uv/tools/manim/bin/python renders/check_video.py
```

Скрипт выполняет FFprobe, утверждения по параметрам и числу потоков, полное
декодирование `ffmpeg -v error -xerror -i out/video.mp4 -f null -`, затем:

```bash
ffmpeg -v error -y -i out/video.mp4 -map 0:v:0 -fps_mode passthrough -start_number 0 renders/frames/frame-%03d.png
```

Результаты сохранены в `renders/ffprobe.json`:

| Параметр | Факт |
| --- | --- |
| Итог | `out/video.mp4`, новый рендер этой сессии |
| Размер файла | 23974 байта |
| Видео | H.264 High, yuv420p, progressive |
| Разрешение | 640 × 360 |
| FPS (r/avg) | 30/1 и 30/1 |
| Кадры (заявлено / декодировано) | 120 / 120 |
| Начало | 0.000000 с |
| Длительность видео / контейнера | 4.000000 / 4.000000 с |
| Потоки | Один видеопоток, **аудиопотоков нет** |
| Полное декодирование | Успех, код 0, без ошибок |

## Фактический визуальный просмотр

Из итогового MP4 извлечены все 120 PNG в `renders/frames/` (нумерация с нуля).
Открыт через `read` контактный лист `renders/contact-sheet.png` с кадрами:

`0, 7, 14, 15, 29, 30, 37, 44, 45, 59, 60, 67, 74, 75, 89, 90, 119`.

Покрыты начало, середины трёх FadeIn, конец каждого появления, границы
0.5/1/1.5/2/2.5/3 с до и после смены действия и последний кадр 3.9667 с.
Отдельно открыты полноразмерные `frame-067.png` и `frame-119.png`.

- Кадр 0 — заданный пустой фон, начало FadeIn с нулевой непрозрачностью.
- Кадры 7, 14, 15 — первая точка плавно появляется и сохраняется.
- Кадры 29/30 — первая точка остаётся, вторая начинает появление без скачка фона.
- Кадры 37, 44, 45 — вторая точка появляется, обе сохраняются.
- Кадры 59/60 — обе точки; начало появления формулы без скачка.
- Кадр 67 — полупрозрачная формула; 74/75 — читаемая полная формула.
- Кадры 89/90/119 — две точки и `1 + 1 = 2` сохраняются до конца.
- Обрезания, наложения, пропавшие элементы и видимые цветовые скачки не обнаружены.

Дефектов, требующих исправления реализации или изменения сценария, не найдено.

## Границы проверки

Движение оценено по последовательности выбранных реальных кадров, а не по
воспроизведению в реальном времени. Все 120 кадров декодированы и сохранены,
но индивидуально визуально просмотрены только перечисленные точки таймлайна.
GUI/плеер не использовались по условию автоматического CLI-прогона. Прослушивание
не требовалось: отсутствие звука подтверждено отсутствием аудиопотоков.
Блокеров производства и запрошенных автоматических проверок нет.
