# Motion Replication Pipeline

用于 AI 编程助手的动效拆解与复刻 Skill。提供逐帧观察、可编辑画面与字幕重建、未剪辑口播迁移验证、共享组件入库、HTML 审核和封版流程。

**仅限非商用使用。** 本项目采用 PolyForm Noncommercial 1.0.0，允许符合许可的学习、研究、修改与分享。商业用途须另行获得许可。完整条款见 [LICENSE.md](LICENSE.md)。第三方字体、模型与示例素材的范围见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 效果示例

以下8个示例使用代码绘制的虚构人物和图形。6组字幕调用既有可编辑字幕执行器，2组画面演示对应合成机制。参数保存在 examples/inputs，视频均为无声 mock 演示。

| 完整组 | 效果 | 实际视频与参数 |
|---|---|---|
| 暗角聚焦、底部素材与问句接管 | ![暗角聚焦示例](examples/gifs/cg01.gif) | [完整结果](examples/videos/cg01.mp4) |
| 前景符号下落与人物后标题 | ![符号下落示例](examples/gifs/cg02.gif) | [完整结果](examples/videos/cg02.mp4) |
| 白句切半与金句接管 | ![字幕切半示例](examples/gifs/N21.gif) | [结果](examples/videos/N21.mp4) · [参数](examples/inputs/N21.json) |
| 白句对角让位 | ![对角让位示例](examples/gifs/N22.gif) | [结果](examples/videos/N22.mp4) · [参数](examples/inputs/N22.json) |

另附 N07 上下切半插句、N13 中英双层标题、N17 逐字波浪与 N24 逐字揭晓接力，共 8 个展示案例。[示例目录](examples/catalog.json)

本地播放示例页面。

```bash
python -m http.server 8765
```

打开 http://127.0.0.1:8765/examples/index.html 。GitHub 页面上的 HTML 文件可下载或通过本地 HTTP 服务打开。

## Mock 素材与重建

人物、背景和图形由 examples/build_mock_examples.py 绘制，示例无音轨。默认 migration-demo 输入是12秒合成动画。真实口播迁移请提供你有权使用的视频。

运行 python examples/build_mock_examples.py 可重建8个示例和默认合成输入。历史认可记录中的媒体摘要仅记录当时验证范围，mock 示例摘要见 examples/catalog.json。

## 安装

```bash
git clone https://github.com/jane00021/motion-replication-pipeline.git
cd motion-replication-pipeline
python -m pip install -r requirements.txt
```

使用 Python 3.10 或更新版本，并安装 ffmpeg、ffprobe，确保两者在 PATH 中。字幕执行器使用 NumPy、Pillow 和 fontTools。浏览器检查、人物抠像和具体案例可能需要额外依赖，按对应脚本实际导入安装。示范模型的许可证见第三方说明。

在 Codex 中，将仓库目录放到用户的 skills 目录，例如 Windows 的 `%USERPROFILE%/.codex/skills/motion-replication-pipeline`。其他支持 Skill 的助手可读取仓库根目录 SKILL.md，将当前目录作为 skill-root，并保留 scripts、references、assets 的结构。

## 让你的 AI 使用这个 Skill

### 直接把仓库链接交给 AI

把下面这段发给具备文件读写、终端和视频处理能力的 AI 助手，将三个路径换成你自己的路径。

```text
请下载 https://github.com/jane00021/motion-replication-pipeline 到 <Skill目录>。
先实际读取其中的 SKILL.md，将该目录作为 skill-root，并按当前任务读取相关 references。
检查 Python、ffmpeg、ffprobe 和视频观察能力，安装所需依赖。
处理参考视频 <视频绝对路径>，在 <新的项目目录> 初始化状态机。
完成拆解并生成可手动校正的中文观察 HTML，停在用户反馈环节，把页面打开方式发给我。
```

这段适合首次使用。AI 需要能访问参考视频和项目目录，并执行 Python 与 ffmpeg。请使用它实际可读的路径。提供网页链接时，先确认 AI 已取得可处理的视频文件。

