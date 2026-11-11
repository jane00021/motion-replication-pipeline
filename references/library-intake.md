# 04 入库：从用户认可的完整组到可调用共享库

适用：一个或多个项目已有真实复刻结果，用户要求把这些结果入库。目标是复用源码和参数，保留原有组合与认可证据。组件可组合不等于新的搭配通过；本流程默认不创作新搭配。

## 1. 锁定认可范围，先给映射

- 查项目状态、最新用户反馈、实际页面媒体、复刻源码、配方和输入。用认可记录及 SHA256 锁定实际展示版本，过期状态随证据更新。保留旧 ID/合并成员与原参考时码；未认可、试作、废弃版单列。若认可记录只给口头范围，先把范围绑定到实际展示文件与当时参数，不能拿最新文件倒推认可。
- 独立判别画面与字幕机制。比较表达职责、动作与缓动、空间关系、层级和事件骨架。文字、素材、图标、颜色或同骨架的事件时点通常是参数；标题在人物后、字幕是否随父层变换、揭晓是否逐字等差异要看真实层和帧。相同动作的表现变体优先留在同一入口；独立职责或编舞无法用同一合同表达时记录拆分理由。
- 先交付“原完整组 → 画面组件 → 字幕组件 → 原组合配方”映射，附合并和保留理由。完成分组识别再提炼运行器，不因两个完整组不同就复制两套组件。相同组件配不同字幕、或相同组件但编舞不同，分别保留原配方或变体。普通口播底片无需虚报为组件。

## 2. 建真实入口与独立预览

- 每个共享机制一个有版本的入口，按项目语言实现，例如用 component(id, input, localFrame, canvas) 返回具名 RGBA 层。合同写中文名、表达作用、输入和可改字段、时钟单位、输出层、空间/遮挡约束、来源和验证范围。提炼相同动作，不能只让多个 ID 指向各自旧整组渲染器。保留素材、字体、抠像的有效路径与版本，复用素材槽和资源，不按每套配方复制实现。
- 配方通过注册表调用组件，声明组件 ID/版本、参数绑定、共享时钟、图层次序、接管、退出及原组 ID/时码。保留原组实际台词和素材，不重新搭配。渲染同一输入，必要时分别对照旧实现与共享实现的具名层，含字幕透明度、人物前后层、裁切与合成顺序。
- 单独调用每个组件并编码预览。字幕输出真实 RGBA（如 PNG 序列或支持 alpha 的视频），另叠到统一观察底输出可播放 MP4；画面使用干净口播，避免其他动效。检查输出真实有变化、帧数与独立入口一致，字幕观察底不能烘进透明交付层。
- 面板三栏：画面动效库、字幕动效库、完整组合配方。前两栏显示中文名、表达用途、可改内容、来源、验证状态和独立播放；配方显示引用组件和接管/退场。原配方回归对照留工程验证目录；另列未入库组。在真实浏览器检查加载、播放、拖动和切换，记录实际结果。

## 3. 以共享机制分批跑原配方

Skill 提供 scripts/library_intake.py，项目初始化也会带一份 .pipeline/library_intake.py。工具不改状态、不挑选字体或替项目写渲染器。先写好项目自己的共享配方入口与独立组件入口，工具调用真实配方并对两个编码结果完整解码。需要 Python、NumPy、ffmpeg 与 ffprobe。

~~~powershell
python -X utf8 "<skill-root>/scripts/library_intake.py" map --project "<项目>" --plan "library/intake-plan.json" --output "reviews/library/mapping-v1"
python -X utf8 "<skill-root>/scripts/library_intake.py" regress --project "<项目>" --plan "library/intake-plan.json" --component V-FOCUS --output "reviews/library/focus-v1"
python -X utf8 "<skill-root>/scripts/library_intake.py" verify --project "<项目>" --plan "library/intake-plan.json" --receipt "reviews/library/focus-v1/regression.json"
~~~

