# 构图与字幕验收

在01拆解时从原对标过程帧分别记录每组的下缘占幅、完整笔画可见性、字幕锚点及转折。分包给出这些字段后才实现。共享 family 不替代每次出现的测量，用户纠正优先写入结构字段和对照标题。

02报告的 `fidelityAudit` 指向 JSON。用 `schema: 2`，`scope` 为本批实际覆盖的 occurrence IDs，`groups` 逐组记录 `id`、`reference`（切片 `path`、`sha256`、局部 `frames` 和 `evidence`）、`presenter.fit`、`subtitle.visibility` 和 `choreography`（按顺序填写 `{frame, action}`）。本批新增范围同步补测，不能用前两组的记录代替后续组。

03报告绑定同一批次编码结果。每组增加 `media`（`path`、`sha256`、`frames`）和逐帧 `samples`，以实际图层算取 `presenterAlphaBox` 和 `occludedGlyphPixels`。满幅组记录 `presenter.settledPhases`，稳定帧用 `settled: true` 和 `phase` 对应阶段；从主体 alpha 统计最底行及上方至少两条扫描线的背景露出像素，记录 `bottomUncoveredPixels`。文字要求完整时，标记 `textVisible` 并测重点字与不允许遮挡区域的交叠，不把背景纹理字当成同一种角色。

将过程帧从真实编码输出解码。`phaseComparison` 保存 `evidence`、`reviewed` 和 `phaseFrames`（每个源转折 `referenceFrame` 对应的 `resultFrame`）。短瞬态检查相邻帧，口播时长变化时按动作阶段对应。只有实际检查过才写 `reviewed: true`。浏览器能播放只能验证交付，不能替代动作对照。