### 在 Codex 中安装并调用

你可以让 Codex 帮忙安装。把下面这段发给 Codex。

```text
请把 https://github.com/jane00021/motion-replication-pipeline 安装为当前用户的 Skill，
目录名为 motion-replication-pipeline，保留 scripts、references、assets 和 examples。
检查已有安装，已有目录时先核对版本再更新。
```

安装后在新对话中输入下面的请求。在支持 Skill 选择的界面中也可输入 $ 并选择 motion-replication-pipeline。若助手未识别名称，直接提供安装目录下 SKILL.md 的绝对路径。

```text
调用 $motion-replication-pipeline，拆解视频 <参考视频路径>。
项目保存到 <新项目路径>，做到中文手动校正观察 HTML，等我反馈。
```

### 在其他 AI 编程助手中使用

把仓库克隆或解压到 AI 的工作区，确保 SKILL.md 位于该目录第一层。再发送下面的请求。

```text
读取 <Skill目录>/SKILL.md，按该 Skill 执行。
参考视频是 <视频路径>，新项目保存到 <项目路径>。
先检查运行依赖，再初始化项目，按状态机完成拆解观察页，停在用户反馈环节。
```

如果通过附件交付 ZIP，让 AI 先解压并定位 SKILL.md，再按解压目录读取相邻脚本、参考文档和资源。只能阅读对话的助手需要接入能执行本地文件与终端的环境，才能完成渲染和 HTML 交付。

### 反馈后继续复刻

在观察页保存边界、名称和组合关系的校正后，发给同一个 AI。

```text
调用当前 Skill 继续 <项目路径>。
先读取并应用我在观察页保存的校正，完成本批观察与测量验收。
使用 <未剪辑口播路径> 做迁移验证，先复刻前两个完整动效组。
在 HTML 中提供原对标与新口播完整结果，等我审核。
```

前两组效果认可后继续。

```text
前两组通过。按校正后的目录完成其余完整动效组。
共用机制合并为组件，完整配方引用组件。支持 subagent 时按共享 family 分包并行，
主进程统一做编码复核和 HTML 展示，完成后给我审核。
```

全部复刻认可后进行入库。

```text
当前复刻结果已认可，请按 Skill 完成入库、替换验证、编码复审和共享库 HTML。
已有替换结果导入验收。先列来源组到画面组件、字幕组件、完整配方的映射，
分批回归原组合，再继续独立目录复用与封版。
```

### 更换对话后恢复

把原项目目录提供给新的 AI，并发送下面的请求。

```text
读取 <Skill目录>/SKILL.md，接手 <项目路径>。
先读取项目入口、.pipeline/state.json、TASK.md 和最新报告，
运行 status 确认当前节点，继续尚未完成的工作。
```

每次交接保留项目中的状态、源码、输入参数、媒体和审核记录。AI 返回页面后，可按本次任务检查观察卡片、逐组播放结果、校正保存入口以及源码和参数路径。


## 调用提示词

只做拆解和反馈观察页。

```text
调用 $motion-replication-pipeline，处理视频 <参考视频路径>。
初始化新项目，按状态机完成拆解，输出可手动校正的中文观察 HTML，停在用户反馈环节。
```

复刻已有拆解目录。

```text
调用 $motion-replication-pipeline，继续项目 <项目路径>。
按校正后的完整动效组复刻，使用 <未剪辑口播路径> 验证迁移。
先完成前两组并输出原对标与新口播结果，等我审核。
```

整理已认可成果。

```text
调用 $motion-replication-pipeline，把项目 <项目路径> 中已认可的动效组整理进共享库。
先列来源组到画面组件、字幕组件、完整配方的映射，按共享机制入库并回归原组合。
```

## 完整工作流程

