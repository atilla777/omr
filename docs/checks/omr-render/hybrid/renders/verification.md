# Проверка производства: гибрид

Дата: 2026-10-16. Проект: `docs/checks/omr-render/hybrid`.
Получен новый `out/video.mp4`; финальная сборка выполнена **Remotion**.

## Входы и ограничения

Использованы `requirements.md`, `content/index.md`, `script.md` без изменений.
Полные SHA-256 входов и MP4 сохранены в `renders/measurements.json`.
Скиллы загружены через инструмент `skill`: `omr-render`,
`remotion-best-practices`, `manim`, `manim-local`; прочитаны профильные
руководства по созданию, разметке, композициям, видео, звуку и рендеру.

- Работа только в выбранном тестовом проекте, без делегирования.
- Node-зависимости установлены локально, версии закреплены в `package.json`
  и `package-lock.json`; зависимости соседних проектов не использовались.
- Общее Manim uv tool окружение не изменялось, установки Python не выполнялись.
- Не запускались Studio, GUI, desktop-браузер, видеоплеер или аудиоплеер.
  Chromium использован только headless-процессом рендера.
- Нет речи, музыки и внешних медиа; ресурсы описаны в `public/assets.md`.
- Предыдущие этапы не запускались. Публикация, commit и push не выполнялись.

## Окружение

- Node v26.8.1, npm 11.19.0.
- Remotion, `@remotion/cli`, `@remotion/media`: 4.0.536.
- React / React DOM 19.2.0.
- Manim CE 0.22.0, существующий CLI `manim` из uv tool.
- FFmpeg / ffprobe n9.0.1; Chromium 152.0.7977.82.
- Noto Sans Regular: `fc-match 'Noto Sans'` → NotoSans-Regular.ttf.
- `latex` и `dvisvgm` доступны; отдельный CLI `typst` отсутствует.
  Сцена использует только Dot, математический текстовый движок не нужен.
- Проверочный Python: существующий
  `/home/aleksei/.local/share/uv/tools/manim/bin/python` с NumPy и Pillow 12.3.0.
  Этот путь относится к текущей машине, в исходники не зашит.

## Команды

Все команды выполнялись из выбранного проекта. Воспроизведение с чистыми
локальными Node-зависимостями: `npm ci` (при первом запуске использовалось
`npm install --save-exact`; аудит сообщил 0 уязвимостей).

Проверка окружения:

```bash
git status --short
node --version
npm --version
manim --version
ffmpeg -version
ffprobe -version
fc-match 'Noto Sans'
command -v typst latex dvisvgm chromium google-chrome
npm view remotion version
npm ls --depth=0
chromium --version
```

Производство и повторный рендер:

```bash
manim -s --resolution 640,360 --fps 30 --media_dir renders/manim src/manim/insert.py PairInsert
manim --resolution 640,360 --fps 30 --media_dir renders/manim --disable_caching -o insert.mp4 src/manim/insert.py PairInsert
ffmpeg -v error -y -i renders/manim/videos/insert/360p30/insert.mp4 -c copy renders/insert.mp4
ffprobe -v error -count_frames -show_streams -show_format -of json renders/insert.mp4
ffmpeg -v error -y -i renders/insert.mp4 -vf "select='eq(n,0)+eq(n,30)+eq(n,59)',tile=3x1" -frames:v 1 renders/insert-contact.png
python src/prepare.py
npm run build
npm run render
```

`npm run build` разворачивается в:

```bash
remotion bundle src/remotion/index.tsx --out-dir=renders/bundle
```

Первый вызов bundle ошибочно использовал позиционный `renders/bundle` и сохранил
bundle в стандартный `build/`. Команда исправлена на `--out-dir`, сборка повторена
успешно; обе технические папки исключены из Git.

`npm run render` — точная команда финального рендера:

```bash
remotion render src/remotion/index.tsx Hybrid out/video.mp4 --codec=h264 --crf=18 --audio-codec=aac --audio-bitrate=192k --concurrency=2 --browser-executable=/usr/bin/chromium
```

Проверка готового MP4:

```bash
/home/aleksei/.local/share/uv/tools/manim/bin/python src/verify.py
git diff -- requirements.md content/index.md script.md
```

`src/verify.py` сохраняет `renders/measurements.json`, реальные PNG в
`renders/frames/`, `renders/contact-sheet.png`. Он вызывает:

```bash
ffprobe -v error -count_frames -show_streams -show_format -of json out/video.mp4
ffmpeg -v error -xerror -i out/video.mp4 -f null -
ffmpeg -v error -i out/video.mp4 -f rawvideo -pix_fmt rgb24 -
ffmpeg -v error -i out/video.mp4 -vn -ac 2 -ar 48000 -f f32le -
```

Сырые данные забираются через pipe непосредственно в Python, без открытия плеера.

## Видео и стыковка

