# MarketReader MVP — HTML/CSS 2-page version

AssetPicker용 **쇼츠 전용 Daily Market Board** 생성기입니다.
OpenAI API는 사용하지 않습니다.

## 출력 구조

- 1페이지: Daily Market Board — 11초
- 2페이지: Ending / CTA — 4초
- 총 15초

`config.py`에서 아래 두 숫자만 바꾸면 10초 버전도 바로 됩니다.

```python
PAGE1_SECONDS = 7
PAGE2_SECONDS = 3
```

## 가장 먼저 넣을 이미지

직접 만든 이미지는 아래 파일명으로 넣어주세요.

```text
assets/page1_bg.png        # 1페이지 도시 야경 배경 (jpg/jpeg/webp도 가능)
assets/page2_bg.png        # 2페이지 확대경/도시 배경 (jpg/jpeg/webp도 가능)
assets/page2_cta_bg.png    # 선택: CTA 버튼 뒤 띠 배경
```

이미지가 없어도 CSS fallback 배경으로 렌더됩니다.

## 핵심 파일

```text
templates/page_1.html   # 1페이지 디자인 + CSS + 데이터 자리
templates/page_2.html   # 마지막 페이지 디자인 + CSS
render.py               # JSON → HTML 값 주입 → PNG 스크린샷
build_video.py          # page_1 + page_2 → 15초 MP4
main.py                 # 전체 실행
config.py               # 해상도/페이지 시간
```

## 설치

```powershell
cd market_reader_mvp_html
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
Copy-Item .env.example .env
```

이미 PC에 Chrome이 있고 Playwright 브라우저를 따로 설치하기 싫다면 `.env`에 `CHROME_PATH`를 넣어도 됩니다.

## 샘플 실행

```powershell
python main.py --sample
```

PNG만 먼저 확인:

```powershell
python main.py --sample --frames-only
```

결과:

```text
output/YYYY-MM-DD/
  market.json
  page_1.html
  page_1.png
  page_2.html
  page_2.png
  market_reader.mp4
```

## 실제 데이터

`.env`에 API 키를 넣고:

```powershell
python main.py
```

1페이지의 `출처` 줄은 `market.json`의 `sources` 값을 자동으로 조합합니다.
