# 上班摸魚（moyu）

偽裝成 Excel 報表的手機網頁小遊戲。給在這個 repo 工作的 Claude 看的規則與說明。

## 專案
- 整個遊戲是單一檔案 `index.html`，純 HTML/CSS/JS，沒有建置步驟、沒有套件。
- 主要玩家用手機（觸控）玩，也支援電腦鍵盤。修改時兩者都要顧到。
- 偽裝要像真的：遊戲元素都要看起來像 Excel 的東西（條件式格式、選取框、公式列、狀態列）。

## 存檔（commit）規則
- 存檔說明一律用繁體中文，N 接續上一版（看 `git tag` 的最新 vN）。
- 存檔命名（commit 第一行）格式為「存檔N版-主要修改」，主要修改用 2～8 個字。
- 次要改動寫在 commit 內文（第一行之後空一行，用條列寫）。
- 每次存檔要打 tag `vN`，並 push commit 與 tag。
- 修改要先實際測試、確認可以玩，再存檔。
- 若在雲端（手機）對話中工作，且使用者沒有指定，先推到分支並開 PR，讓使用者檢查後再合併到 `main`。

## 安全
- 不要把任何金鑰、密碼、token 或憑證存進 repo。

## 程式結構（index.html）
- `CFG`：所有手感與難度參數集中在這裡（移動速度、等魚時間、搏鬥張力等）。
- 地形 `T`／`TILES`（顏色、能不能走、水域種類）；`genMap()` 產生地圖。
- 魚種 `FISH`（水域、稀有度 `rar`、尺寸、`price`、像素圖參數）；稀有度 `RAR`。
- 背景格子只放文字與數字（`cellText()` 產生假報表資料），不畫插圖，要像手機看 Excel。
- 右上角小地圖 `#miniBox`（偽裝成圖表），點擊 `openMap()` 放大。
- 魚的像素圖由 `makeFish()` 依參數產生；人物像素圖 `SPR`／`PAL`。
- 特殊物品 `SPECIALS`（奇物，手繪像素圖 `rows`／`pal`）；餌料偏好 `LIKES`、`ONLY_BAIT`；裝備 `RODS`、`BAITS`。
- 魚的力量等級 `fishLv()` 對上釣竿等級：差 1 級很吃力，差 2 級直接斷線。
- 水裡的魚影 `shadows`：大小代表魚的大小，下竿後最近的魚影會游過來（`SZ_MULT` 決定稀有度）。
- 商店：店面格 `T.SHOP_T`／`T.SHOP_M`，走進去 `openShop()`，店員台詞在 `NPC`；今日行情 `hotList()` 每 30 分鐘換；售價 `priceOf()`。
- 拋竿：按住蓄力（state `charge`，`castPower()` 0→1→0 擺盪），放開 `doCast()`；落點 `aimSpot()`，距離 `CFG.castMin`～`castMax`。
- 誘餌 `LURES`（永久，只有 `pred` 掠食魚會咬，線斷 30% 弄丟）；船 `BOATS`（走進水裡自動上船，`canEnter()` 決定能去的水域，一開始送舢舨）。
- 遠洋 `T.FAR`（地圖最東邊，要漁船）。
- 天氣 `WEATHERS`／`weatherAt()`，每 3 分鐘依時間換；暴風雨（`severe`）出現變種怪影（魚影 sz 3），釣到 `MUTANTS` 變種怪魚。
- 搏鬥掙扎頻率有上限 `CFG.surgeCap`，確保最強的魚用好竿子拉得上來。
- 料理 `METHODS`（烤、炸、煮湯、生魚片）：餐廳 `restBody()` 代客料理，背包的 `b.dish` 是料理；吃 `eatDish()` 得到加成 `S.buffs`（`hasBuff()`）；料理只能賣給餐廳。
- 客人委託 `S.quests`：`questFishList()` 只挑目前釣竿、船釣得到的魚（不含變種、奇物）。
- 拉霸 `slotBody()`／`spinSlot()`／`slotPrize()`，大獎金條（`gold`，`noDex` 不進圖鑑、不會釣到）。
- 回城 `goHome()`：回到四間店中間（`SPAWN`）。畫面永遠以人物為中心，地圖外畫成樹林。
- 狀態 `state`：walk → charge → cast → wait → bite → fight → land（魚飛起來的動畫）→ caught；搏鬥資料在 `F`、動畫資料在 `L`。
- 背包 `bag`（`moyu.bag`）與金錢、裝備、圖鑑 `S`（`moyu.save`）存在 localStorage。
- `setBoss()`：隱藏功能（左上角 X 圖示），畫面變成普通報表並暫停。
- 程式註解使用繁體中文。
