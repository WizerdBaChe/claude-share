// architecture-diagramming/capability-set.build.mjs
//
// The capability set drawn with its own toolchain. This script IS the diagram;
// capability-set.html is a projection of it (carrier-playbook, § Source-of-truth
// & regeneration — the model plus this script is what regenerates, never the
// pixels). Written 2026-08-29 against the `build()` contract in
// archdiag/README.md, using the copy of the library that ships in this repo.
//
// Node RECTS are hand-authored: positions carry semantics (which layer a file
// belongs to, which way the flow runs), so the router never touches them. Every
// edge path and pill anchor is machine-routed by the 'channel' provider.
//
// Every node and edge carries `ev` — an evidence anchor naming the file or the
// section this element was read out of. The schema rejects the build without
// it; that is the fabrication firewall as running code rather than as advice.
//
// Regenerate:  node architecture-diagramming/capability-set.build.mjs
// Expect: "written: …; schema + build-time asserts passed; sha256 …" and, on a
// re-run with no edits, git reporting the html unchanged (the receipt property).

import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { build } from './archdiag/index.mjs';
import { route, applyRoutes } from './archdiag/route.mjs';
import { table } from './archdiag/tables.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const GRID = 8;

// --------------------------------------------------------------------------
// View 1 — what the set is made of, and who owns which layer.
// The question: "if I install this, which file decides what?"
// --------------------------------------------------------------------------
const vSet = {
  id: 'set',
  title: '1 能力集合結構',
  subtitle: '問題：裝了這一組之後，哪個檔案決定哪件事？',
  vb: [1280, 664],
  declared: [
    '四層＝理論／生產／稽核／執行，不是四顆 skill：生產與稽核共用同一份理論',
    '虛線 = 「引用、不複寫」——理論只有一份，第二份就是會漂移的分叉',
    '節點位置帶語意（同一層同一列）；邊為機器走線',
  ],
  declaredCrossings: 2,
  containers: [
    { id: 'cTheory', x: 40, y: 72, w: 400, h: 240, title: '理論層 · product-design-thinking/references/' },
    { id: 'cProd', x: 480, y: 72, w: 400, h: 336, title: '生產層 · diagram-authoring/' },
    { id: 'cAudit', x: 920, y: 72, w: 320, h: 240, title: '稽核層 · code-review-deep-checklist/' },
    { id: 'cExec', x: 480, y: 448, w: 760, h: 168, title: '執行層 · architecture-diagramming/archdiag/（2026-08-29 收錄）' },
  ],
  nodes: [
    {
      id: 'rep', kind: 'block', x: 72, y: 120, w: 336, h: 72,
      t: 'representation-models.md',
      l: ['選型：一個問題一種主圖', '盲點配對（單視圖證不了完整性）'],
      ev: 'architecture-diagramming/README.md § 檔案',
    },
    {
      id: 'vic', kind: 'block', x: 72, y: 216, w: 336, h: 72,
      t: 'view-integrity-checks.md',
      l: ['各圖種完整性檢查、跨視圖對應', '缺口表格式（view/element/defect/…）'],
      ev: 'architecture-diagramming/README.md § 檔案',
    },
    {
      id: 'da', kind: 'proc', x: 512, y: 120, w: 336, h: 72,
      t: 'SKILL.md',
      l: ['模式路由、fabrication firewall', '結構模型先行、三段驗證'],
      ev: 'skill-toolkit/skills/diagram-authoring/SKILL.md',
    },
    {
      id: 'not', kind: 'block', x: 512, y: 216, w: 336, h: 64,
      t: 'notation-precision.md',
      l: ['畫法慣例、幾何自檢斷言組'],
      ev: 'skill-toolkit/skills/diagram-authoring/references/notation-precision.md',
    },
    {
      id: 'car', kind: 'block', x: 512, y: 304, w: 336, h: 72,
      t: 'carrier-playbook.md',
      l: ['載體精度天花板與驗證路徑', '§archdiag：本列指向執行層'],
      ev: 'skill-toolkit/skills/diagram-authoring/references/carrier-playbook.md',
    },
    {
      id: 'pr', kind: 'proc', x: 952, y: 120, w: 256, h: 96,
      t: 'project-review.md（Mode B）',
      l: ['從 code 反向重建視圖', '不是抄既有文件', '重建視圖＋缺口表留檔'],
      ev: 'skill-toolkit/skills/code-review-deep-checklist/references/project-review.md',
    },
    {
      id: 'lib', kind: 'store', x: 512, y: 496, w: 296, h: 88,
      t: 'archdiag 函式庫（11 檔）',
      l: ['schema → 幾何斷言 → marker 閉合', '→ 決定性輸出 → sha256 收據'],
      ev: 'architecture-diagramming/archdiag/README.md § Modules',
    },
    {
      id: 'sc', kind: 'block', x: 856, y: 496, w: 176, h: 88,
      t: 'selfcheck.mjs',
      l: ['頁內第 1–8 項檢查', '唯一來源'],
      ev: 'architecture-diagramming/archdiag/README.md § Invariants',
    },
    {
      id: 'ga', kind: 'block', x: 1064, y: 496, w: 152, h: 88,
      t: '.gitattributes',
      l: ['archdiag/** = LF', '收據的前提'],
      ev: 'architecture-diagramming/README.md § archdiag 性質 3',
    },
  ],
  edges: [
    { id: 'e1', type: 'eps', from: 'da', to: 'rep', pill: '引用不複寫', ev: 'SKILL.md Step 1/2 相對路徑引用' },
    { id: 'e2', type: 'eps', from: 'da', to: 'vic', pill: '引用不複寫', ev: 'SKILL.md Reference files 節' },
    { id: 'e3', type: 'eps', from: 'pr', to: 'vic', pill: '同一支儀器', ev: 'project-review.md Mode B 視圖層' },
    { id: 'e4', type: 'call', from: 'da', to: 'not', ev: 'SKILL.md Step 3–5' },
    { id: 'e5', type: 'call', from: 'da', to: 'car', ev: 'SKILL.md Step 3–5' },
    { id: 'e6', type: 'call', from: 'car', to: 'lib', pill: '§archdiag', ev: 'carrier-playbook.md § Audit view-set toolchain' },
    { id: 'e7', type: 'data', from: 'lib', to: 'sc', pill: '唯一來源', ev: 'index.mjs → selfcheck.inPageScript' },
    { id: 'e8', type: 'proto', from: 'ga', to: 'lib', pill: 'LF pin', ev: '.gitattributes archdiag/**' },
    { id: 'e9', type: 'trans', from: 'pr', to: 'da', pill: '要簡報級交付就回生產層', ev: 'architecture-diagramming/README.md § 機制' },
  ],
};

