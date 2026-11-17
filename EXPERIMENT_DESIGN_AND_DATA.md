# 實驗設計與資料欄位

## 實驗設計

### `Phase1`: Comprehension

參與者閱讀兩個針對相同決策寫下的決策理由並根據 AI prompt 判斷具體程度

### `Phase2`: Basic 11–20

- 共 15 回合。第一回合開始前將受試者兩兩隨機配對，固定小組進行此部分
- 組別隨機分成兩種額外說明回合配置，且兩種配置各佔一半：
  - A：`(1, 3, 8, 13)`
  - B：`(1, 4, 9, 14)`
- DEBUG 測試模式為 5 回合，使用專屬 schedule：A `(1, 3)`、B `(1, 4)`。正式模式為 15 回合，使用正式 schedule：A `(1, 3, 8, 13)`、B `(1, 4, 9, 14)`。
- A、B 必須各含相同數量、按時間先後排列且不重複的回合，才能和第四部分預測次數對齊。
- 為維持兩種 schedule 組數各半，且第三部分可在各 schedule 內兩兩配對，每場參與人數需為至少 4 的 4 倍數。
- 每回合受試者先選擇一個介於 11–20 的整數；額外說明回合可選擇是否更改數字並寫下理由。
- 回合基礎報酬為最終數字選擇。如果最終數字比對手一開始選的數字少 1，額外獲得 20 法幣。

#### 頁面顯示順序與時機

1. 第一回合顯示實驗說明及開始等待頁；所有受試者完成準備後開始此階段。
2. 每回合先顯示數字選擇頁。額外說明回合的受試者提交初始數字後，才會進入 reasoning wait page；非額外說明回合會略過等待頁及理由頁。
3. reasoning wait page 只等待同一固定配對的另一位受試者完成初始數字選擇。A、B schedule 配對各自進行；不需要理由的配對略過此頁。
4. 等待結束後，額外說明回合顯示理由頁，受試者可維持或更改數字並提交理由。
5. 每一固定配對完成當回合決策後，系統即計算該配對報酬並顯示結果；兩位都完成結果頁後，該配對即可進入下一回合，不等待另一 schedule 的配對。最後一回合後另有全體等待頁，所有受試者完成本部分後才進入第三部分。

### `Phase3`: No-cycle 11–20

- 共 10 回合。第一回合開始前將受試者兩兩隨機配對，固定小組進行此部分。
- 依第二部分額外說明回合配置對應安排 reasoning schedule: Basic A 對應 `(1, 4, 7, 10)`；Basic B 對應 `(1, 3, 6, 9)`。
- DEBUG 測試模式為 5 回合，使用專屬 schedule：A `(1, 4)`、B `(1, 3)`。正式模式為 10 回合，使用正式 schedule：A `(1, 4, 7, 10)`、B `(1, 3, 6, 9)`。
- A、B schedule 必須各含相同數量且按時間先後排列的回合。
- 每回合先選擇一個介於 11–20 的整數；額外說明回合可選擇是否更改數字並填寫理由。
- 回合基礎報酬為最終數字選擇；如果最終數字比對手一開始選擇數字少 1，額外獲得 20 法幣；如果最終數字和對手一開始選擇數字相同，可額外 10 法幣。

#### 頁面顯示順序與時機

1. 第一回合顯示實驗說明及開始等待頁；所有受試者完成準備後開始此階段。
2. 每回合先顯示數字選擇頁。額外說明回合的受試者提交初始數字後，才會進入 reasoning wait page；非額外說明回合會略過等待頁及理由頁。
3. reasoning wait page 只等待同一固定配對的另一位受試者完成初始數字選擇。A、B schedule 配對各自進行；不需要理由的配對略過此頁。
4. 等待結束後，額外說明回合顯示理由頁，受試者可維持或更改數字並提交理由。
5. 每一固定配對完成當回合決策後，系統即計算該配對報酬並顯示結果；兩位都完成結果頁後，該配對即可進入下一回合，不等待另一 schedule 的配對。最後一回合後另有全體等待頁，所有受試者完成本部分後才進入第四部分。

