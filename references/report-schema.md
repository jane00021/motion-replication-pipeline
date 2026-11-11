# 节点报告字段

每个 `reports/<stage>.json` 至少包含：

```json
{
  "stage": "03-pilot",
  "unresolved": [],
  "artifacts": [
    {"role": "editable-source", "path": "source/"},
    {"role": "comparison-video", "path": "render/pilot/compare.mp4"}
  ],
  "checks": [
    {
      "id": "full-motion",
      "passed": true,
      "method": "encoded-playback",
      "finding": "实际连续观看了入场、中段停留、退场和下一镜交接。",
      "evidence": ["render/pilot/compare.mp4", "reviews/pilot-review.json"]
    }
  ],
  "notes": "",
  "applied_lessons": []
}
```

`passed` 不能只写成布尔值；每项检查必须写实际发现和证据路径。`unresolved` 不为空时不能接受节点。

04 报告的 libraryRegression 填入 plan（入库计划路径）与 receipts（回归收据路径数组）；由 preflight 重验覆盖、绑定和结果文件。独立组件调用、透明层、真实播放、原组效果检查和剩余限制另列 checks/unresolved。见 [认可成果入库执行](library-intake.md)。

05 报告的 \`mode\` 为 \`generate\` 或 \`import\`。import 报告的每个替换条目都要填写 \`media\`、\`mediaSha256\`、\`input\`、\`inputSha256\`、\`source\`、\`sourceSha256\`、\`fonts\`、\`checks\` 和 \`scope\`。import 只验收既有结果，不生成第二份替换视频。

观察和库目录还必须区分：

```json
{
  "families": [
    {
      "id": "F01",
      "mechanism_signature": ["circle-presenter", "title-reveal", "portrait-broll"],
      "occurrences": ["O01", "O04"],
      "variants": ["different-text", "different-image"]
    }
  ],
  "occurrences": [
    {"id": "O01", "family_id": "F01", "source": {"start": 6.8, "end": 12.6}}
  ]
}
```

同一机制只换文字、颜色、图片或事件时点，必须合并到同一个 `family_id`；只有动作、层级、几何或表达职责不同，才允许新增 family。