- map 在提炼后校验机器可读映射并导出 Markdown 和 JSON；前述人工映射先于提炼。regress 的 --component 可重复，取所选组件全部原配方的并集；不指定时重跑计划全部。对正式范围的每批都运行，verify 传入所有批次收据。用完整活动范围的同一计划和冻结文件运行各批；任何计划或绑定文件变化，旧收据都会过期。失败保留日志，用新输出目录复测。
- 程序比较编码尺寸、完整帧数、逐帧 PTS、尾帧时长和逐帧 RGB；检查音轨数量，并记录轨道元数据。默认像素完全相等。编码差异需事先填写有理由的容差并检查最大误差帧，不能用提高容差掩盖字体、动作或层级变化。没有尾帧时长的编码需先核实时间边界并产出可测证据。技术回归不证明听审、观感认可或新输入适配。实际对照进场、接管、稳定与退出，音效/口播需听审时单独记录。
- 活动目录只列当前入库范围，旧版存档。正式 04 必须等 03 通过并激活 04，补齐独立组件、浏览器、保真和局限检查。04 报告用 libraryRegression.plan 与 libraryRegression.receipts 引用本次计划及批次收据；新项目的 preflight 会重验覆盖、绑定与活动目录是否一致。也可用 verify 的 --catalog 参数检查活动目录。既有项目使用安装版命令或同步脚本与引用后使用本地入口，保留旧状态与缺项。预先整理的候选库不升级节点。
- 保持三种状态分别记录：用户认可原媒体、共享实现重跑技术通过、对新输入或新搭配验证。后两种不能继承第一种。

## 入库计划最小示例

下方只示范字段。项目内路径相对 --project，实际文件和 SHA 由项目生成，不采用示例参数。旧项目的认可记录原样存档，不改变其内容；row 是访问认可条目的 JSON 路径，数组下标用数字。认可条目中必须有匹配的媒体哈希和被绑定输入/配方哈希。多个项目的必要文件可按源项目分别归档到当前项目，媒体复制后仍须保持 SHA 不变。

~~~json
{
  "schema": 1,
  "scope": "本次已认可的完整组，原组合回归",
  "components": [{
    "id": "V-FOCUS",
    "kind": "visual",
    "version": "1.0.0",
    "name": "椭圆暗角聚焦",
    "signature": "径向遮罩：周边渐暗 → 停留 → 恢复",
    "reason": "原组合共用径向遮罩；中心与时间为参数",
    "entrypoint": "library.runtime:component",
    "contract": "library/contracts/V-FOCUS.json",
    "files": ["library/runtime.py"]
  }],
  "recipes": [{
    "id": "R-A-01",
    "origin": "A:01",
    "recipe": "library/recipes/R-A-01.json",
    "files": ["library/run.py", "library/runtime.py", "library/inputs/A-01.json", "assets/talking.mp4"],
    "argv": ["{python}", "library/run.py", "--recipe", "{recipe}", "--output", "{output}"],
    "result": "result.mp4",
    "approval": {
      "record": "reviews/approval-A.json",
      "recordSha256": "<认可记录文件的 SHA256>",
      "row": ["groups", 0],
      "mediaHashKey": "mediaSha256",
      "media": "library/approved-media/A-01.mp4",
      "mediaSha256": "<认可媒体 SHA256>",
      "files": {"source/A-01-input.json": "<认可条目中保存的输入 SHA256>"}
    }
  }]
}
~~~

配方 JSON 须包含 id、newCombination:false、componentRefs（每项 id 与 version）、purpose、clock、zOrder、handoff、exitPolicy。目录的 components 含 id、kind、version、entrypoint、contract；recipes 列出实际配方 JSON 路径。给运行器的 argv 使用参数数组，不经过 shell。{python}、{recipe}、{output} 必须分别占一个参数；运行器自行创建独立输出目录，实际产物要在其内。调用前检查 argv 对应当前项目可信源码。files 要列全真实输入、素材、字体及运行依赖，不能只列启动文件；原输入、原配方能绑定的均记录。可选 tolerance 含 meanRgb、worstFrameRgb、ptsMs 和 reason，像素用 0–255 尺度，时钟用毫秒。技术证据只覆盖此计划和被绑定文件。