// --------------------------------------------------------------------------
// View 2 — the design entry, as a data-flow view.
// The question: "a new diagram is asked for; what happens, in what order?"
// --------------------------------------------------------------------------
const vDesign = {
  id: 'design',
  title: '2 設計入口（資料流）',
  subtitle: '問題：要一張新圖，資料依序經過什麼，哪一關會擋下來？',
  vb: [1280, 560],
  declared: [
    '兩個 gate 是硬關卡：資料閘門擋「編造」，健全性檢查擋「不完整」',
    '缺口不是繞過，是產物：缺口表與圖一起交付',
    '交付＝圖＋圖例＋缺口表＋再生源，四件缺一不成立',
  ],
  declaredCrossings: 0,
  nodes: [
    { id: 'q', kind: 'ext', x: 40, y: 128, w: 168, h: 72, t: '問題', l: ['要回答什麼', '給誰看'], ev: 'README § 機制：設計入口' },
    { id: 'pick', kind: 'proc', x: 256, y: 128, w: 176, h: 72, t: '選型', l: ['一問題一主圖', '＋盲點配對'], ev: 'representation-models.md' },
    { id: 'fw', kind: 'proc', x: 480, y: 128, w: 184, h: 72, t: '資料閘門', l: ['fabrication firewall', '沒有的連線不補'], ev: 'diagram-authoring SKILL.md Step 0' },
    { id: 'model', kind: 'store', x: 712, y: 128, w: 200, h: 72, t: '結構化文字模型', l: ['state×event 矩陣', 'node/edge 表'], ev: 'diagram-authoring SKILL.md Step 1–2' },
    { id: 'ic', kind: 'proc', x: 712, y: 264, w: 200, h: 72, t: '健全性檢查', l: ['單視圖＋跨視圖', 'ISO 42010 correspondence'], ev: 'view-integrity-checks.md §1–§2' },
    { id: 'gap', kind: 'store', x: 480, y: 264, w: 184, h: 72, t: '缺口表', l: ['view/element/defect', 'severity/basis'], ev: 'view-integrity-checks.md §3' },
    { id: 'carr', kind: 'proc', x: 960, y: 128, w: 184, h: 72, t: '載體選擇', l: ['mermaid / SVG', 'HTML / PPTX'], ev: 'carrier-playbook.md' },
    { id: 'ver', kind: 'proc', x: 960, y: 264, w: 184, h: 72, t: '三段驗證', l: ['建置期 → 頁內 → 人'], ev: 'diagram-authoring SKILL.md Step 5' },
    { id: 'del', kind: 'store', x: 712, y: 400, w: 432, h: 72, t: '交付', l: ['圖＋圖例＋缺口表＋再生源（模型＋腳本）'], ev: 'README § 機制：交付' },
  ],
  edges: [
    { id: 'd1', type: 'data', from: 'q', to: 'pick', ev: 'README § 機制' },
    { id: 'd2', type: 'data', from: 'pick', to: 'fw', ev: 'README § 機制' },
    { id: 'd3', type: 'warn', from: 'fw', to: 'model', pill: '過不了就回去要資料', ev: 'SKILL.md Step 0 閘門語意' },
    { id: 'd4', type: 'data', from: 'model', to: 'ic', ev: 'README § 機制' },
    { id: 'd5', type: 'warn', from: 'ic', to: 'gap', pill: '缺口先進表', ev: 'view-integrity-checks.md §3' },
    { id: 'd6', type: 'data', from: 'ic', to: 'carr', ev: 'README § 機制' },
    { id: 'd7', type: 'data', from: 'carr', to: 'ver', ev: 'carrier-playbook.md 驗證路徑' },
    { id: 'd8', type: 'data', from: 'ver', to: 'del', ev: 'README § 機制' },
    { id: 'd9', type: 'data', from: 'gap', to: 'del', pill: '缺口表隨圖交付', ev: 'README § 機制：交付' },
  ],
};

