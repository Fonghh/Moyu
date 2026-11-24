# 上班摸魚（moyu）

3D 第一人稱釣魚的手機網頁小遊戲，左上角 X 一按就變成 Excel 報表。給在這個 repo 工作的 Claude 看的規則與說明。

## 專案
- 整個遊戲是單一檔案 `index.html`，使用 three.js r128（從 cdnjs 載入），沒有建置步驟。
- 主要玩家用手機（觸控）玩，也支援電腦鍵盤。修改時兩者都要顧到。
- 平常是全螢幕 3D；隱藏模式（`#bossView`）要像真的 Excel 報表。

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
- 真實地圖（試作，預設開啟）：桃園竹圍漁港 1 公里見方（以漁港為原點：西 400～東 600、南 500～北 650 公尺），資料 `REAL_DATA`（© OpenStreetMap 貢獻者，ODbL，畫面上要標示）。網址加 `?map=old` 回到原本編出來的小島（`REAL` 是 null）。
  - 產生資料：`tools/fetch_osm.py`（OSM 官方 API 分 16 塊抓，Overpass 常連不上）→ `tools/realmap.py`（海岸線左邊陸地、右邊海；港池、防波堤、河、道路、房子外框；地圖沒畫的透天厝沿村子的路補上；樓高 `FL`；堤防平滑外框；出生點在港邊）。輸出的 JSON 直接貼進 `REAL_DATA`。
  - 四間店放在真實建築：漁產品直銷中心＝魚市場、避風港海鮮館＝海港餐廳、漁會大樓＝釣具行、遊藝場是補上的房子。
  - 格子一樣 5m×2m（200×575 格），多了 `T.QUAY` 堤防、`T.BLDG` 建築；房子碰撞、進店看外框 `BLD`／`bldAt()`（不是看格子）。
  - 比例：眼睛高度 `REAL_EYE`（1.75 公尺，跟真人一樣）；一樓 3.8、樓上每層 3.4 公尺。
  - 3D：`buildRealTown()` 把房子合成一個網格（一樓鐵捲門／店面、樓上窗戶鐵窗冷氣的貼圖 `facadeTex()`／`groundTex()`，晚上窗戶亮）、屋頂水塔和鐵皮加蓋、招牌 `boardTex()`、馬路和標線、堤防（`REAL.quays` 每個是外圈＋洞，直立水泥塊）、外側消波塊、港內直立堤岸、漁船 `boatGeos()`（V 型船身、駕駛艙、桅杆，四成是有集魚燈的魷魚船，`realBoats`／`updateRealBoats()` 跟著浪）。
  - 標誌性建築 `buildLandmarks()`：港口大眾爺廟 `buildTemple()`、漁產品直銷中心 `buildMarket()`、漁業綜合大樓頂樓旋轉餐廳 `buildTower()`（`spinners`）、防波堤尖端紅綠燈塔 `buildHarbourLights()`（晚上閃 `blinkers`）。外框方向用 `obbOf()`。
  - 夜景：路燈 `buildStreetLamps()`（地上光暈 `poolMat`，店門口也有）、跟著玩家的暖色點光源 `nightLamp`；`nightK`（0 白天～1 深夜）在 `updateEnv()` 算、`updateLandmarks()` 每幀用。
  - 地圖很大：地形網格放粗（`GSX`/`GSZ`）、`chunked()` 分塊 96 公尺、樹有距離 LOD；魚生在玩家 110 公尺內，150 公尺外的會換到身邊（`spawnShadow()`／`churnFish()`）；大地圖點一下可以直接走過去。真實地圖的水泥地靠水也不畫成沙灘色。