### `Phase4`: 實驗後預測

#### 頁面顯示順序與時機

1. 第 1 回合顯示實驗說明；開始後 AI 處理第二、三部分所有額外說明回合的理由，並由全體等待頁確認處理完成。
2. 接著依序進行與 Basic schedule 長度相同的預測回合（正式模式目前 4 回合；DEBUG 目前 2 回合）。A、B 配置同步預測各自對應序號的 Basic reasoning round，並從相同配置的受試者中抽選預測對象；同一預測回合可能對應不同 Basic 原始回合。
3. 每個預測回合依序顯示預測頁、等待該階段小組完成預測、計算正確性與報酬，再顯示預測結果。完成第 1–3 回合結果後進入下一個預測回合。
4. 最後一個預測回合結束後，不再顯示其他預測頁。系統內部回合索引會依第二、三部分實際回合數延伸（目前為 15）；最後索引顯示兩個 11–20 部分的報酬結果、總報酬頁及個人資料表單連結。

原始 Basic 回合編號記錄在 `basic_source_round`。預測對象從第四部分全體受試者中抽選，但限於與預測者相同的 Basic schedule，且該目標回合必須同時有受試者理由與 AI 理由；因此不受 oTree 當前小組範圍限制。若同 schedule 沒有任何其他受試者具備該回合完整理由資料，程式會明確報錯，而不顯示不完整的預測題目。

#### 第四部分資料讀法

- 第四部分 oTree 匯出有與第二、三部分較長回合數相同的 `phase4` 回合索引（正式模式目前為 15；DEBUG 為 5）；**只有前 N 回合是預測回合**，N 為 Basic A、B schedule 的共同長度（正式模式目前 N=4；DEBUG 為 2）。這些列的 `prediction`、`is_correct`、`payoff` 及 `tp_id` 對應受試者依序預測的 Basic reasoning round。
- `basic_source_round` 表示該次預測目標在 Basic 11–20 的原始回合。例如 A schedule 的第 3 次預測對應 Basic 第 8 回合；B schedule 對應 Basic 第 9 回合。因此 A、B 同一個 phase4 預測回合號不一定是相同的 Basic 回合。
- `tp_id` 是被抽中理由提供者的第四部分 `id_in_subsession`。理由內容由該目標的 `phase2_history` 依 `basic_source_round` 讀取；分析預測結果時應以 `phase4.round_number` 識別預測次序，以 `basic_source_round` 識別題目來源回合。
- `prediction` 的值為 `A`、`B` 或 `Tie`，表示選理由 A、理由 B 或判斷平手；`is_flipped` 記錄兩份理由是否交換顯示位置，解讀 A/B 勝負時需一併參照。`is_correct` 和 `payoff` 是此預測回合的正確性與報酬。
- 超過 N 的回合不會顯示預測題目，`prediction` 等預測欄位不代表額外題目；這些索引是為了保存兩個 11–20 階段 AI 處理資料，並在最後索引顯示 AI 結果與報酬頁。AI 欄位 `gpt_reason` / `winner_type` 對應 Basic 原始回合索引；`gpt_reason_2` / `winner_type_2` 對應 No-cycle 原始回合索引，應依各自階段的 `phase2_reasoning_rounds` / `phase3_reasoning_rounds` 判斷哪些列為 reasoning rounds。

此階段目前的 AI 實驗規則文字尚未依新的 Basic/No-cycle 設計更新，請在後續修改 `phase4/ai_processing.py` 中的 `experimental_rules` 與 `experimental_rules_2`。

### P-beauty & Spatial 11-20

p-beauty 和 Spatial 11-20 app 保留在 `p_beauty` 和 `spatial_11_20`。

## 重要資料欄位

