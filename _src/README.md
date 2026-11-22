# Pawradise 網站（2026 重建）

## 改內容
1. 改 `_src/pages/` 入面嘅檔案（每頁第一行 `<!--meta {...} -->` 係標題、描述等設定）
2. 喺 repo 根目錄行：`python3 _tools/build.py`
3. 檢查全部通過先 commit（會自動擋：失效連結、禁用字眼、價錢）

**唔好直接改根目錄嘅 HTML**：每次 build 都會被覆蓋。

## meta 設定
- `title`／`description`：Google 搜尋同分享預覽用
- `draft: true`：草稿，唔入 sitemap、唔畀搜尋器收錄
- `noindex: true`：永遠唔畀搜尋器收錄（例如 City Dog Challenge 公布前）
- `localbusiness: true`：加入尖沙咀校區地址、營業時間標記
- `lang: "en"`＋`alt`：英文頁同對應中文頁
- `nav`：導航列標示邊個選項；`"none"`＝唔標示

## 共用部分
- 頁頭頁尾：`_src/layout.html`
- 樣式：`assets/css/site.css`（顏色字體跟品牌手冊 2026-10-03）
- 舊 `.dc.html` 轉址：`_tools/build.py` 入面 `REDIRECTS`

## City Dog Challenge 三個狀態
1. 隱藏（而家）：`noindex: true`，唔放導航列
2. 即將公布（12 月公布日）：拎走 `noindex`、拎走頂部紅色預覽條、`NAV_ZH` 加返連結
3. 計分榜：接 grading-backend 公開計分榜（未做）

## 上線前（第 7 步）要做
- 所有頁拎走 `draft`
- 刪舊檔：`support.js`、`images/`
- 開 Google Search Console＋Google Analytics，加代碼

## 家長指南（/guide/）
- 每篇＝`_src/pages/guide/<英文網址>/index.html`，參考範例 `dog-not-playing-with-other-dogs/`
- meta 要有 `h1`（大標題）同 `article`：`category`（behaviour／social／boarding／care）、`date`（2026-12-01）、`cover`、`cover_alt`、`excerpt`
- 正文只寫 `<p class="hc-lead">` 導言＋`<h2>`／`<p>`／`<ul>`；頁頭、封面、文尾邀請、延伸閱讀、Article 標記全部自動
- 列表頁自動排（新到舊）；`draft: true` 唔入列表。本機睇草稿：`GUIDE_PREVIEW=1 python3 _tools/build.py`（push 前要行返普通 build）
- 第一篇正式文章上線時，`guide/index.html` 拎走 draft，並喺 build.py `NAV_ZH`／頁尾加家長指南連結
- 同事寫稿範本：`~/Desktop/內部文件/網站重建/家長指南寫稿範本.docx`
