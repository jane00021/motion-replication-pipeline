---
name: motion-replication-pipeline
description: "当用户上传或提供一条参考视频/视频链接，并要求拆解、复刻画面动效、复刻字幕动效、验证换内容、生成 HTML 展示面板，或将已认可的复刻动效组整理进共享组件库时自动触发。负责从来源核验到逐帧拆解、可编辑重建、编码复审、HTML 面板、独立复用和发布记录的完整状态机流程。"
---

公开发布说明：当前示范输入和展示视频均为代码绘制的虚构人物 mock。历史真人视频、截图及原声媒体已经移除。历史路径和摘要仅用于追溯记录。可运行参数见 examples/inputs，播放页见 examples/index.html。真实迁移请提供有权使用的口播素材。

# Motion Replication Pipeline

这是“参考视频 -> 可编辑画面/字幕动效 -> HTML 面板 -> 可复用模板”的统一入口。
只要用户给出参考视频或视频链接，并提出“拆解、复刻、还原、做成动效组、做 HTML 预览、换字、换字体、做模板”等要求，就使用本 Skill。不要只给方案、只截帧或只做一个能播放的网页。

## 强制入口

收到新参考视频后，第一步必须：

1. 确认实际视频文件。只有链接时先用当前环境已授权的下载能力获取文件；无法获取时记录 blocker，不编造视频内容。
2. 在新项目目录初始化状态机：

```powershell
python "<skill-root>/scripts/motion_pipeline.py" init `
  --project "<新项目绝对路径>" `
  --name "<项目名>" `
  --style-id "<小写短ID>" `
  --reference "<参考视频绝对路径>"
```

3. 立即读取项目内的 `SKILL.md`、`.pipeline/state.json` 和生成的 `TASK.md`，然后按当前节点执行。不能绕过状态机直接写最终 HTML 或宣称完成。

用户要求把已有复刻入库时，先定位现有项目、认可记录、真实源码和媒体；不重新初始化已有项目。按 [认可成果入库执行](references/library-intake.md) 先给映射，再重跑原配方。03未通过时可保存按授权范围整理的候选库与技术证据，04保持待处理。

替换人物、内容或字体已经在03试作期间完成时，读取这些结果作为05的输入证据。先绑定实际视频、透明层、源码、参数、字体路径和SHA，再运行05的证据验收。只有缺少可追溯替换证据时，05才重新生成替换版本。05不重复制作已通过的替换结果。

03通过后，04-library、05-replacement、06-encoded-review和07-html-preview可以作为一个连续的后处理批次执行。批次内先整理组件和配方，再导入或生成替换结果，接着完成编码复审和HTML面板。四个节点仍分别写报告、运行preflight并accept，节点之间无需重复制作或等待新的创意审核。

`agents/openai.yaml` 保持隐式触发开启；WorkBuddy 等平台没有 Skill 注入时，以项目目录中的 `SKILL.md` 为唯一恢复入口。

跨平台独立测试：收到本技能ZIP或目录时，先读取解压目录的本SKILL.md，以解压目录作为skill-root，保留scripts、references、assets完整结构；不依赖Codex专有工具或旧聊天记录。使用当前平台可用的文件、终端和浏览器能力完成同样流程。先核对Python、ffmpeg、ffprobe与实际观看/浏览器能力；缺少能力据实记录，不把静态代码或HTTP探测当成实际播放验证。用户只要求拆解观察HTML时，在01的观察与反馈环节停止，不因为本技能覆盖完整复刻流程就继续后续节点。

## 状态机

状态只能按顺序前进；任何来源、源码、输入、报告或验证证据变化都会使当前节点及下游重新变为待处理。

```text
00-intake
  -> 01-observe
  -> 02-measure
  -> 03-pilot
  -> 04-library
  -> 05-replacement
  -> 06-encoded-review
  -> 07-html-preview
  -> 08-cleanroom
  -> 09-release
```

每个节点都必须经历：

```text
status -> next -> 实际执行 -> preflight/自检 -> accept
```