// --------------------------------------------------------------------------
// View 3 — the audit entry.
// The question: "an existing system needs a check-up; what is produced?"
// --------------------------------------------------------------------------
const vAudit = {
  id: 'audit',
  title: '3 稽核入口（資料流）',
  subtitle: '問題：體檢一個既有系統時，圖是從哪裡來的、留下什麼？',
  vb: [1280, 456],
  declared: [
    '重建視圖的來源是 code，不是既有文件——這是這條路的全部價值',
    '用的是設計入口的同一支儀器，不是第二套檢查',
    '留檔是為了下一輪 diff：一次體檢的產物是下一次的基準線',
  ],
  declaredCrossings: 0,
  nodes: [
    { id: 'cb', kind: 'ext', x: 40, y: 152, w: 168, h: 72, t: 'codebase', l: ['受測系統本體'], ev: 'project-review.md Mode B' },
    { id: 'rb', kind: 'proc', x: 256, y: 152, w: 192, h: 72, t: 'Mode B 重建', l: ['Standard-tier 視圖組', '從 code，不抄文件'], ev: 'project-review.md Mode B 視圖層' },
    { id: 'rv', kind: 'store', x: 496, y: 152, w: 176, h: 72, t: '重建視圖', l: ['與宣稱架構對照'], ev: 'project-review.md Mode B' },
    { id: 'inst', kind: 'proc', x: 720, y: 152, w: 192, h: 72, t: '同一支儀器', l: ['view-integrity-checks', 'integrity pass'], ev: 'architecture-diagramming/README.md § 機制' },
    { id: 'fnd', kind: 'store', x: 960, y: 88, w: 200, h: 72, t: 'findings', l: ['review.arch.view-*'], ev: 'project-review.md Mode B 輸出' },
    { id: 'arch', kind: 'store', x: 960, y: 216, w: 200, h: 72, t: '留檔（視圖＋缺口表）', l: ['下輪體檢的基準線'], ev: 'architecture-diagramming/README.md § 機制' },
    { id: 'next', kind: 'ext', x: 496, y: 320, w: 416, h: 64, t: '下一輪體檢：與留檔 diff', l: ['delta.mjs 把手工比對自動化'], ev: 'archdiag/README.md § S3 acceptance' },
  ],
  edges: [
    { id: 'a1', type: 'data', from: 'cb', to: 'rb', ev: 'project-review.md Mode B' },
    { id: 'a2', type: 'data', from: 'rb', to: 'rv', ev: 'project-review.md Mode B' },
    { id: 'a3', type: 'data', from: 'rv', to: 'inst', ev: 'architecture-diagramming/README.md § 機制' },
    { id: 'a4', type: 'data', from: 'inst', to: 'fnd', ev: 'project-review.md Mode B 輸出' },
    { id: 'a5', type: 'data', from: 'inst', to: 'arch', ev: 'architecture-diagramming/README.md § 機制' },
    { id: 'a6', type: 'trans', from: 'arch', to: 'next', pill: '基準線', ev: 'archdiag delta.mjs' },
    { id: 'a7', type: 'egress', from: 'next', to: 'rb', pill: '再跑一次', ev: 'architecture-diagramming/README.md § 機制' },
  ],
};

