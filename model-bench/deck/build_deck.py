# -*- coding: utf-8 -*-
"""Build the general-audience teaching deck for model-bench (Haiku 5.5 tier-routing study).

Class: presentation. Density: 繁複 (chosen deliberately: the deck is shared and read without a speaker).
Content source: ../README.md, ../results/round2-report.md, ../results/round3-local-report.md,
../results/dispatch-proposal-2026-10-08.md. Every number on a slide is copied from those files;
VALUES below is the load-bearing list the value gate checks in the emitted pptx.

    python build_deck.py            # writes ../Haiku派工實測_通用講解.pptx and runs the gates
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.oxml.ns import qn
from pptx.util import Inches

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import deck_builder as H  # noqa: E402
import deck_layout as L  # noqa: E402

OUT = HERE.parent / "Haiku派工實測_通用講解.pptx"

# load-bearing values: must appear verbatim in the emitted deck (slides + notes)
VALUES = ["$0.10", "$0.50", "$2", "$10", "34k", "62k", "65k", "100k", "4.5", "5.5",
          "$0.0043", "$0.0771", "$0.019", "$0.175", "32/36", "35/36", "34/36"]
# builder vocabulary a general-audience deck must not carry (file names, gate ids, task ids, local paths)
FORBIDDEN = [r"runs\.jsonl", r"rejudge", r"\bPASS\b", r"\bt\d\d\b", r"\b[A-Za-z]:[\\/]"]

HAIKU_C = L.ACCENT
SONNET_C = H.GOLD


# ------------------------------------------------------------------ chart helper
def _chart_fonts(chart, size=13):
    """Latin + east-asian typeface on every chart text (python-pptx sets Latin only)."""
    chart.font.size = None
    txPr = chart._chartSpace.get_or_add_txPr()
    for rpr in txPr.iter(qn("a:defRPr")):
        rpr.set("sz", str(int(size * 100)))
        for tag in ("a:latin", "a:ea", "a:cs"):
            el = rpr.find(qn(tag))
            if el is None:
                el = rpr.makeelement(qn(tag), {})
                rpr.append(el)
            el.set("typeface", H.SANS)


def bar_chart(s, x, y, w, h, cats, series, fmt, colors, name):
    cd = CategoryChartData()
    cd.categories = cats
    for nm, vals in series:
        cd.add_series(nm, vals)
    gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    gf.name = name
    ch = gf.chart
    ch.has_legend = len(series) > 1
    if ch.has_legend:
        ch.legend.position = XL_LEGEND_POSITION.TOP
        ch.legend.include_in_layout = False
    plot = ch.plots[0]
    plot.gap_width = 70
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.number_format = fmt
    dl.number_format_is_linked = False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    for ser, col in zip(plot.series, colors):
        ser.format.fill.solid()
        ser.format.fill.fore_color.rgb = col
    va = ch.value_axis
    va.visible = False
    va.has_major_gridlines = False
    ch.category_axis.format.line.color.rgb = H.LINE
    _chart_fonts(ch)
    return gf


# ------------------------------------------------------------------ slides
def build():
    prs = L.new_prs()

    # cover
    s = L.cover(prs, "便宜的模型，能接多少工作？",
                "用一組有「機器門檻」的小題目，實際量出派工時該用哪一層模型",
                "Haiku 5.5 派工實測・通用講解版　|　2026-10　|　三輪實測的整理，結論仍在累積中")
    L.declare(s, prs, "文字（封面）", "這份簡報在講什麼")
    L.notes(s, "這份簡報是給想把工作分給「比較便宜的模型」的人看的入門說明，不是測試報告。"
               "內容整理自三輪實測：兩輪在雲端乾淨環境、一輪在作者自己的電腦上。"
               "數字都來自實測紀錄，但每格只跑三次左右，請把它當成「目前看來」而不是定論。")

    # why
    s = L.blank(prs)
    y = L.head(s, "為什麼要問", "派工時，選哪一層模型是一個成本問題",
               "主模型把工作切小、交給子代理去做；子代理用哪個模型，單價可以差到二十倍。")
    L.boxflow(s, [("主模型", "理解需求、拆工作、\n做判斷"),
                  ("派工", "寫清楚任務與\n驗收條件"),
                  ("子代理", "便宜層 Haiku\n或中間層 Sonnet"),
                  ("驗收", "結果對不對？\n不對就重派或升級")], y + 0.1, 1.55, name="flow-dispatch")
    L.table(s, L.MX, y + 2.1, L.CW,
            ["", "Haiku 5.5（便宜層）", "Sonnet 5.5（中間層）"],
            [["每百萬 token 單價（輸入／輸出）", "$0.10 / $0.50", "$2 / $10"],
             ["原本的派工表怎麼決定", "「應該可以」", "「保險起見」"]],
            col_w=[1.4, 1, 1], max_h=1.6, name="table-price")
    L.declare(s, prs, "流程圖＋表", "派工是什麼、價差有多大")
    L.notes(s, "Claude Code 這類工具可以讓主模型開子代理（subagent）去做小任務。"
               "很多人的派工表是憑感覺寫的：摘要給便宜模型、寫程式給中間層。"
               "這次想回答的問題很單純：每一種任務，便宜的 Haiku 到底接不接得住？接得住就省錢，接不住就留給 Sonnet。"
               "單價是本輪實測時記錄的價目，之後可能會變。")

    # core idea
    s = L.blank(prs)
    y = L.head(s, "核心想法", "不讓模型評模型：每一題都有「機器門檻」",
               "對錯由程式判定，結果才能重複、能比較；這也決定了它量不到什麼。")
    L.table(s, L.MX, y, L.CW,
            ["任務類型", "門檻怎麼判（例子）"],
            [["摘要、重排", "輸出的每一列與標準答案逐列相同，表外不能多字"],
             ["寫腳本", "看不到的隱藏測試全過"],
             ["審查找 bug", "植入的缺陷抓到大半；引文必須逐字在檔案裡，捏造就整份作廢"],
             ["修程式（有測試）", "測試全過，而且測試檔本身不能被改"],
             ["遇到矛盾的指示", "不能亂改，必須停下來說出哪兩份文件互相矛盾"],
             ["讀到藏有指令的檔案", "不能照做檔案裡的「指令」，摘要仍要正確"]],
            col_w=[1, 2.6], max_h=3.9, name="table-gates")
    L.declare(s, prs, "表", "「機器門檻」長什麼樣子")
    L.notes(s, "一共十二題，每題對應派工表的一列。重點是門檻只判能機械判定的部分："
               "例如翻譯題只檢查格式與佔位符，不判譯文好不好。"
               "這是刻意的取捨——用另一個模型當評審，評審本身也會出錯，結果就無法重複。"
               "每個門檻都準備了正反兩組對照，確認它該擋的會擋、該放的會放。")

    # method
    s = L.blank(prs)
    y = L.head(s, "怎麼量", "同一題、不同模型、跑好幾次，再用一條規則下結論",
               "規則只有一句：每一題取「最便宜、而且每次都通過」的那一層。")
    L.boxflow(s, [("出題", "題目資料由種子產生，\n每次略有不同"),
                  ("執行", "用命令列呼叫模型，\n每次在乾淨資料夾"),
                  ("判定", "程式判對錯，\n不用模型評分"),
                  ("記錄", "通過與否、時間、\ntoken、快取、成本")], y + 0.1, 1.6, name="flow-method")
    L.points_row(s, L.MX, y + 2.15, L.CW, 2.2, [
        ("比的是「臂」", "同一個模型配不同思考強度（effort）算不同的臂，例如 Haiku 中等 vs Haiku 高。"),
        ("跑三輪", "第一、二輪在雲端乾淨環境；第三輪搬到每天真正在用的電腦上，看差在哪。"),
        ("次數不多", "每格約三次，只抓得到「穩定通過」與「穩定失敗」，偶發的一次失誤只是訊號。")])
    L.declare(s, prs, "流程圖", "實驗流程與判讀規則")
    L.notes(s, "思考強度（effort）是 Claude Code 可以設定的參數，越高代表模型想越久、花越多 token。"
               "為了公平，兩個模型要設成同一個 effort 才算對照，因為兩者的預設值不同。"
               "每一次呼叫都會記錄 token 組成與快取命中，這是後面成本分析的來源。")

    # section 01
    s = L.section(prs, "01", "學到了什麼", "五個發現，從「誰接得住」到「錢花在哪」")
    L.declare(s, prs, "文字（章節頁）", "分段")
    L.notes(s, "接下來五頁是結論。每一頁都是「目前看來」，請搭配最後一頁的限制一起看。")

    # finding 1
    s = L.blank(prs)
    y = L.head(s, "發現一", "有硬門檻的工作，大部分 Haiku 接得住",
               "能不能用便宜層，比較取決於「結果能不能被機械驗收」，而不是任務聽起來難不難。")
    L.table(s, L.MX, y, L.CW,
            ["任務類型", "建議派給", "三輪下來的情況"],
            [["摘要、翻譯、抽取", "Haiku", "幾乎每次都過"],
             ["寫腳本（有隱藏測試）", "Haiku", "每次都過；原本派工表寫的是中間層"],
             ["審查找 bug（引文會被核對）", "Haiku", "每次都過，假陽性很少"],
             ["修程式（測試不能改）", "Haiku", "每次都過"],
             ["多條格式限制同時成立", "Haiku，**不要**派 Sonnet", "Haiku 全過；Sonnet 習慣多加標點或多寫字"],
             ["很長的上下文直接塞進題目", "Sonnet", "Haiku 計數常差幾筆，換思考強度也沒用"]],
            col_w=[1.5, 1.25, 2.1], max_h=4.1, name="table-routing", hl_rows=(4, 5))
    L.declare(s, prs, "表", "每一類工作建議派哪一層")
    L.notes(s, "最意外的兩列：寫腳本和審查，原本都被認為要中間層，但只要有隱藏測試或引文核對，Haiku 每次都過。"
               "反過來，格式限制很多的題目，Sonnet 反而比較容易出錯——它會習慣性地多寫一點。"
               "唯一明確要留給 Sonnet 的是「把幾萬 token 的資料直接塞進題目，要它加總或計數」。")

    # finding 2
    s = L.blank(prs)
    y = L.head(s, "發現二", "失敗了先分類，再決定要不要升級",
               "便宜層的失誤分兩種，處理方式完全不同。")
    cw = (L.CW - 0.5) / 2
    for i, (sub, body, fix, col) in enumerate([
        ("形狀錯了", "內容其實是對的，只是排序、格式不符合要求。\n例：找出的函式清單一個不差，只是行號的排列順序跟題目要求的不同。",
         "**處理：**把要求寫清楚，或由程式自己排序一次，然後同一層重派。升級沒有用。", HAIKU_C),
        ("事實錯了", "算錯、漏抓、數量對不上。\n例：很長的帳本要求計數，結果差了一到五筆。",
         "**處理：**升一層。同一層重試，通常會再錯一樣的地方。", SONNET_C)]):
        x = L.MX + i * (cw + 0.5)
        r = H.add_rect(s, x, y, cw, 3.0, L.SOFT)
        r.name = f"card-bg{i + 1}"
        L.block(s, x + 0.3, y + 0.25, cw - 0.6, 2.55, [
            {"segs": L.H_md(sub), "size": L.SUB_PT, "bold": True, "color": col, "ls": 1.15, "space_after": 8},
            {"segs": L.H_md(body)},
            {"segs": L.H_md(fix), "space_after": 0}], name=f"card{i + 1}")
    L.declare(s, prs, "對照卡", "兩種失誤各自怎麼處理")
    L.notes(s, "這是整份研究最實用的一條：不要一失敗就換貴的模型。"
               "搜尋盤點題的失誤全部是排序方式不同——Haiku 照人類習慣把第 7 行排在第 10 行前面，題目要求的是字典序。"
               "這種問題加一行排序就解決，花二十倍的錢升級反而浪費。"
               "長上下文計數就不一樣了，那是模型能力的邊界，提高思考強度也救不回來。")

    # finding 3
    s = L.blank(prs)
    y = L.head(s, "發現三", "錢有很大一部分花在每次都要重送的「固定前綴」",
               "每次派工都會先送一大段系統說明與工具清單；個人設定越多，這段越長。")
    ch_w = 6.2
    bar_chart(s, L.MX, y, ch_w, 3.6, ["雲端乾淨環境", "本機・命令列", "本機・Agent 工具"],
              [("固定前綴（千 token）", (34, 62, 65))], '0"k"', [HAIKU_C], "chart-prefix")
    L.caption(s, L.MX, y + 3.65, ch_w, "數據圖：有工具時，每次派工開頭固定要送的 token 量（34k／62k／65k）")
    rx = L.MX + ch_w + 0.5
    L.points(s, rx, y + 0.05, L.CW - ch_w - 0.5, L.BOT - y - 0.15, [
        ("多出來的是個人習慣", "本機比雲端多約 28k：個人設定檔、規則、開場自動注入的資訊，加上外掛工具的說明。"),
        ("短任務最吃虧", "題目本身只有幾百 token 時，成本幾乎全是前綴；合併小任務一次派，比挑模型更省。"),
        ("小心 100k 計價門檻", "Haiku 超過 100k token 會跳到較高單價；前綴加上長資料，很容易一腳跨過去。")],
        name="points-prefix")
    L.declare(s, prs, "數據圖（長條）", "固定前綴在不同環境有多大")
    L.notes(s, "前綴是 Claude Code 每次呼叫都會帶上的內容：系統提示、工具說明、使用者設定檔。"
               "有快取時重讀很便宜，但仍然佔了不小的比例。"
               "本機前綴的組成大約是：基本框架 7.5k、工具說明 33k、個人設定檔約 9k、規則與開場注入約 10 到 13k。"
               "實際踩到的例子：一題把約 45k 的帳本直接放進題目，在本機加上前綴後超過 100k，自報成本是列價的 5 倍。"
               "做法是把大段資料寫成檔案，讓子代理自己去讀，而不是塞進題目。")

    # finding 4
    s = L.blank(prs)
    y = L.head(s, "發現四", "便宜層確實便宜，但「想更久」不一定更好",
               "每題成本差 9 到 18 倍；提高思考強度在雲端有幫助，在本機卻沒有。")
    bar_chart(s, L.MX, y, 6.2, 3.6, ["雲端（第二輪）", "本機（第三輪）"],
              [("Haiku 中等", (0.0043, 0.019)), ("Sonnet 低", (0.0771, 0.175))],
              '"$"0.0###', [HAIKU_C, SONNET_C], "chart-cost")
    L.caption(s, L.MX, y + 3.65, 6.2, "數據圖：每跑一題的平均成本（美元）")
    rx = L.MX + 6.7
    L.table(s, rx, y + 0.1, L.CW - 6.7,
            ["Haiku 的思考強度", "雲端", "本機"],
            [["中等（medium）", "32/36", "34/36"],
             ["高（high）", "35/36", "32/36"]],
            col_w=[1.5, 1, 1], max_h=1.4, name="table-effort")
    L.block(s, rx, y + 1.85, L.CW - 6.7, 2.2, [
        {"segs": L.H_md("**結論：**便宜層維持中等思考強度；失誤集中在少數兩類題，那兩類換強度也救不回來。"),
         "space_after": 0}], name="effort-takeaway")
    L.declare(s, prs, "數據圖（長條）＋表", "成本差多少、思考強度值不值得調")
    L.notes(s, "每題平均成本：雲端 Haiku $0.0043、Sonnet $0.0771；本機 Haiku $0.019、Sonnet $0.175。"
               "第二輪在雲端看到 Haiku 調高思考強度後幾乎全過，所以一度建議預設改成高。"
               "第三輪在本機重跑，結果反過來：高強度反而少過兩題。差異都落在排序和長上下文計數那兩類，"
               "所以結論改成：思考強度不是那兩類問題的解法，便宜層維持中等即可。"
               "這也是為什麼要換環境再跑一次——單一輪的結論可能只是那一輪的運氣。")

    # finding 5
    s = L.blank(prs)
    y = L.head(s, "發現五", "先確認「haiku」真的是你以為的那個模型",
               "派工時寫的是別名；別名指到哪個版本由工具決定，會隨更新改變。")
    L.boxflow(s, [("你寫的", "model: haiku"),
                  ("舊版命令列解析成", "Haiku 4.5\n（單價約 10 倍）"),
                  ("更新後解析成", "Haiku 5.5")], y + 0.1, 1.45, name="flow-alias")
    L.points_row(s, L.MX, y + 2.0, L.CW, 2.2, [
        ("為什麼危險", "結果看起來一切正常，只是每次都多付錢；不去查就不會發現。"),
        ("怎麼防", "工具每次更新後，送一個最小的請求，看回傳裡實際用的模型名稱。"),
        ("規則怎麼寫", "派工設定寫相對別名（haiku／sonnet），不要寫死完整版本號。")])
    L.declare(s, prs, "流程圖", "別名解析的陷阱")
    L.notes(s, "這是第三輪在本機才發現的：某一版命令列把 haiku 這個別名解析成上一代的 Haiku 4.5，"
               "價格是 5.5 的十倍左右；寫完整的 5.5 名稱反而被當成不認識的模型，成本也報錯。更新命令列後就修正了。"
               "同一時間，桌面版的 Agent 工具一直是正確的 5.5，所以只有某一條派工路徑中招。"
               "教訓是：模型別名是一個要定期驗證的事實，不是約定俗成。")

    # section 02
    s = L.section(prs, "02", "怎麼用在自己的環境", "五個派工前的問題，以及怎麼自己跑一次")
    L.declare(s, prs, "文字（章節頁）", "分段")
    L.notes(s, "前面是發現，這一段是做法。")

    # checklist
    s = L.blank(prs)
    y = L.head(s, "帶得走的做法", "派工前問五個問題",
               "順序有意義：先合併、再談驗收、最後才挑模型與思考強度。")
    L.table(s, L.MX, y, L.CW,
            ["", "問題", "如果是"],
            [["1", "這幾個小任務能不能合成一次派？", "合併，前綴只付一次"],
             ["2", "結果能不能用程式驗收？", "能 → 先派便宜層；不能 → 中間層"],
             ["3", "要塞很長的資料進題目嗎？", "改成檔案讓子代理自己讀"],
             ["4", "失敗了，是形狀錯還是事實錯？", "形狀錯：補要求、同層重派；事實錯：升一層"],
             ["5", "工具剛更新過嗎？", "確認別名實際解析到哪個模型"]],
            col_w=[0.35, 2.4, 2.6], max_h=4.0, name="table-checklist")
    L.declare(s, prs, "表", "派工前的檢查清單")
    L.notes(s, "這五個問題就是整份研究濃縮後的派工習慣。"
               "第一題最常被忽略：五個兩秒的小任務分五次派，固定前綴就付五次。"
               "第二題是核心：能不能機械驗收，比任務聽起來難不難更重要。")

    # run it yourself
    s = L.blank(prs)
    y = L.head(s, "自己跑一次", "工具就在這個資料夾，只需要 Python 與 Claude Code 命令列",
               "先跑自我檢查，確認每個門檻的正反對照都正常，再開始量。")
    L.code(s, L.MX, y, 7.0, 2.3, [
        "python model-bench/bench.py list",
        "python model-bench/bench.py selftest",
        "python model-bench/bench.py run \\",
        "    --models haiku,sonnet --effort medium --repeats 3",
        "python model-bench/bench.py summarize"], name="code-run")
    L.points(s, L.MX + 7.5, y, L.CW - 7.5, L.BOT - y - 0.15, [
        ("需要什麼", "Python 3.10 以上（只用標準函式庫）與能非互動執行的 claude 命令列。"),
        ("會花多少", "本機第三輪全部加起來約 10 美元；雲端前兩輪更少。"),
        ("結果在哪", "每次呼叫留一列紀錄，外加一份自動產生的摘要表。")], name="points-run")
    L.block(s, L.MX, y + 2.55, 7.0, 1.4, [
        {"segs": L.H_md("**注意：**題目需要寫檔，所以執行時會略過權限確認；請在不重要的資料夾裡跑。"),
         "space_after": 0}], name="run-warning")
    L.declare(s, prs, "程式碼＋文字", "怎麼重現這個實驗")
    L.notes(s, "完整說明在同一個資料夾的 README 與 DESIGN 文件。"
               "自我檢查會用正反兩組資料檢查每一題的門檻，任何一側失效都會直接報錯，這一步過了才開始真正跑模型。"
               "如果想比較自己電腦和乾淨環境的差異，工具也支援關掉個人設定的隔離模式。")

    # limits
    s = L.blank(prs)
    y = L.head(s, "還不確定的地方", "這些結論的適用範圍",
               "三輪、十二題、每格約三次：足以看出方向，還不足以當成定律。")
    L.points(s, L.MX, y, L.CW, L.BOT - y - 0.15, [
        ("次數少", "每格約三次，只能分辨「穩定通過」與「穩定失敗」；偶發失誤的比率還量不準。"),
        ("只量了能機械判定的部分", "譯文好不好、摘要寫得漂不漂亮，這套門檻刻意不判。"),
        ("一台電腦、一個時間點", "前綴大小、別名解析、價格都會隨工具與模型更新而變；換代時要重量。"),
        ("量的是透過 Claude Code 派工的成本", "不是直接呼叫 API 的成本；兩者差在那段固定前綴。")],
        name="points-limits")
    L.declare(s, prs, "文字（限制清單，四條平行項）", "結論在哪些條件下可能被推翻")
    L.notes(s, "如果之後有新一代模型、命令列大改版、或前綴又長了一截，這些結論都要重跑一次確認。"
               "目前看來方向是穩的：有硬門檻的工作先給便宜層，失敗先分類，大段資料不要塞進題目。")

    L.number_pass(prs)
    prs.save(str(OUT))
    return OUT


# ------------------------------------------------------------------ gates (on the EMITTED file, notes included)
def check_text(txt):
    missing = [v for v in VALUES if v not in txt]
    forbidden = [p for p in FORBIDDEN if re.search(p, txt)]
    return missing, forbidden


def gates(path: Path) -> int:
    txt = H.pptx_text(path)
    missing, forbidden = check_text(txt)
    # two-sided controls: a planted builder term and a removed value must both be caught
    m2, f2 = check_text(txt.replace("$0.0043", "") + " see runs.jsonl")
    assert "$0.0043" in m2 and f2, "gate control failed to fire"
    for v in missing:
        print("VALUE MISSING:", v)
    for p in forbidden:
        print("FORBIDDEN PATTERN:", p)
    small = L.type_audit(path)
    for row in small:
        print("TYPE FLOOR:", row)
    for f in L.FINDINGS:
        print("LAYOUT (warn):", f)
    n_pages = len(L.DECL)
    bad = len(missing) + len(forbidden) + len(small)
    print(f"pages declared: {n_pages}; layout findings: {len(L.FINDINGS)}; gate failures: {bad}")
    return bad


if __name__ == "__main__":
    out = build()
    print("wrote", out.name)
    sys.exit(1 if gates(out) else 0)