oTree 匯出中的欄位通常會以 app 名稱和欄位名稱辨識
- 以下欄位名稱即為 `Player` 欄位
- `participant.vars` 是 app 間跨階段的暫存資料

### `phase1`

| 欄位 | 說明 |
| --- | --- |
| `prediction` | 對判斷結果的預測 |
| `is_correct` | 該回合預測是否正確 |
| `payoff` | 該回合報酬 |

### `phase2`: Basic 11–20

| 欄位 | 說明 |
| --- | --- |
| `initial_num` | 回合一開始選的數字 |
| `revised_num` | 額外說明回合重新選擇的數字；未更改時為空 |
| `final_num` | 最終選擇的數字 |
| `opponent_initial_num` | 對手一開始選的數字 |
| `opponent_revised_num` | 對手重新選擇的數字；未更改時為空 |
| `reason` | 額外說明回合的受試者理由 |
| `reasoning_schedule_id` | 額外說明回合類別: `A` 或 `B` |
| `is_reasoning_round` | 該回合是否為額外說明回合 |
| `is_number_winner` | 最終數字是否比對手一開始的數字少 1 |
| `is_same` | 最終數字是否等於對手一開始的數字 (Basic 11-20 不因此獲得額外報酬) |
| `payoff` | 本回合報酬 (一般回合) |

### `phase3`: No-cycle 11–20

欄位名稱與 `phase2` 對齊。`is_same` 記錄數字相同情況，並可額外獲得 10 法幣。

### `phase4`

| 欄位 | 說明 |
| --- | --- |
| `tp_id` | 該回合預測理由的受試者 id |
| `basic_source_round` | 目標理由所屬受試者在 Basic 11–20 的原始回合編號 |
| `prediction` | 對 AI / 受試者 (human) 理由判斷結果的預測 |
| `is_flipped` | 顯示 AI / 受試者 (human) 理由的顯示順序是否翻轉；預設受試者為理由A，AI為理由B |
| `is_correct` | 預測是否正確 |
| `gpt_reason` / `gpt_analysis` | Basic 11-20 生成的理由與 AI 判斷說明 |
| `winner_type` | Basic 11-20 理由判斷結果 |
| `payoff_by_reasoning` | Basic 11-20 該額外說明回合是否以理由判斷結果決定報酬 |
| `gpt_reason_2` / `gpt_analysis_2` | No-cycle 11-20 生成的理由與 AI 判斷說明 |
| `winner_type_2` | No-cycle 11-20 理由判斷結果 |
| `payoff_by_reasoning_2` | No-cycle 11-20 該額外說明回合是否以理由判斷結果決定報酬 |

### 主要 `participant.vars` key

| key | 說明 |
| --- | --- |
| `phase2_reasoning_rounds` / `phase3_reasoning_rounds` | 該參與者在兩個 11–20 階段使用的實際 reasoning rounds |
| `phase2_reasoning_schedule_id` / `phase3_reasoning_schedule_id` | 該參與者所屬配置 `A` 或 `B` |
| `phase2_history` / `phase3_history` | 各階段逐回合結果及跨階段 AI 顯示資料 |
| `phase2_round_payoffs` / `phase3_round_payoffs` | 各階段逐回合報酬 |
| `phase2_sum_payoffs` / `phase3_sum_payoffs` | 根據 AI 判斷結果調整前各階段報酬總和 |
| `phase2_same_number_<round>` / `phase3_same_number_<round>` | 是否與對手一開始選擇的數字相同 |

`phase2_history` / `phase3_history` 的逐回合紀錄包含 `round`、`initial_num`、`revised_num`、`reason`、`is_reasoning_round`、`bonus`、`is_same` 及報酬等資訊。為了相容目前 phase4 的 AI 處理，歷史紀錄仍保留 `num`（最終數字）與 `other_num`（對手一開始的數字）等舊 key；分析時應優先使用 `phase2` / `phase3` 匯出表中名稱明確的 Player 欄位。