| 节点 | 实际工作与产物 |
|---|---|
| 00-intake | 核验参考文件、SHA、画幅、帧率和 PTS，初始化项目 |
| 01-observe | 登记 occurrence，按机制归并 family，建立中文手动反馈观察页 |
| 02-measure | 测量字形、位置、尺寸、遮罩、前后层级、动作和字词时钟 |
| 03-pilot | 先做两个完整代表组，完成同字校准、真实编码、迁移与用户反馈 |
| 04-library | 提炼共享画面和字幕入口，完整组合配方引用组件，重跑原组合 |
| 05-replacement | generate 生成替换结果，import 绑定此前完成的替换证据 |
| 06-encoded-review | 检查实际编码、帧数、时间戳、声画与各阶段动作 |
| 07-html-preview | 提供完整组审核面板或共享库浏览面板，实际检查播放交互 |
| 08-cleanroom | 在独立目录核对依赖并实际调用、编码和复审 |
| 09-release | 固定版本、媒体和源码摘要，保存发布清单与交接记录 |

每个节点依次执行 status、next、实际制作、preflight、accept。04 至 07 可以在同一连续批次内完成，分别保留节点收据。已有替换结果使用 import 绑定证据。用户反馈导致前置结果变化时，通过 reopen 回退并检查受影响内容。

使用 CLI 初始化项目。

```bash
python scripts/motion_pipeline.py init --project "./output/my-project" --name "我的动效项目" --style-id "my-motion" --reference "/absolute/path/reference.mp4"
python scripts/motion_pipeline.py status --project "./output/my-project"
python scripts/motion_pipeline.py next --project "./output/my-project"
```

项目的 TASK.md 给出当前节点。详细要求见 [节点手册](references/stage-playbook.md) 和 [Skill 入口](SKILL.md)。

## 运行一个可编辑字幕示例

在仓库根目录运行，输出目录需要是新的目录。

```bash
python scripts/render_subtitle.py --input examples/inputs/N21.json --output output/N21
```

执行器输出具名角色 PNG、透明 RGBA 序列、叠观察底的 MP4 和 verification.json。修改 JSON 中的文字、字体、位置与时钟后，输出到另一个目录比较结果。N13 的公开可运行示例使用思源字体显示英文，历史校准采用 Georgia Bold，公开版本移除了该字体文件。使用自己拥有授权的英文候选字体时需重新校准字形与排版。

## 组件与组合方式

- 画面库负责构图、注意力、人物与素材、遮罩和空间关系。
- 字幕库负责阅读顺序、角色、重点、字词动作、字体与材质。
- 完整配方引用组件版本，记录共享时钟、层级、接管与退出。
- 搭配规则记录表达任务、空间冲突、前提和已验证范围。

相同机制的文字、颜色、图片、图标和事件变化作为输入或变体。用户以完整组审核表达关系。前两组认可后按共享 family 分配工作包，具备 subagent 能力时并行制作并统一复核。[组件合同](references/library-composition.md) · [入库执行方法](references/library-intake.md)

## 仓库内容与验证范围

```text
SKILL.md          助手执行入口
scripts/          状态机、拆解反馈、字幕与入库执行器
references/       测量、校准、组件、审核与发布合同
assets/           历史认可案例快照、参数与示范输入
examples/         8个展示案例、播放页和可移植字幕参数
licenses/         第三方许可原文
```

两条参考在项目开发中形成 41 条完整配方和共享库验证记录。本仓库保留 Skill 执行器、历史代码和文字记录。历史真人媒体已经移除，公开示例均替换为代码绘制的虚构人物 mock，完整项目的共享库目录与本机 127.0.0.1 服务需要在各自项目中生成。历史快照含当时本地路径，直接重跑请优先使用 examples/inputs 的可移植参数。原字体身份、独立音效听审和任意新人物适配以具体证据为准。

## 许可与反馈

维护者拥有权利的代码、文档和配置按 [PolyForm Noncommercial 1.0.0](LICENSE.md) 发布，使用限制以许可全文为准。第三方字体与模型遵循原许可。视频、人物肖像及参考片段的其他用途需取得相应权利。

欢迎通过 [Issues](https://github.com/jane00021/motion-replication-pipeline/issues) 提交复现步骤、来源帧号、参数和编码对照。请在分享素材前确认你有权公开该内容。