失败时使用 `block` 记录具体缺项；发现前置结果失效时使用 `reopen` 回退到最早受影响节点。禁止修改 `state.json`、收据或报告来跳过节点。

## 每次执行的硬规则

- 拆解时分别建立画面动效 family、字幕动效 family，再记录二者单独、重叠或连续接力组成的完整 occurrence。普通口播底片不自动计为画面动效；数字、问号、警示与素材变化不能重复制造相同画面 family。
- 观察面板必须在每卡主标题和结构化字段落实修正，已否定名称只保留于历史。完整组显式区分“仅画面”“仅字幕”“画面＋字幕动态组合”，支持筛选与更正，并显示组件的表达接力；不能只在备注中纠错而主卡仍显示错误机制。
- 先排除普通底片与口播主字幕，再识别真实动作组件；“有字幕”不等于“有字幕动效”。首轮展示前核对动作前后帧、共同画面机制、字幕变体、连续完整表达，以及当前名称/组件/类型的一致性。最终反馈用 `apply_observation_feedback.py` 应用、`validate_decomposition.py` 检查，不沿用合并后消失的旧ID；详见拆解反馈参考。
- 单纯切回既有画面、静态圆角框或人物位于角落不证明存在缩入／让位动画。先比较运动、遮罩和空间关系，背景、描边、素材作变体；连续口播跨越真实裁切与主体几何改变时也须检查是否应拆组。拆分、合并、排除及缓存恢复规则见拆解反馈参考。
- `01-observe` 默认提供可保存反馈的中文手动校正观察页（显著标注“仅拆解，不是复刻”），用原片逐帧改起终点、合并连续组并填写备注。收到用户反馈后先应用标注、解释机制修订与画面×字幕搭配，再做01/02验收；详见 [拆解与用户反馈闭环](references/decomposition-feedback.md)。
- 用户明确当前在测试/反馈修改skill时，记录 `workflow-context.json` 的 `mode: skill-test-feedback`，停在拆解与技能修订范围。“继续”沿用此范围，不自行进入03复刻。保存标注、应用反馈、用户认可界面、节点通过分别记录，不能互相替代。

- 参考视频只有成片时，称“参考重建”，不能称拿到了原作者源码。
- 先保留原文、原人物、原图、原字体和原时间关系做基准版，再做换内容版和换字体版。
- 画面动效拆成真实层：人物、视频、图片、背景、图形、遮罩、前后景和声音落点；不能用静态截图冒充可编辑动效。
- 字幕动效必须保留文本、词/字时钟、字体、字宽、行距、基线、描边、阴影、重点词角色和入/停/退动作；不能把字幕烧死在一张图片里。
- 同一组的入场、推进、阅读停留、退出和下一镜交接都要复现；只看落定帧不算完成。
- 改内容、改字体、改图片、改项数和改事件时点必须真实改变渲染，并检查溢出、错位、缺字和遮挡。
- 不用白色卡片、统一淡入或普通字幕替代参考中有明确机制的动作。
- 只有确实连续观看、逐帧观察、编码解码或试听过，才能在报告中写对应结论；抽帧和信号分析不能冒充完整观看或听感判断。
- HTML 是验收和展示面板，真正可复用的源码、参数、字体和媒体入口必须留在项目源工程中。
- 原素材基准、换内容版、换字体版和清理/修补版分目录保存，不能覆盖或混为一套。
- 分组时必须区分 `occurrence`（一次实际出现）和 `family`（可复用机制）；同一机制只换文字、图片或事件时点不能重复计组。
- `00-intake`、`01-observe`、`02-measure` 只能产出来源核验、参考切片、联系表、关键帧、分层测量和拆解报告；禁止生成或展示 `baseline`、`changed-content`、`changed-font`、复刻视频或“可编辑模板”标签。没有进入 `03-pilot` 并完成原素材基准复现前，任何替换版都必须视为无效产物。

## 已认可复刻案例与审核节奏