// --------------------------------------------------------------------------
// View 4 — the verification ladder as a state machine.
// The question: "what does it take for a diagram to count as accepted, and
// what does a failure at each rung do?" A sequence view would be one run;
// completeness of the failure space needs the machine.
// --------------------------------------------------------------------------
const vGate = {
  id: 'gate',
  title: '4 驗證階梯（狀態機）',
  subtitle: '問題：一張圖要通過什麼才算「驗收過」？每一關失敗會退回哪裡？',
  vb: [1280, 512],
  declared: [
    '三段驗證＝兩段機器＋一段人；人的那段不可由機器代簽',
    '凍結後任何改動都重開 Step 5，收據重發（驗收過的位元組變了就不是那一份）',
    '完整性由狀態機承擔：每個狀態的失敗邊都畫出來，不是只畫快樂路徑',
  ],
  declaredCrossings: 1,
  inits: [{ at: [64, 128], to: [128, 128] }],
  nodes: [
    { id: 's0', kind: 'state', x: 128, y: 96, w: 176, h: 64, t: '模型（草稿）', l: ['結構化文字，尚未渲染'], ev: 'SKILL.md Step 1–2' },
    { id: 's1', kind: 'state', x: 376, y: 96, w: 192, h: 64, t: '建置期檢查', l: ['schema＋幾何斷言＋marker'], ev: 'archdiag/index.mjs pipeline' },
    { id: 's2', kind: 'state', x: 640, y: 96, w: 192, h: 64, t: '頁內幾何自檢', l: ['第 1–8 項，真 getBBox'], ev: 'archdiag/selfcheck.mjs' },
    { id: 's3', kind: 'state', x: 904, y: 96, w: 192, h: 64, t: '外觀人審', l: ['visual_review 三態'], ev: 'SKILL.md Step 5（B-4）' },
    { id: 's4', kind: 'state', x: 904, y: 256, w: 192, h: 64, t: '凍結（已驗收）', l: ['sha256 收據'], ev: 'SKILL.md Step 5（B-3）' },
    { id: 'f1', kind: 'stateT', x: 376, y: 256, w: 192, h: 64, t: '建置失敗', l: ['throw，不產檔'], ev: 'archdiag/index.mjs throw 條件' },
    { id: 'f2', kind: 'stateT', x: 640, y: 256, w: 192, h: 64, t: '診斷物件（B-1）', l: ['碼＋建議修法＋有界修復'], ev: 'SKILL.md B-1／B-2' },
    { id: 'e0', kind: 'stateT', x: 376, y: 400, w: 456, h: 64, t: '版本升版（D-043）', l: ['驗收後的任何改動：回報＋使用者裁決，絕不靜默重生'], ev: 'archdiag/MAINTENANCE.md M1' },
  ],
  edges: [
    { id: 'g1', type: 'trans', from: 's0', to: 's1', pill: 'build()', ev: 'archdiag/index.mjs' },
    { id: 'g2', type: 'trans', from: 's1', to: 's2', pill: 'pass', ev: 'archdiag/index.mjs' },
    { id: 'g3', type: 'trans', from: 's2', to: 's3', pill: 'PASS／0 診斷', ev: 'archdiag/selfcheck.mjs' },
    { id: 'g4', type: 'trans', from: 's3', to: 's4', pill: '人簽核', ev: 'SKILL.md Step 5' },
    { id: 'g5', type: 'warn', from: 's1', to: 'f1', pill: 'fail', ev: 'archdiag/index.mjs throw' },
    { id: 'g6', type: 'warn', from: 's2', to: 'f2', pill: 'fail', ev: 'SKILL.md B-1' },
    { id: 'g7', type: 'trans', from: 'f1', to: 's0', pill: '改模型', ev: 'SKILL.md 修復次序' },
    { id: 'g8', type: 'trans', from: 'f2', to: 's0', pill: '有界修復後重跑', ev: 'SKILL.md B-2' },
    { id: 'g9', type: 'warn', from: 's3', to: 'f2', pill: '外觀退回', ev: 'SKILL.md B-4 三態' },
    { id: 'g10', type: 'trans', from: 's4', to: 'e0', pill: '任何後續改動', ev: 'archdiag/MAINTENANCE.md M1' },
    { id: 'g11', type: 'absent', from: 'e0', to: 's4', pill: '沒有「靜默重生」這條邊', ev: 'archdiag/MAINTENANCE.md M1（明訂禁止）' },
  ],
};

