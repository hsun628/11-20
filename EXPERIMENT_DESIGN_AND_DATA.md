# 實驗設計與資料欄位

## 實驗設計

### `Phase1`: Comprehension

參與者閱讀兩個針對相同決策寫下的決策理由並根據 AI prompt 判斷具體程度

### `Phase2`: Basic 11–20

- 共 15 回合。第一回合開始前將受試者兩兩隨機配對，固定小組進行此部分
- 組別隨機分成兩種額外說明回合配置；組數為偶數時兩配置各佔一半，組數為奇數時隨機決定哪個配置多一組：
  - A：`(1, 3, 8, 13)`
  - B：`(1, 4, 9, 14)`
- 每回合受試者先選擇一個介於 11–20 的整數；額外說明回合可選擇是否更改數字並寫下理由。
- 回合基礎報酬為最終數字選擇。如果最終數字比對手一開始選的數字少 1，額外獲得 20 法幣。

#### 頁面顯示順序與時機

1. 第一回合顯示實驗說明及開始等待頁；此階段配對完成後進入回合流程。
2. 每回合先顯示數字選擇頁。額外說明回合的受試者提交初始數字後，才會進入 reasoning wait page；非額外說明回合會略過等待頁及理由頁。
3. reasoning wait page 只等待同一固定配對的對手完成初始數字選擇；不同配對（不論 schedule 相同或不同）不會互相等待。不需要理由的回合會略過此頁。
4. 等待結束後，額外說明回合顯示理由頁，受試者可維持或更改數字並提交理由。
5. 每回合由固定配對互相等待完成決策，系統計算該組報酬並顯示結果；兩位都完成結果頁後即可進入下一回合，不等待其他配對。
6. 最後一回合結果後設有階段結束等待頁，所有受試者完成本部分後才進入第三部分。

### `Phase3`: No-cycle 11–20

- 共 10 回合。第一回合開始前將受試者兩兩隨機配對，固定小組進行此部分。
- 依第二部分額外說明回合配置對應安排 reasoning schedule: Basic A 對應 `(1, 4, 7, 10)`；Basic B 對應 `(1, 3, 6, 9)`。
- 依 schedule 分開隨機配對；各 schedule 有奇數個 Basic 小組也可進行配對，若該 schedule 只有一組，則保留該組兩位受試者配對。
- 每回合先選擇一個介於 11–20 的整數；額外說明回合可選擇是否更改數字並填寫理由。
- 回合基礎報酬為最終數字選擇；如果最終數字比對手一開始選擇數字少 1，額外獲得 20 法幣；如果最終數字和對手一開始選擇數字相同，可額外 10 法幣。

#### 頁面顯示順序與時機

1. 第一回合顯示實驗說明及開始等待頁；此階段配對完成後進入回合流程。
2. 每回合先顯示數字選擇頁。額外說明回合的受試者提交初始數字後，才會進入 reasoning wait page；非額外說明回合會略過等待頁及理由頁。
3. reasoning wait page 只等待同一固定配對的對手完成初始數字選擇；不同配對（不論 schedule 相同或不同）不會互相等待。不需要理由的回合會略過此頁。
4. 等待結束後，額外說明回合顯示理由頁，受試者可維持或更改數字並提交理由。
5. 每回合由固定配對互相等待完成決策，系統計算該組報酬並顯示結果；兩位都完成結果頁後即可進入下一回合，不等待其他配對。
6. 最後一回合結果後設有階段結束等待頁，所有受試者完成本部分後才進入第四部分。

### `Phase4`: 實驗後預測

#### 頁面顯示順序與時機

1. 第 1 回合顯示實驗說明；開始後 AI 處理第二、三部分所有額外說明回合的理由，並由全體等待頁確認處理完成。
2. 接著依序進行 4 個預測回合。A、B 配置同步預測各自第 1–4 個 Basic reasoning round，並從相同配置的受試者中抽選預測對象；同一預測回合可能對應不同 Basic 原始回合。
3. 每個預測回合依序顯示預測頁、等待該階段小組完成預測、計算正確性與報酬，再顯示預測結果。完成第 1–3 回合結果後進入下一個預測回合。
4. 第 4 個預測回合結束後，不再顯示其他預測頁。系統內部仍保留 15 回合索引以對齊 AI 資料；第 15 回合顯示兩個 11–20 部分的報酬結果、總報酬頁及個人資料表單連結。

原始 Basic 回合編號記錄在 `basic_source_round`。

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
