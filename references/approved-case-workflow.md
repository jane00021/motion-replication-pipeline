公开发布说明：当前示范输入和展示视频均为代码绘制的虚构人物 mock。历史真人视频、截图及原声媒体已经移除。历史路径和摘要仅用于追溯记录。可运行参数见 examples/inputs，播放页见 examples/index.html。真实迁移请提供有权使用的口播素材。

# 认可版本归档与下一轮复刻审核

## 当前保存的范围

`assets/approved-case-wechat/case.json` 指向这次用户认可的完整案例快照：视频、对标切片、源码、参数、组合层序、依赖摘要与已披露差异。最终目录17个完整occurrence保留合并前19个成员映射；不要为凑19制造新family。`approval.json`以真实视频SHA绑定人类认可，并逐条区分当前源码摘要和历史配方声明。历史技术绑定过期不得改成验收通过。

这些是案例源码与组合关系，不是扩大后的正式组件库，也未认证脱离环境独立运行。字体仍有外部路径；模型/字体身份、听审及任意新输入保真均不由视觉认可自动推导。先阅读案例manifest与bindingIssues，再借鉴实现。

## 通用方法与案例参数

通用方法见 `replication-calibration.md` 和 `library-composition.md`：完整组为效果审核单位；画面/字幕独立入口；配方引用family、共享时钟、显式zOrder；语义重点重新标注；同字校准、真实字面定位、阴影、透明边界及编码过程对照；图片/视频优先，SVG补充。

本片的坐标、工作分辨率、字体候选、文字、素材、抠像种子和事件帧仅属于案例参数。新参考必须逐帧重测，不能复制后宣称同等效果。保留当前接口即可：visual `render(id, rawFrame, localFrame, input, disabled)`，subtitle `render_subtitle(id, localFrame, input, disabled)`（原模块render等价）；返回独立RGBA slots。recipe记录component refs/source SHA、input、layerOrder、supportBindings；普通底片不新建画面family。已批准视频不覆盖。

## 默认迁移验证视频

`assets/migration-demo/talking-head-raw.mp4` 是代码绘制的12秒无声合成输入；manifest绑定真实SHA。没有指定其他迁移输入时可用它做默认案例；用户给新口播时优先新输入。每次按语义重选片段/重点词/时间，不把示范台词当通用文案，不把示范视频当参考动作证据。

## 新参考进入03后的审核节奏

先按已通过的拆解目录的来源顺序复刻前两个完整occurrence，各自输出原对标和新口播完整结果两条播放器。同字和过程校准留工程，实际编码后自检；先停止扩展，等待用户明确效果认可。将认可意见与这两条媒体、源码、参数摘要绑定。

通过后按共用机制分工作包：同一family由同一owner维护，其occurrence/variant引用同一实现。主进程先固定组件接口和共用文件归属，再调用多个subagent，每个负责一个工作包的完整组，不把画面和字幕拆给互不协调的agent。任务卡必须写独占路径、所含occurrences/families、素材/语义、检查与返回manifest；主进程统一整合与浏览器复核。共用family跨包时先调整分包，避免重复实现或并发改同文件。无subagent工具时如实顺序执行，不假称并行。

这是一条新参考项目的03内用户审核流程。用户明确认可并且报告、回归和保真证据齐全后，主进程可以进入04到07后处理批次。已有认可成果进入共享库时，按library-intake执行证据导入。用户收缩范围时立即按最新范围处理。

## 实际归档命令

已有总览元数据 `render/pilot/all-groups-metadata.json` 与 `observations/group-catalog.json` 的认可案例可执行：

```powershell
python "<skill-root>/scripts/archive_approved_case.py" --project "<project>" --output "<全新归档目录>" --quote "<用户实际认可原话>"
```

命令不覆盖旧快照，验证媒体SHA、复制源码/输入/素材/片段、列出外部依赖与过期技术绑定；不修改状态机。它不是新参考的自动复刻器。现有组件真实入口保存在案例快照中；本轮不新增或发布泛化组件库。

## 新增六组字幕认可快照与执行入口

`assets/approved-subtitle-rework.json` 定位N07/N13/N17/N21/N22/N24认可记录、实际源码/参数/媒体/过程证据与独立字体。通用执行方法及真实调用命令见 [subtitle-execution.md](subtitle-execution.md)。旧全组归档脚本仍属于旧案例合同，不用其历史编号解释新项目。六组认可不自动授予其他18组或03节点通过。