// --------------------------------------------------------------------------
// View 5 — the library's own module graph. The scan's most literal answer to
// "what did we just ship?", and the view that makes the single-source
// invariant visible as a shape rather than as a sentence.
// --------------------------------------------------------------------------
const vLib = {
  id: 'lib',
  title: '5 archdiag 模組圖',
  subtitle: '問題：這 11 個檔案彼此怎麼依賴？「檢查器只有一份」長什麼樣子？',
  vb: [1280, 512],
  declared: [
    '依賴讀自 import 敘述本身（node -e 逐檔掃過），不是讀 README 的描述',
    'selfcheck.mjs 沒有任何人 import 它兩次——單一來源在圖上就是「只有一個箭頭進去」',
    'vendor/ 只被 route.mjs 用；上游 rect 形狀在呼叫邊界轉接',
  ],
  declaredCrossings: 1,
  nodes: [
    { id: 'bs', kind: 'ext', x: 40, y: 208, w: 168, h: 72, t: 'build 腳本', l: ['本檔就是一份', '不隨函式庫出貨'], ev: 'archdiag/README.md § build() contract' },
    { id: 'idx', kind: 'proc', x: 264, y: 208, w: 176, h: 72, t: 'index.mjs', l: ['build()：五關管線'], ev: 'archdiag/index.mjs' },
    { id: 'sch', kind: 'block', x: 512, y: 72, w: 176, h: 64, t: 'schema.mjs', l: ['只裁決可判定的'], ev: 'archdiag/schema.mjs' },
    { id: 'ast', kind: 'block', x: 512, y: 176, w: 176, h: 64, t: 'asserts.mjs', l: ['寫檔前的幾何'], ev: 'archdiag/asserts.mjs' },
    { id: 'emt', kind: 'block', x: 512, y: 280, w: 176, h: 64, t: 'emit.mjs', l: ['樣式＋列舉來源'], ev: 'archdiag/emit.mjs' },
    { id: 'slf', kind: 'block', x: 512, y: 384, w: 176, h: 64, t: 'selfcheck.mjs', l: ['頁內檢查唯一來源'], ev: 'archdiag/emit.mjs → inPageScript' },
    { id: 'tbl', kind: 'block', x: 760, y: 384, w: 152, h: 64, t: 'tables.mjs', l: ['表格輸出'], ev: 'archdiag/tables.mjs' },
    { id: 'rte', kind: 'proc', x: 760, y: 176, w: 176, h: 64, t: 'route.mjs', l: ['正交走線＋標籤'], ev: 'archdiag/route.mjs' },
    { id: 'dlt', kind: 'proc', x: 760, y: 72, w: 176, h: 64, t: 'delta.mjs', l: ['模型層 diff'], ev: 'archdiag/delta.mjs' },
    { id: 'ven', kind: 'store', x: 1008, y: 176, w: 208, h: 64, t: 'vendor/archify-geometry.mjs', l: ['第三方 MIT，逐字'], ev: 'archdiag/vendor 檔頭' },
    { id: 'out', kind: 'store', x: 1008, y: 296, w: 208, h: 88, t: 'HTML 交付物', l: ['自帶頁內自檢', '＋ sha256 收據'], ev: 'archdiag/index.mjs 回傳值' },
  ],
  edges: [
    { id: 'l1', type: 'call', from: 'bs', to: 'idx', pill: 'build()', ev: 'README build() contract' },
    { id: 'l2', type: 'call', from: 'idx', to: 'sch', ev: "index.mjs: import { validateViews }" },
    { id: 'l3', type: 'call', from: 'idx', to: 'ast', ev: "index.mjs: import { buildAsserts }" },
    { id: 'l4', type: 'call', from: 'idx', to: 'emt', ev: "index.mjs: import { pageHtml, DEFS, EDGE }" },
    { id: 'l5', type: 'eps', from: 'sch', to: 'emt', pill: '列舉唯一來源', ev: "schema.mjs: import { FILL, EDGE }" },
    { id: 'l6', type: 'call', from: 'emt', to: 'slf', pill: '唯一一條進入邊', ev: "emit.mjs: import { inPageScript }" },
    { id: 'l7', type: 'call', from: 'rte', to: 'emt', ev: "route.mjs: import { cjkW }" },
    { id: 'l8', type: 'call', from: 'rte', to: 'ven', pill: '在呼叫邊界轉接', ev: 'route.mjs: rect adapters 註解' },
    { id: 'l9', type: 'call', from: 'bs', to: 'rte', pill: '走線在 build 之前', ev: '本檔 applyRoutes 用法' },
    { id: 'l10', type: 'call', from: 'bs', to: 'tbl', ev: '本檔 table() 用法' },
    { id: 'l11', type: 'data', from: 'idx', to: 'out', pill: '決定性位元組', ev: 'index.mjs sha256 收據' },
    { id: 'l12', type: 'data', from: 'slf', to: 'out', pill: '嵌進頁面', ev: 'emit.mjs pageHtml <script>' },
    { id: 'l13', type: 'eps', from: 'dlt', to: 'emt', ev: 'delta.mjs 與 emit 共用型別語彙' },
  ],
};

