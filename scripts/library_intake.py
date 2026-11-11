"""Audit a library intake plan, render existing recipes, and verify technical regression."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def local(project, value):
    p = (project / value).resolve()
    require(p.is_relative_to(project), f"入库文件须位于项目内：{value}")
    return p


def ident(value):
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", value), f"无效 ID：{value}")
    return value


def index(rows):
    result = {ident(row["id"]): row for row in rows}
    require(len(result) == len(rows), "存在重复 ID")
    return result


def tolerance(row):
    limits = row.get("tolerance", {})
    keys = {"meanRgb", "worstFrameRgb", "ptsMs"}
    require(not (limits.keys() - keys - {"reason"}), "未知回归容差")
    values = {k: limits.get(k, .05 if k == "ptsMs" else 0) for k in keys}
    require(all(isinstance(n, (int, float)) and not isinstance(n, bool)
                and math.isfinite(n) and n >= 0 for n in values.values()), "回归容差必须是有限非负数")
    require(values["meanRgb"] <= values["worstFrameRgb"] <= 255, "像素容差区间无效")
    require(not any(k in limits for k in keys) or limits.get("reason", "").strip(),
            "自定义容差必须记录事先确定的依据")
    return values


def audit(project, plan_path):
    plan = read(plan_path)
    require(plan["schema"] == 1 and plan["scope"].strip(), "缺少入库范围或 schema 不受支持")
    components, rows = index(plan["components"]), index(plan["recipes"])
    require(rows and components, "入库范围不能为空")
    hashes, origins, signatures, refs, used = {}, set(), set(), {}, set()

    def bind(name, expected=None):
        p = local(project, name)
        key = p.relative_to(project).as_posix()
        if key not in hashes:
            hashes[key] = sha(p)
        require(expected is None or hashes[key] == expected, f"文件与绑定摘要不一致：{name}")
        return p

    for cid, comp in components.items():
        for field in ("name", "version", "signature", "reason", "entrypoint"):
            require(comp[field].strip(), f"{cid} 缺少 {field}")
        key = (comp["kind"], " ".join(comp["signature"].casefold().split()))
        require(key[0] in {"visual", "subtitle"}, f"{cid} 机制类型无效")
        require(key not in signatures, f"{cid} 重复机制签名，先归并")
        signatures.add(key)
        bind(comp["contract"])
        require(comp["files"], f"{cid} 未绑定实际组件文件")
        for name in comp["files"]:
            bind(name)

    for rid, row in rows.items():
        origin = row["origin"]
        require(origin.strip() and origin not in origins, f"完整组来源为空或重复：{origin}")
        origins.add(origin)
        approval = row["approval"]
        entry = read(bind(approval["record"], approval["recordSha256"]))
        for part in approval["row"]:
            entry = entry[part]
        require(isinstance(entry, dict) and entry.get(approval["mediaHashKey"]) == approval["mediaSha256"],
                f"{rid} 的认可记录未绑定指定媒体")
        occurrence = entry.get(approval.get("occurrenceKey", "occurrence"))
        if occurrence is not None:
            require(str(occurrence) == origin.rsplit(":", 1)[-1], f"{rid} 的认可条目对应不同来源组")
        bind(approval["media"], approval["mediaSha256"])
        for name, digest in approval["files"].items():
            require(digest in entry.values(), f"{rid} 原输入/配方摘要未绑定至该认可条目：{name}")
            bind(name, digest)
        require(approval["files"], f"{rid} 缺少认可的输入或源码绑定")
        recipe = read(bind(row["recipe"]))
        require(recipe["id"] == rid and recipe["newCombination"] is False, f"{rid} 不是本轮已有配方")
        require(recipe["purpose"] and recipe["clock"] and recipe["zOrder"] and recipe["handoff"]
                and recipe["exitPolicy"], f"{rid} 缺少表达、共享时钟、层级、接管或退出")
        ids = [ref["id"] for ref in recipe["componentRefs"]]
        require(ids and len(ids) == len(set(ids)), f"{rid} 无组件或组件重复")
        for ref in recipe["componentRefs"]:
            require(ref["version"] == components[ref["id"]]["version"], f"{rid} 组件版本错配")
        refs[rid] = ids
        used.update(ids)
        require(row["files"], f"{rid} 未绑定重跑输入及运行器")
        for name in row["files"]:
            bind(name)
        argv = row["argv"]
        require(isinstance(argv, list) and argv and all(isinstance(a, str) for a in argv)
                and "{recipe}" in argv and "{output}" in argv, f"{rid} 须提供真实配方调用和独立输出路径")
        dest = Path(row["result"])
        require(not dest.is_absolute() and not dest.drive and ".." not in dest.parts and dest.name.endswith(".mp4"),
                f"{rid} 输出须为独立输出目录内的 MP4")
        tolerance(row)
    require(used == set(components), "计划中有未被原配方引用的组件")
    return plan, components, rows, refs, hashes


def emit_mapping(dest, plan, components, rows, refs):
    def cell(value):
        return str(value).replace("|", r"\|").replace("\n", " ")

    dest.mkdir(parents=True, exist_ok=True)
    lines = ["# 已认可完整组 → 共享组件 → 原组合", "", plan["scope"], "",
             "| 来源完整组 | 画面组件 | 字幕组件 | 原配方 |",
             "|---|---|---|---|"]
    for rid, row in rows.items():
        by_kind = [", ".join(cid for cid in refs[rid] if components[cid]["kind"] == kind) or "—"
                   for kind in ("visual", "subtitle")]
        lines.append("| " + " | ".join(map(cell, [row["origin"], *by_kind, rid])) + " |")
    lines.extend(["", "## 合并和保留理由", "", "| 机制 | 来源 | 理由 |", "|---|---|---|"])
    for cid, comp in components.items():
        sources = ", ".join(rows[rid]["origin"] for rid in refs if cid in refs[rid])
        lines.append("| " + " | ".join(map(cell, [f'{cid} {comp["name"]}', sources, comp["reason"]])) + " |")
    (dest / "merged-mapping.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write(dest / "merged-mapping.json", {
        "scope": plan["scope"], "components": list(components.values()),
        "recipes": [{"id": rid, "origin": row["origin"], "componentRefs": refs[rid]} for rid, row in rows.items()],
    })


def probe(path):
    def get(*args):
        return json.loads(subprocess.check_output(["ffprobe", "-v", "error", *args, "-of", "json", str(path)]))

    video = get("-select_streams", "v:0", "-show_streams", "-show_frames",
                "-show_entries", "stream=width,height:frame=best_effort_timestamp_time,pkt_duration_time,duration_time")
    v = video["streams"][0]
    times = [float(f["best_effort_timestamp_time"]) for f in video["frames"]]
    last = video["frames"][-1]
    duration = last.get("duration_time") or last.get("pkt_duration_time")
    audio = get("-select_streams", "a", "-show_streams",
                "-show_entries", "stream=start_time,duration,sample_rate,channels").get("streams", [])
    return (v["width"], v["height"]), times, float(duration) if duration else None, audio


def compare(old, new, limits):
    import numpy as np

    shape, a, ad, audio_a = probe(old)
    other_shape, b, bd, audio_b = probe(new)
    same_count = len(a) == len(b)
    pts = max((abs(x - y) * 1000 for x, y in zip(a, b)), default=None)
    end_delta = abs(ad - bd) * 1000 if ad is not None and bd is not None else None
    audio_count = len(audio_a) == len(audio_b)
    result = {"originalSize": shape, "newSize": other_shape, "originalFrames": len(a),
              "newFrames": len(b), "maxPtsErrorMs": pts, "lastFrameDurationErrorMs": end_delta,
              "audioStreamsMatchInCount": audio_count, "originalAudio": audio_a, "newAudio": audio_b,
              "audioListened": False, "continuousVisualReview": False, "fullVideoDecode": False}
    if shape != other_shape or not same_count or not a:
        return result | {"technicalPassed": False}

    def decode(path, log):
        return subprocess.Popen(["ffmpeg", "-v", "error", "-xerror", "-threads", "1",
                                 "-noautorotate", "-i", str(path), "-map", "0:v:0",
                                 "-fps_mode", "passthrough", "-c:v", "rawvideo", "-threads:v", "1",
                                 "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1"],
                                stdout=subprocess.PIPE, stderr=log)

    size = shape[0] * shape[1] * 3
    errors, processes = [], []
    with tempfile.TemporaryFile() as log:
        try:
            processes.append(decode(old, log))
            processes.append(decode(new, log))
            for n in range(len(a)):
                x, y = [p.stdout.read(size) for p in processes]
                require(len(x) == size and len(y) == size, f"解码帧数不足或截断，帧 {n}")
                x = np.frombuffer(x, dtype=np.uint8)
                y = np.frombuffer(y, dtype=np.uint8)
                errors.append(float(np.abs(x.astype(np.int16) - y).mean()))
            require(all(p.stdout.read(1) == b"" for p in processes), "解码帧数多于时间戳")
            statuses = [p.wait() for p in processes]
            if any(statuses):
                log.seek(0)
                raise ValueError("解码失败：" + log.read().decode(errors="replace")[-2000:])
        finally:
            for p in processes:
                p.stdout.close()
                if p.poll() is None:
                    p.kill()
                    p.wait()
    mean, worst = sum(errors) / len(errors), max(errors)
    return result | {"meanRgbError": mean, "worstFrameRgbError": worst, "worstFrame": errors.index(worst),
                     "fullVideoDecode": True, "decodedVideoExact": worst == 0,
                     "technicalPassed": (audio_count and pts <= limits["ptsMs"]
                                         and end_delta is not None and end_delta <= limits["ptsMs"]
                                         and mean <= limits["meanRgb"] and worst <= limits["worstFrameRgb"])}


def regress(project, plan_path, dest, selected, rows, hashes):
    records = {}
    for rid in selected:
        row = rows[rid]
        approval = row["approval"]
        work = dest / rid
        log = dest / (rid + ".log")
        argv = {"{python}": sys.executable, "{recipe}": str(local(project, row["recipe"])), "{output}": str(work)}
        result = (work / row["result"]).resolve()
        require(result.is_relative_to(work), "输出越过独立运行目录")
        rec = {"approvedSha256": approval["mediaSha256"], "result": result.relative_to(project).as_posix(),
               "tolerance": tolerance(row), "userApprovedRerun": False}
        try:
            with log.open("wb") as f:
                subprocess.run([argv.get(a, a) for a in row["argv"]], cwd=project,
                               stdout=f, stderr=subprocess.STDOUT, check=True)
            require(result.resolve() == result and result.is_file(), "运行器没有在指定位置生成独立结果")
            rec.update(compare(local(project, approval["media"]), result, rec["tolerance"]))
            rec["resultSha256"] = sha(result)
        except (ValueError, OSError, IndexError, KeyError, subprocess.SubprocessError) as exc:
            rec.update(technicalPassed=False, failure=str(exc))
        records[rid] = rec
        print(rid, "通过技术回归" if rec["technicalPassed"] else "技术回归未通过", flush=True)
    unchanged = all((project / name).is_file() and sha(project / name) == digest for name, digest in hashes.items())
    plan_unchanged = sha(plan_path) == hashes[plan_path.relative_to(project).as_posix()]
    receipt = {"schema": 1, "plan": plan_path.relative_to(project).as_posix(),
               "bindings": hashes, "results": records,
               "technicalPassed": unchanged and plan_unchanged and all(r["technicalPassed"] for r in records.values()),
               "bindingsUnchanged": unchanged and plan_unchanged, "stageAccepted": False}
    write(dest / "regression.json", receipt)
    return receipt["technicalPassed"]


def verify_receipts(project, plan_path, receipts, catalog_path=None):
    plan, components, rows, refs, hashes = audit(project, plan_path)
    if catalog_path is not None:
        catalog = read(local(project, catalog_path))
        if catalog.get("activeCatalog"):
            catalog = read(local(project, catalog["activeCatalog"]))
        listed = index(catalog["components"])
        require(listed.keys() == components.keys(), "活动库组件范围与回归计划不同")
        for cid, comp in components.items():
            require(all(comp[key] == listed[cid][key] for key in ("kind", "version", "entrypoint", "contract")),
                    f"活动库组件版本或入口与回归计划不同：{cid}")
        actual = [local(project, name) for name in catalog["recipes"]]
        expected = [local(project, row["recipe"]) for row in rows.values()]
        require(len(actual) == len(expected) and set(actual) == set(expected), "活动库配方范围与回归计划不同")
    hashes[plan_path.relative_to(project).as_posix()] = sha(plan_path)
    covered = set()
    for path in receipts:
        receipt = read(local(project, path))
        require(receipt["schema"] == 1 and receipt["technicalPassed"] is True
                and receipt["bindingsUnchanged"] is True and receipt["bindings"] == hashes
                and receipt["plan"] == plan_path.relative_to(project).as_posix(), f"回归收据失败或过期：{path}")
        for rid, result in receipt["results"].items():
            require(rid in rows and result["technicalPassed"] is True and result["fullVideoDecode"] is True
                    and result["approvedSha256"] == rows[rid]["approval"]["mediaSha256"]
                    and result["tolerance"] == tolerance(rows[rid])
                    and sha(local(project, result["result"])) == result["resultSha256"], f"回归结果无效或过期：{rid}")
            covered.add(rid)
    require(covered == set(rows), "缺少原配方回归：" + ", ".join(sorted(set(rows) - covered)))
    return covered


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["map", "regress", "verify"])
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--output", help="全新的项目内输出目录")
    parser.add_argument("--component", action="append", default=[], help="仅重跑引用所选组件的全部原配方；可重复")
    parser.add_argument("--catalog", help="verify 可同时检查活动目录范围")
    parser.add_argument("--receipt", action="append", default=[], help="verify 要检查的回归收据；可重复")
    args = parser.parse_args()
    project = args.project.resolve()
    plan_path = local(project, args.plan)
    if args.action == "verify":
        print(f"回归覆盖 {len(verify_receipts(project, plan_path, args.receipt, args.catalog))} 个原配方")
        return
    plan, comps, rows, refs, hashes = audit(project, plan_path)
    hashes[plan_path.relative_to(project).as_posix()] = sha(plan_path)
    require(args.output, "map/regress 需要 --output")
    dest = local(project, args.output)
    require(not dest.exists(), "输出目录已存在")
    require(set(args.component) <= comps.keys(), "分批参数含未知组件")
    emit_mapping(dest, plan, comps, rows, refs)
    if args.action == "regress":
        selected = [rid for rid in rows if not args.component or set(refs[rid]).intersection(args.component)]
        if not regress(project, plan_path, dest, selected, rows, hashes):
            raise SystemExit(1)
    print(dest)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, IndexError, OSError, subprocess.SubprocessError) as exc:
        raise SystemExit(f"入库检查失败：{exc}") from exc

