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