// --------------------------------------------------------------------------
// Route every view. Node positions in, edge paths out — the seam the router
// is allowed to write through, and nothing else.
// --------------------------------------------------------------------------
const raw = [vSet, vDesign, vAudit, vGate, vLib];
const routed = [];
const routeStats = [];
for (const v of raw) {
  const res = route(v, { grid: GRID });
  const diag = (res.diagnostics || []).filter((d) => d && d.code);
  if (diag.length) {
    console.error(`ROUTER DIAGNOSTICS for ${v.id}:`);
    for (const d of diag) console.error('  -', d.code, JSON.stringify(d));
    throw new Error(`router returned diagnostics for view "${v.id}" — declare or hint, never silently redraw`);
  }
  routed.push(applyRoutes(v, res));
  routeStats.push([
    v.id,
    String(v.nodes.length + (v.containers ? v.containers.length : 0)),
    String(v.edges.length),
    `${res.edges.filter((e) => e.pts).length}/${v.edges.length}`,
    String(res.crossings ?? 0) + ' / ' + String(v.declaredCrossings ?? 0),
  ]);
}

const doc = {
  lang: 'zh-Hant',
  title: 'architecture-diagramming — 能力集合自繪架構視圖組',
  h1: 'architecture-diagramming：用自己的工具鏈畫自己',
  legendbar:
    '<b>節點</b>：藍＝檔案／模組・灰＝外部・綠＝資料存放・紫＝狀態・黃＝處理　｜　'
    + '<b>邊</b>：實線＝呼叫／資料流・虛線＝「引用不複寫」・紅＝失敗或警告路徑・'
    + '<span style="opacity:.7">✕＝契約上不存在的邊</span>　｜　'
    + '每個節點與每條邊都帶 <code>ev</code> 證據錨點（schema 強制，缺一不給 build）',
  footerNote:
    '本頁由 architecture-diagramming/capability-set.build.mjs 以本 repo 出貨的 archdiag 函式庫產生；'
    + '節點位置手工編排（位置帶語意），每條邊路徑與標籤位置為機器走線。'
    + '模型＋腳本是再生源，本 HTML 是投影——要更新請改腳本後重跑，不要改像素。',
};

