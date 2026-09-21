# `domains/` — 領域設定檔機制｜Domain-profile machinery

> **中文摘要｜Chinese summary**：這個 share 只帶領域 profile 的 authoring
> machinery，不帶任何特定研究領域的已填內容。先用 template 建立自己的 profile，
> 再用 routing manifest 與 expansion guide 驗證；來源端的私有領域知識刻意不在此包。
>
> **English summary**: This share contains the machinery for authoring domain profiles,
> not filled profiles for a particular research field. Start from the template, register
> the profile in the routing manifest, and run the guide's pre-merge checks.

## 快速導覽｜Quick guide

| 項目 | 中文 | English |
|---|---|---|
| 收錄 | template、routing format、authoring／quality guide | Template, routing format, and authoring/quality guidance |
| 不收錄 | 來源端作者的 condensed-matter／semiconductor filled profiles 與私人 citation inventory | The source author's filled profiles and private citation inventory |
| 先做什麼 | 先讀 `domain-expansion-guide.md` §2，再複製 `_template.md` | Read §2 of `domain-expansion-guide.md`, then copy `_template.md` |
| 驗收 | 加入一列 `base` routing，依 guide 的 pre-merge checklist 檢查 | Add one `base` routing row and run the guide's pre-merge checklist |

## 收錄內容｜What ships

| File | 中文用途 | English purpose |
|---|---|---|
| `_template.md` | 空白 profile 骨架；包含 Nodes 1–6、literature anchors、source ledger 與 cross-domain sections | Blank profile skeleton for Nodes 1–6, literature anchors, source ledger, and cross-domain sections |
| `_routing.md` | load manifest 格式，附四列 template rows、沒有真實 domain rows | Load-manifest format with four template rows and no real domain rows |
| `domain-expansion-guide.md` | base／sub-profile／reference／boundary 的雙閘門決策樹、逐 node 品質線與 pre-merge checklist | Two-gate decision tree, node quality bars, and pre-merge checklist |

## 刻意排除內容與理由｜What is deliberately excluded

The source environment's `domains/` held filled profiles for its author's own
research fields (condensed-matter and semiconductor-device topics). Those files are
**subject-matter knowledge, not agent methodology** — they would be wrong for your
field, they are the largest content in the tree, and their presence misrepresents
what this skill is. They were removed from this share; the same applies to the
citation inventory under `../references/user-supplied-citations.md`, which now ships
as an empty template.

`domain-expansion-guide.md` still names some of those files in its illustrative
directory tree. Read those as **example filenames**, not as files you should expect
to find here.

## 對 evals 的影響｜Consequence for the skill's evals

`../evals/evals.json` retains assertions written against the excluded profiles (for
example, one checks that a material sub-profile loads in preference to its generic
parent). Those evals are kept as **worked examples of what a good domain-routing
assertion looks like** — they are not runnable against this share as-is. Rewrite
them against your own first domain, or treat their `passed`/`evidence` fields as a
record from the source environment rather than a claim about this copy.

## 建立第一個 domain｜Build your first domain

1. Read `domain-expansion-guide.md` §2 first — most authoring mistakes are a topic
   put at the wrong level, not bad content.
2. Copy `_template.md` to `<your_domain>.md` and fill Nodes 1–6 plus the
   literature/source and cross-domain sections. Node 6 (pitfalls) is the primary
   standing-trigger home; the former separate “Node 8” decision-trigger section
   was abolished in the current template, so do not invent it.
3. Add one `base` row to `_routing.md` and delete the template rows.
4. Run the guide's pre-merge checklist before relying on it.
