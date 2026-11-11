# 画面动效拆解合同

每个画面动效组必须回答四个问题：

1. 观众此刻要理解什么？
2. 哪个对象接管人物的表达？
3. 对象如何进入、推进、停留、退出？
4. 这个动作由什么声音或下一镜承接？

## 分层记录

```json
{
  "id": "VIS-001",
  "source": {"file": "reference.mp4", "start": 12.4, "end": 16.8},
  "purpose": "证据展示",
  "dialogue_relation": "人物先提出判断，素材随后给出证据",
  "layers": [
    {"role": "presenter", "entry": 0.0, "hold": 1.1, "exit": 0.3},
    {"role": "broll", "mask": "rounded-rect", "motion": "slide-up-and-scale"},
    {"role": "caption", "role_type": "supporting", "timing": "word-clock"}
  ],
  "handoff": {"from": "presenter", "to": "broll", "return": true},
  "sound_anchor": [{"event": "broll-reveal", "kind": "fx", "source": "local-library"}],
  "editable": ["presenter", "broll", "caption", "event_time"]
}
```

不得把 `motion` 只写成“淡入”。必须描述对象、方向、空间关系和时序。若参考是复杂透视、撕纸、抠像、镜头运动或材质变化，必须实现相应机制或明确记录尚未复现，不能降级成普通卡片后标记通过。

## 画面组验收

- 拆解时逐个 occurrence、逐个背景段记录人物底边和左右占幅，检查首帧、稳定帧、换背景前后及末帧。共用抠像 family 只说明机制相同，不能继承人物框、缩放或对齐方式。
- 明确记录 `bottom-full-width`、`bounded` 或 `not-applicable`。满幅用人物自身的实质 alpha 测底部至少三条扫描线及左右边缘，含最底一行，不能只看 alpha 外接框、白描边或单张终态。每段稳定期间都要验证，发现背景从下缘露出先改裁切、等比放大和底部锚点。
- 人物和素材的前后层级正确。
- 对象进入前有必要的铺垫，答案没有提前露出。
- 过程动作和停留时间可看懂，不只看最终静帧。
- 退场后给下一镜足够交接空间。
- 换人物、换图片和换事件时点不会携带旧蒙版或旧内容。