const sections = [
  {
    h2: '這五張圖各自回答什麼（一問題一主圖）',
    html: table(
      ['視圖', '它回答的問題', '為什麼是這個圖種', '它證明不了什麼'],
      [
        ['1 能力集合結構', '裝了之後哪個檔案決定哪件事', '結構問題 → block/C4 式分層圖', '不證明流程順序，也不證明行為完整性'],
        ['2 設計入口', '要一張新圖時資料依序經過什麼', '轉換與擋點 → data-flow', '一條路徑不是行為空間；失敗分支看第 4 張'],
        ['3 稽核入口', '體檢既有系統時圖從哪來、留下什麼', '同上，另一個方向的資料流', '不描述「重建得多準」，那是 findings 的事'],
        ['4 驗證階梯', '一張圖要過什麼才算驗收過', '完整性主張只能由狀態機承擔', '不含時間軸；每關耗時不在此圖'],
        ['5 archdiag 模組圖', '11 個檔案彼此怎麼依賴', '靜態依賴 → 模組圖', '不含執行期呼叫次數與熱點'],
      ],
    ),
  },
  {
    h2: '走線與宣告（機器產生，非人工填寫）',
    html: table(
      ['視圖', '節點＋容器', '邊', '成功走線', '實際交叉 / 宣告預算'],
      routeStats,
    ),
  },
  {
    h2: '本次掃描找到的缺口（gap report — 這一節是產物，不是免責聲明）',
    html: table(
      ['視圖', '元素', '缺口', '嚴重度', '依據'],
      [
        ['1 能力集合結構', 'global-claude-md/CLAUDE.md', '來源環境已把「選型＋盲點配對」升格為全域規則，本 repo 的 CLAUDE.md 快照尚未含這條，故圖上沒有「全域規則 → 選型」那條邊', 'medium', 'architecture-diagramming/README.md § 邊界；manifest representation-models 條目的 deferral'],
        ['2 設計入口', 'PPTX 載體', '載體那一列需要平台的 pptx 技能，本集合不附；缺件時該路徑不可用，圖上未畫成獨立分支', 'low', 'README § 安裝 3；ACCEPTANCE 未關證據格'],
        ['4 驗證階梯', '「外觀人審」狀態', '人審的判準本身無法機器化，狀態機只能畫出它存在與它的退回邊，畫不出它的內容', 'inherent', 'SKILL.md Step 5（B-4 三態）'],
        ['5 archdiag 模組圖', 'build 腳本', '來源環境的三份參考 build 腳本在不出貨的 outputs/ 樹裡；圖上的「build 腳本」節點在本 repo 只有一份實例（就是產生本頁的這支）', 'low', 'manifest [[collected]] archdiag 註解；carrier-playbook.md § Reference builds'],
        ['全部', '時序視角', '整組沒有 timing/sequence 視圖：本次掃描的五個問題沒有一個是時間問題。這是刻意空缺，不是遺漏——需要時由 representation-models 的選型表開', 'by design', 'representation-models.md 選型表'],
      ],
    ),
  },
];

build({
  outPath: path.join(HERE, 'capability-set.html'),
  grid: GRID,
  doc,
  views: routed,
  sections,
});