进入03前先读 [认可案例、接口和两组审核流程](references/approved-case-workflow.md)。默认先复刻目录前两个完整组，真实编码、两条对照并等用户认可；通过后按共享family划分工作包，分发subagent并行复刻，主进程固定接口/写入归属并汇总复核。用户本轮只要求记录与更新时，不据此扩大建库。

公开版本保存默认合成迁移示范视频及历史认可案例代码和参数。示范素材可作为默认输入，案例坐标/字体/时钟不是通用规则；原字体身份、听审与正式状态机验收按证据分别记录。

## 节点执行索引

完整组验证与组件复用分开：采用“画面动效库＋字幕动效库＋引用式完整组合配方＋搭配规则”，详见 [库与组合合同](references/library-composition.md)。学习时按完整组验证，沉淀时只拆真正可独立表达/替换/验证的部分；配方引用组件，不复制实现。日常调用优先成熟配方；新搭配先标待验证。

字幕复刻进入03、返工或并行分发前，必读 [字幕机制判别与真实执行器](references/subtitle-execution.md)。技能已内置六组认可参数、字体、具名RGBA渲染和编码校验入口；先辨明切半、让位、独立英文、逐字波浪或揭晓机制，再选择实现，不按“金色重点词”统一套T01。案例参数须按新参考重新测量。

进入03复刻或返工前，先读 [同字校准、语义角色与编码返工](references/replication-calibration.md)。先同字字形/排版/材质（含可见阴影），再分层时钟与真实编码对照，最后干净新输入迁移；颜色与光效绑定语义角色，禁止套用固定字符位置。复审默认每组只显示原对标与新口播应用结果；多版本及校准证据留在工程，不用面板数量代替质量。

`02-measure` 和 `03-pilot` 的 `fidelityAudit` 按本批 occurrence 填写。对每组独立确认人物占幅、字幕字面是否被遮挡，以及锚点／颜色／拖影的阶段时钟。满幅需按每个背景阶段检查真实人物 alpha 下缘，字幕需按实际笔画核对留白。详见 [构图与字幕验收](references/fidelity-audit.md)。

详细操作、产物和验收条件在 `references/stage-playbook.md`；01/02的中文校正页、用户反馈和技能测试模式在 `references/decomposition-feedback.md`；画面动效拆解在 `references/visual-motion.md`；字幕动效拆解在 `references/subtitle-motion.md`；03之后的复刻HTML面板合同在 `references/html-preview.md`；报告字段在 `references/report-schema.md`。

每个节点开始前运行：

```powershell
python "<skill-root>/scripts/motion_pipeline.py" status --project "<项目绝对路径>"
python "<skill-root>/scripts/motion_pipeline.py" next --project "<项目绝对路径>"
```

节点完成后，先执行报告中的所有检查，再运行：

```powershell
python "<skill-root>/scripts/motion_pipeline.py" preflight `
  --project "<项目绝对路径>" `
  --report "<当前节点报告.json>"

python "<skill-root>/scripts/motion_pipeline.py" accept `
  --project "<项目绝对路径>" `
  --report "<当前节点报告.json>"
```

HTML 节点额外运行：

```powershell
python "<skill-root>/scripts/motion_pipeline.py" validate-html `
  --project "<项目绝对路径>" `
  --html "preview/index.html"
```

视频节点额外运行：

```powershell
python "<skill-root>/scripts/motion_pipeline.py" validate-video `
  --project "<项目绝对路径>" `
  --video "render/portrait/final.mp4"
```

## 交付最低标准

最终项目至少包含：

- 参考源和来源/时码记录
- 动效组目录与逐帧测量证据
- 画面动效和字幕动效的可编辑源工程
- 原素材基准版
- 换内容版
- 换字体版
- 编码后复审视频和复审记录
- 可逐组播放的 `preview/index.html`
- HTML 面板使用的 `metadata.json`
- 清洁目录独立复用记录
- 最终版本、SHA256、支持画幅、验证范围和剩余限制

用户只说“先给我看看”时，可以停在 `03-pilot` 或 `07-html-preview`，但必须明确当前节点、已完成检查和下一节点；不能把局部预览说成完整模板。
