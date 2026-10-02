# E2 交付閘門測試套件 (delivery-gate test harness)

測 `hooks/delivery_gate_shadow.py`（掛在 SubagentStop，**影子模式：只記錄、
永不阻擋**）。票：T-009。

## 為什麼需要一組固定的測試檔

合成的 stdin payload 只能證明**分類器**對不對，證明不了**真實事件長什麼樣**
（`ops/lessons.md` L-012：用代理物的證據講本尊的話）。這裡的做法是丟一個
一次性沙盒專案給真的子代理去做，讓 hook 收到真的 `SubagentStop`。

實測抓到的第一個問題就是這樣來的：**`SubagentStop` 給的 `transcript_path` 是
主 session 的逐字稿，不是子代理的**。子代理自己的在
`<主逐字稿同名資料夾>/subagents/agent-<agent_id>.jsonl`。若照著給的路徑掃，
每一列都會變成 wrote=True + verified=True（主 session 幾乎永遠兩者皆真），
整週資料全是垃圾且看不出來。

## 怎麼跑

```powershell
cd $HOME\.claude; python tools\e2-gate-test\make_fixture.py
```

會在 `drafts\e2-gate-fixture\` 建好一個玩具專案（`calc.py` + `test_calc.py`，
驗證指令用 `python -m unittest`，因為本機**沒有裝 pytest**），並印出三段
要派給子代理的 prompt。沙盒放在工作樹內是故意的：子代理繼承 cwd 範圍的檔案
權限，放 `%TEMP%` 會變成在測權限層而不是測閘門。

三個案例與預期：

| 案例 | 子代理做什麼 | 預期 |
|---|---|---|
| A | 只讀檔，不改不跑 | wrote=False → 不擋 |
| B | 改檔 + 跑 `python -m unittest`（通過） | wrote=True, verified=True → 不擋 |
| C | 只改檔，完全不跑指令 | wrote=True, verified=False → **WOULD-BLOCK** |

派完（model 用 haiku，成本上限見 `ops/environment.md`）之後看結果：

```powershell
python tools\e2-gate-test\check_shadow_log.py -n 10 --commands
```

`--commands` 會把子代理實際跑過的指令彙整出來——那是 phase 2 重建驗證白名單
的原料。**現在 hook 裡那份白名單是用猜的**，不能直接拿去當強制條件。

## 判讀

先看 `transcript_kind`：只要不是 `subagent-*` 開頭，那幾列的 wrote/verified 就
是 null（設計如此，寧可不分類也不亂猜），該次測試無效。

再看誤判率：`would_block` 的列裡，有幾個其實是好的交付？這個數字沒量出來之前，
**不開啟任何真正的阻擋**。

## 收尾

```powershell
Remove-Item -Recurse -Force $HOME\.claude\drafts\e2-gate-fixture
```

## 已知限制（不是待辦，是這個階段本來就測不到的）

- `echo pytest` 會通過白名單。影子模式量得出這個洞有多大，補不了。
- `is_error` 是工具層的錯誤旗標，是「exit code 0」的代理物，不是 exit code
  本身。若 phase 2 發現兩者會分歧，就得改用 PostToolUse(Bash) 記錄真實結束狀態。
- 逐字稿沒記到的工具呼叫，這裡一律看不到。