- 地形 `T`／`TILES`（顏色、能不能走、水域種類）；`genMap()` 產生地圖。
- 魚種 `FISH`（水域、稀有度 `rar`、尺寸、`price`、畫圖參數）；稀有度 `RAR`。
- 地圖仍是格子（`genMap()`），一格 = 東西 `TX`（5m）× 南北 `TZ`（2m）；邏輯座標用格子（`P.x`、`P.y`、魚影、`spot.x/y`），畫面換算成公尺。
- 3D：`buildTerrain()` 地形與水面、`buildTrees()` 樹林、`buildShops()` 店面房子；`render3D()` 每幀更新相機、手上的釣竿（`rodRig`／`rodSegs`）、浮標、釣線、魚影 mesh、天氣、船。
- 寫實畫面：材質 `toon()` 現在回傳 PBR 的 MeshStandardMaterial（名字沿用），`addOutline()` 不再畫描邊；水面下的東西用 `underwater(mat)`（越深越偏水色、海底焦散 `UW`）。
- 一天的時間：`gameHour()`（現實 1 分鐘＝遊戲 1 小時，5 點日出、19 點日落），`updateEnv()` 每幀算太陽 `SUN_DIR`、月亮 `MOON_DIR`、天空 `skyMat`（含黃昏、星星 `starMat`）、光線、雲 `clouds`（貼圖雲）、遠方的島、晚上亮的窗戶 `nightGlow`。
- 水面：以鏡頭為中心的同心圓網格 `waterMesh`，四道浪 `WAVES` 疊加（大小 `waveAmp` 看天氣、`CALM` 看水域），JS 的 `waterH(x, z)` 跟 shader 同一組浪（浮標、船跟著浪）；鏡面倒影 `renderReflection()`（低解析度、第 1 層的小花灌木不畫進倒影）；漣漪 `addRipple(x, z, amp)`；陰影每幀只更新一次（`shadowMap.autoUpdate = false`）。
- 地形：每格高度 `tileH`，`hField()` 平滑內插（海岸線落在格子邊上），`groundH()` 是腳下高度（相機跟著走）；水面是 shader `waterMat`（水深 `depthTex` 上色、`tintTex` 的 A 是浪的大小、岸邊浪花）。
- 樹、灌木、花、石頭用 `chunked()` 分塊的 InstancedMesh，遠的區塊用 `updateLod()` 關掉描邊和小花。
- 順暢度：`QUALITY` 畫質等級，`watchFps()` 依實際幀率自動調整解析度、陰影、描邊。
- 特效：`splashRing()` 水花波紋、`biteGlow` 上鉤閃光、`catchRays`／`stars` 釣到時的放射光和星星。
- 操作：觸控左半邊搖桿 `joy`、右半邊轉頭 `look`（`yaw`／`pitch`）；電腦 WASD、方向鍵、滑鼠拖曳。拋竿方向就是視線方向。
- 店面是房子（不能走進去），撞到門 `shopTouch` 就打開商店。
- 隱藏模式的報表 `drawSheet()`（`cellText()` 產生假資料）；右上角小地圖 `#miniBox`（卡通配色 `MAP_COL`），點擊 `openMap()` 放大。
- 介面統一風格（跟釣具箱一樣）：所有視窗都是半透明深藍面板＋金色重點（`#dlg.clear`、樣式表最後的「遊戲介面統一風格」）；共用元件 `gridCell()`／`tbGrid()` 格子、`fishCard()` 魚的說明卡（出沒、愛吃、力量、小故事 `FISH_STORY`）、`fishSil()` 剪影。背包（漁獲／料理／圖鑑）、釣具行（分類 `shopItems()`）、魚市場、餐廳（委託卡片、料理預覽 `DISH_STORY`）、拉霸、地圖、提示都用這套。新畫面也要照這個風格做。
- 全部是卡通圖：魚的圖 `makeFish()`（向量畫，版面 56×28、放大 `FK` 倍；花紋 `paintFishBody()`、臉 `paintFishFace()`，3D 貼圖 `fishToonTex()` 共用同一套）；奇物、雜物、章魚、鱷魚用 `emoji` 欄位（3D 裡用平面 `fishSprite`，判斷用 `flatItem()`）；店員 `drawNpc()`；料理 `dishImg()`；回城、背包按鈕用 emoji。
- 特殊物品 `SPECIALS`（奇物，`emoji` 當圖）；餌料偏好 `LIKES`、`ONLY_BAIT`；裝備 `RODS`、`LINES`（釣線耐久 `hp`）、`REELS`（收線倍率 `sp`、磨損倍率 `wear`）、`BAITS`；存檔 `S.rod`／`S.line`／`S.reel` 是等級。
- 魚的力量等級 `fishLv()` 對上釣竿等級：差 1 級吃力、差 2 級很難拉，差 3 級直接斷線。
- 水裡的魚 `shadows`（名字沿用）：每條魚出生時就有魚種 `f`、大小 `size`（`rollFish()`，`SZ_MULT`／`SIZE_FIT`），在水裡自己游（`updateShadows()`）：小魚 `SCHOOLERS` 成群跟著帶頭魚（`leader`）、大魚到礁石和碼頭柱子 `STRUCT` 旁休息（`rest`）、到水底覓食（`feed`）。近的畫成會擺動的立體魚（`syncShadows()`／`getSwimmer()`，身體在 shader 裡擺），遠的畫影子。
- 咬餌：`findBiter()` 挑附近的魚 → `hookFish()` → `biteMove()` 依序 approach（游過來）→ circle（繞圈）→ nibble（輕啄，浮標往下點 `nibbleK`）→ decide → take（吞餌，`state = 'bite'`，浮標被拖著走）或 leave。咬法看魚種 `biteStyle()`；吃不吃看餌 `baitAccept()`（喜歡的餌、誘餌只有掠食魚、`ONLY_BAIT`）。釣上來的就是游過來的那條魚。試探中太早拉只會提示、不會收竿。
- 商店：店面格 `T.SHOP_T`／`T.SHOP_M`，走進去 `openShop()`，店員台詞在 `NPC`；今日行情 `hotList()` 每 30 分鐘換；售價 `priceOf()`。
- 拋竿 `castNow(力道, 偏角)`：甩竿 `swipe`（按住下竿鍵往下拉、往上甩，`releaseCharge()` 用最後 160ms 的速度算力道、左右偏一點）；按住不動就用舊的蓄力（`castPower()` 0→1→0 擺盪，鍵盤也是這個）；體感拋竿 `S.opt.motion`（`devicemotion` 揮動手機，iPhone 要 `askMotion()` 允許）。落點 `aimSpot()`，距離 `CFG.castMin`～`castMax`。
- 三種釣法 `RIGS`（下竿鍵左邊的 `#rigBtn` 切換浮釣／沉底，鍵盤 R；裝誘餌就是路亞），`rigOf()` 下竿時記在 `spot.rig`：浮釣看浮標；沉底 `sinker` 沉到水底（`spot.sink`）、看竿尖抖動，底棲魚 `BOTTOM_FISH` 多（`rigMult()`）；路亞 `lureMesh` 按住收線（`CFG.lureSp`），節奏 `lureR`，魚 `follow` 跟在後面，「收一收、停一停」最會咬。
- 釣線 `ropeStep()`：一串點的物理（重力、風、水中阻力、只會變鬆不會拉長），等魚時鬆、搏鬥時張力越大越直。
- 聲音 `SND`／`SFX`／`updateSound()`：Web Audio 即時合成（海浪、風、雨、蟲鳴、咻聲、落水、啄、捲線器、洩線、斷線、釣到、賣錢），第一次觸控才開始（`sndInit()`）。
- 設定 `openSettings()`（左上角 ⚙）：`S.opt.sound`、`S.opt.motion`、操作說明。
- 誘餌 `LURES`（永久，只有 `pred` 掠食魚會咬，線斷 30% 弄丟）；船 `BOATS`（走進水裡自動上船，`canEnter()` 決定能去的水域，一開始送舢舨）。
- 遠洋 `T.FAR`（地圖最東邊，要漁船）。
- 釣況：時段 `todAt()`（`TODS` 清晨/白天/黃昏/夜晚）、季節 `seasonAt()`（遊戲 3 天＝現實 72 分鐘換一季）、潮汐 `tide()`（12.4 小時一循環，`flow` 潮水流速）；每種魚的習性 `HABITS` → `fishActivity()`（影響 `rollFish()` 生出的魚、`findBiter()` 誰游過來）；`churnFish()` 讓遠處的魚慢慢換班。點上方時間 `openConditions()` 看釣況、潮位圖、現在好釣的魚。
- 釣魚筆記 `S.log`（`logCatch()` 記時段、季節、潮汐、天氣），圖鑑卡片 `noteFacts()`；同一種魚釣到 `HABIT_N` 次就揭曉習性 `habitText()`。
- 天氣 `WEATHERS`／`weatherAt()`，每 3 分鐘依時間換；暴風雨（`severe`）出現變種怪影（魚影 sz 3），釣到 `MUTANTS` 變種怪魚。
- 搏鬥（擬真手感）：`FIGHT` 參數、`newFight()`、`nextAct()`（魚的動作：run 左右/外衝、charge 游過來、shake 甩頭、jump 跳水、rest 休息）、`stepFight()`（側壓、收線、洩線 drag、鬆線脫鉤、線被拉光；甩頭跳水硬收的瞬間張力 `F.spike` 和超出洩線的張力 `F.over` 會磨損釣線耐久 `F.hp`，歸零才斷，速度 `FIGHT.wearRate`）。魚的位置用玩家為中心的角度 `th`＋距離 `d`（`fishWorld()`）；左右游有慣性 `F.vlat`（慢慢加速、轉向，看線在水面劃過去就知道往哪跑）。甩頭、跳水剛開始 `FIGHT.react` 秒內收線不會有瞬間張力（給反應時間）。數值改動前先用模擬確認（一般玩家：反應慢、常忘了側壓，也要能拉上適合釣竿的魚；一直硬收的偶爾斷線）。
- 料理 `METHODS`（烤、炸、煮湯、生魚片）：餐廳 `restBody()` 代客料理，背包的 `b.dish` 是料理；吃 `eatDish()` 得到加成 `S.buffs`（`hasBuff()`）；料理只能賣給餐廳。
- 客人委託 `S.quests`：`questFishList()` 只挑目前釣竿、船釣得到的魚（不含變種、奇物）。
- 拉霸 `slotBody()`／`spinSlot()`／`slotPrize()`，大獎金條（`gold`，`noDex` 不進圖鑑、不會釣到）。
- 回城 `goHome()`：回到海邊小鎮（`SPAWN`，碼頭入口旁），面向大海。地圖外圍是一片大海。
- 立體魚和水裡的魚都用寫實魚皮 `fishRealTex()`（背深腹銀、細鱗片、側線、鰓蓋、小眼睛、半透明魚鰭）；介面上的魚圖（`makeFish()`）還是卡通。
- 立體魚 `make3DFish()`（`FISH_BODY` 對應魚圖身體範圍的球體＋尾鰭、背鰭、胸鰭）、`animFish(o, 相位, 幅度, 彎度)` 身體擺動甩尾＋整條彎成 C 字、`showFish3D()`／`fishLen()`；搏鬥整場都畫立體魚（14m 外才加影子），跳水有好幾種跳法 `F.jStyle`（arc 弧線、spin 翻滾、headshake 甩頭、tailwalk 尾巴走水、小魚 flop），累了側躺翻白肚；引拔掙扎的快慢方向 `L.f1`／`L.f2`／`L.sd` 每次隨機。
- 釣具箱 `openBox()`（右邊 🧰 按鈕）：上面四格身上的裝備 `BOX_SLOTS`（釣竿、釣線、捲線器、餌），中間是持有的釣具格子（數量、新東西的藍色「!」記在 `S.seen`），下面說明卡（數值條 `gearStats()`、容易釣到的魚 `gearFish()`，沒釣過的只顯示剪影、小故事 `GEAR_STORY`）。點一下看說明、再點一下或按「換上」就裝上。持有的最高等級在 `S.own`，正在用的在 `S.rod`／`S.line`／`S.reel`。釣具的卡通圖 `gearImg()`（商店表格也用）。
- 小鎮：商店街（出生點那條路）三格寬，四間店在兩邊各退一格。
- 搏鬥：魚有體積（`inWater` 檢查身體四周），碰到岸邊、碼頭過不去，累了就直接在岸邊拉上來；被線拉著時頭朝人（`F.hd`）。
- 大魚的誇張特效：`splash(x, y, n, pw)` 依魚的強度放大水花，稀有以上跳水 `slowMo()` 慢動作＋`fxFlash()` 白光，大魚甩頭、爆衝時 `bigCue()` 畫面中間跳出大字。
- 拉上來的掙扎 `L.mode`：`thrash` 在手上亂甩、`flop` 摔在腳前地上彈跳翻面再撿起來、`escape` 差點從手上跳走；`L.dur` 決定多久後跳出結果。
- 搏鬥畫面：上方魚的體力條 `#fHp`（魚的剪影 `#fIcon`）、釣線耐久條 `#fDur`；水面上的方向指示 `guideRing`／`guideArrow`（綠＝收線、橘＝往箭頭方向壓竿、紅＝甩頭跳水別收）。
- 水面倒影：`waterMat` 用反射方向算天空漸層和雲（不是真的鏡面反射，手機跑得動）；外海零星白浪。
- 視角：眼睛高度 `CFG.eye`（3m），搏鬥時鏡頭自動往下看向魚。
- 狀態 `state`：walk → charge → cast → wait → bite → fight → land（引拔：魚頭朝上掛在線上被吊到面前 `CFG.landFly`，再演掙扎 `L.mode`）→ caught；搏鬥資料在 `F`、動畫資料在 `L`。
- 水族箱 `S.tank`（背包「水族箱」分頁，最多 `TANK_N` 條）：`toTank()` 從漁獲放進去（最大那條）、`tankView()` 畫面上的魚在缸裡游（canvas 動畫，顏色跟著時間）、`tankIncome()` 觀賞門票（依魚的價值，`S.tankAt` 記上次結算）。
- 今日挑戰 `S.daily`（`daily()` 依日期 `today()` 產生三個 `newDaily()`：指定魚或尺寸、釣法或時段、幾種不同的魚），`dailyCheck()` 釣到時檢查，完成直接給獎金；顯示在釣況視窗 `dailyBox()`。
- 背包 `bag`（`moyu.bag`）與金錢、裝備、圖鑑 `S`（`moyu.save`）存在 localStorage。
- 雲端存檔：在 claude.ai 測試網頁（artifact）上玩時，`saveAll()` 也把進度寫到每個人私人的 `data/users/<id>/moyu`（`cloudSave()`，需要 artifact 的 `db`、`user` 能力）；開啟時比較 `S.at`，雲端比較新就讀回來。一般網址沒有 `window.claude`，只用 localStorage。
- 新增存檔欄位時要給預設值（`S` 的初始值或讀檔後補上），舊存檔才不會壞掉。
- `setBoss()`：隱藏功能（左上角 X 圖示），畫面變成普通報表並暫停。
- 程式註解使用繁體中文。