| Проверка | Результат |
|---|---|
| Manim-вставка | H.264 yuv420p, 640×360, 30/1 FPS, 60 декодированных кадров, 2,000 с |
| Прозрачность/звук вставки | Обычный непрозрачный MP4, только 1 видеопоток, аудио отсутствует |
| Итоговое видео | H.264 yuvj420p, 640×360, 30/1 FPS, 120 декодированных кадров, 4,000 с |
| Итоговое аудио | AAC, stereo 48000 Hz, длительность потока 4,011 с |
| Контейнер | 4,011 с, 117352 bytes; разница с 4 с видео — хвост AAC-пакетов |
| Полное декодирование | FFmpeg `-xerror` завершился без ошибок |
| Таймлайн | Старт [0,30), вставка [30,90), финиш [90,120) |
| Вставка | Локальные [0,60) → глобальные [30,90), playbackRate=1, contain 640×360 |

До полного рендера вставки открыт PNG финального состояния Manim
`renders/manim/images/insert/PairInsert_ManimCE_v0.22.0.png` инструментом `read`.
После рендера открыт `renders/insert-contact.png` с локальными кадрами 0,30,59.
Видны две отдельные точки: сначала разнесены, затем сближены; обрезания нет.

Из **готового итогового MP4** декодированы все кадры; PNG сохранены для
0,29,30,44,45,60,74,75,89,90,119. Открыт и визуально изучен инструментом `read`
контактный лист `renders/contact-sheet.png`, содержащий все эти кадры:

- 0,29: белый «СТАРТ» по центру, читаемый, без пропавших символов.
- 29→30: прямая склейка, титр исчезает, обе точки уже присутствуют.
- 30,44,45: начальный hold, центры около x=229,5 и 409,4 px, y≈179,4 px.
- 60: движение, центры x≈263,3 и 375,7 px.
- 74,75,89: финальная пара, центры около x=296,9 и 342,1 px.
- 89→90: прямая склейка с пары на акцентный «ФИНИШ».
- 90,119: неподвижный читаемый «ФИНИШ», по центру, поля достаточны.

Автоматически проверены обе точки в каждом из 60 кадров итоговой вставки:
обе обнаружены, движение левой монотонно, точки не превращаются в один объект.
Исходная камера frame_width=14,2222, frame_height=8; радиусы 0,3.
Длительности hold/play/hold: 0,5/1/0,5 с, rate_func=smooth.

Фон в исходниках везде #101820. После двух H.264/YUV преобразований контрольный
RGB фона: титры (15,24,31), вставка (14,22,32), то есть на склейке разница
до 2 единиц на канал. На просмотренном листе существенного цветового скачка нет;
побитовая точность RGB в сжатом MP4 не заявляется. Нет рамок, наложений, пропавших
медиа, изменения масштаба или титров поверх вставки.

## Звук: измерено, без прослушивания

- `public/tone.wav`: mono PCM S16, 48000 Hz, 9600 samples = 0,200 с.
  Синус 660 Hz, линейные fade in/out 480 samples = 10 ms.
  Измеренный исходный пик 0,100006 FS (квантование PCM16).
- Звук включён только в финальной Remotion-композиции, `from=3*fps` = кадр 90.
- Анализ декодированного AAC выполнен по отдельному каналу, а не через
  суммирующий stereo→mono downmix. В первом измерении downmix добавлял +3 dB;
  метод проверки исправлен, повторное измерение по L/R приведено ниже.
- Измеренные пики L/R: 0,100780 / 0,100780 FS, около −19,93 dBFS.
  Небольшое превышение исходного 0,1 — результат lossy AAC; клиппинга нет.
- RMS интервала 3–3,2 с: 0,068289 FS; доминирующая частота FFT: 660 Hz.
- Сигнал выше 0,001 FS находится в 3,000167–3,199854 с.
  Это согласуется с началом ровно в 3 с и короткими fade; порог не определяет
  первый ненулевой сэмпл буквально.
- Корреляция с исходной 0,2-секундной волной, поставленной ровно в 3 с:
  0,9999959; коэффициент усиления 0,999732. Таким образом, измеренно подтверждены
  синхронизация и сохранность формы сигнала, включая заданные fade.
- До 2,99 с пик 0; после 3,21 с пик 0,000158 FS (около −76 dBFS,
  остаток сжатия, ниже порога сигнала). Иных событий не обнаружено.
- Декодировано 192512 аудиосэмплов на канал / 4,010667 с; видеоряд не обрезан.

## Ограничения проверки

**Интерактивный просмотр и прослушивание не проводились по условию автоматического
CLI-прогона.** Studio/GUI/desktop-плееры не запускались. PNG просмотрены
изображение-способным инструментом `read`, сигнал проверен численно.
Непрерывное движение не просмотрено в реальном времени; оно проверено набором PNG
и координатами по всей вставке. Субъективное качество тона на слух не проверено.
Полностью интерактивно просмотренным/прослушанным результат не объявляется.

Исходники: `src/manim/insert.py`, `src/remotion/index.tsx`;
подготовка ресурсов: `src/prepare.py`; воспроизводимая проверка: `src/verify.py`.
Производственный результат: `out/video.mp4`.
