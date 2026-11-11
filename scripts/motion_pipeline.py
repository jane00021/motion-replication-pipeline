"""Resumable state machine for reference-video motion replication projects."""
from __future__ import annotations

import argparse
import importlib.util
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


STAGES = [
    ("00-intake", "接收与固定范围", ["source-manifest", "scope", "source-probe"]),
    ("01-observe", "完整观察与动效组目录", ["group-catalog", "shot-index", "reference-clip"]),
    ("02-measure", "逐帧和分层测量", ["visual-measurements", "subtitle-measurements", "asset-index"]),
    ("03-pilot", "代表组原素材复现", ["editable-source", "comparison-video", "pilot-review"]),
    ("04-library", "完整动效库", ["library-catalog", "runtime-source", "parameter-contract"]),
    ("05-replacement", "换内容与换字体", ["changed-content", "changed-font", "replacement-matrix"]),
    ("06-encoded-review", "编码后声画复审", ["final-video", "encoded-review", "decode-report"]),
    ("07-html-preview", "HTML 展示面板", ["html-preview", "preview-metadata", "html-review"]),
    ("08-cleanroom", "独立目录复用", ["cleanroom-source", "cleanroom-video", "cleanroom-review"]),
    ("09-release", "封版与交接", ["release-manifest", "release-notes", "handoff"]),
]


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def reconstruction_snapshot(project: Path):
    files = {}
    for name in ("baseline", "variants", "preview"):
        root = project / name
        if root.is_dir():
            for path in root.rglob("*"):
                if path.is_file() and path.suffix != ".log" and "__pycache__" not in path.parts:
                    files[str(path.relative_to(project))] = digest(path)
    return files


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_state(project: Path):
    path = project / ".pipeline" / "state.json"
    if not path.is_file():
        raise SystemExit(f"项目尚未初始化：{project}")
    return read_json(path)


def save_state(project: Path, state):
    state["updated_at"] = now()
    write_json(project / ".pipeline" / "state.json", state)
    update_handoff(project, state)


def current(state):
    return next((stage for stage in state["stages"] if stage["status"] != "passed"), None)


def stage_info(stage_id):
    return next((item for item in STAGES if item[0] == stage_id), None)


def update_handoff(project: Path, state):
    stage = current(state)
    lines = ["# Motion Replication Pipeline Handoff", "", f"项目：{project}", f"更新时间：{now()}", ""]
    if stage:
        info = stage_info(stage["id"])
        lines += [f"当前节点：{stage['id']}", f"节点名称：{info[1]}", "", "恢复动作：读取项目内 SKILL.md，运行 status，再读取 TASK.md。"]
    else:
        lines += ["当前节点：COMPLETE", "全部状态机节点已通过。"]
    if state.get("blocker"):
        lines += ["", f"阻塞项：{state['blocker']}"]
    (project / "HANDOFF.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def init(args):
    project = args.project.resolve()
    if project.exists() and any(project.iterdir()):
        raise SystemExit("init 只接受新的或空的项目目录")
    if not args.style_id or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-" for char in args.style_id):
        raise SystemExit("--style-id 只能使用小写字母、数字和短横线")
    references = []
    for value in args.reference:
        path = Path(value).resolve()
        if not path.is_file():
            raise SystemExit(f"参考视频不存在：{path}")
        references.append({"path": str(path), "sha256": digest(path)})
    project.mkdir(parents=True, exist_ok=True)
    for folder in ("artifacts", "observations", "measurements", "source", "baseline", "library", "variants", "render", "preview", "reviews", "qa", "release", "reports"):
        (project / folder).mkdir()
    workflow = {"schema": 1, "stages": [{"id": ident, "title": title, "roles": roles} for ident, title, roles in STAGES]}
    state = {"schema": 1, "created_at": now(), "updated_at": now(), "stages": [{"id": ident, "status": "pending"} for ident, _, _ in STAGES], "history": [], "blocker": None}
    write_json(project / "project.json", {"schema": 1, "name": args.name, "style_id": args.style_id, "references": references, "layouts": args.layouts, "scope": {"presenter": not args.no_presenter, "editable_text": True, "editable_font": True}, "created_at": now()})
    write_json(project / "workflow-context.json", {"requireFidelityAudit": True, "fidelityAuditSchema": 2, "requireLibraryRegression": True})
    write_json(project / ".pipeline" / "workflow.json", workflow)
    write_json(project / ".pipeline" / "state.json", state)
    local_pipeline = project / ".pipeline" / "motion_pipeline.py"
    shutil.copyfile(Path(__file__).resolve(), local_pipeline)
    local_refs = project / ".pipeline" / "references"
    local_refs.mkdir(parents=True, exist_ok=True)
    for ref_name in ("stage-playbook.md", "visual-motion.md", "subtitle-motion.md", "html-preview.md", "report-schema.md", "decomposition-feedback.md", "replication-calibration.md", "library-composition.md", "approved-case-workflow.md", "fidelity-audit.md", "library-intake.md"):
        shutil.copyfile(Path(__file__).resolve().parents[1] / "references" / ref_name, local_refs / ref_name)
    skill_root=Path(__file__).resolve().parents[1]
    shutil.copytree(skill_root/'assets/decomposition-preview',project/'.pipeline/assets/decomposition-preview')
    shutil.copyfile(skill_root/'scripts/prepare_observation_review.py',project/'.pipeline/prepare_observation_review.py')
    for helper in ('apply_observation_feedback.py','validate_decomposition.py','test_observation_feedback.py','validate_fidelity_contract.py','library_intake.py'):
        shutil.copyfile(skill_root/'scripts'/helper,project/'.pipeline'/helper)
    (project / "SKILL.md").write_text("""# Project Execution Entry\n\n这是一个 motion-replication-pipeline 项目。你接手后必须先读取 `.pipeline/state.json`、`.pipeline/workflow.json`、`.pipeline/references/stage-playbook.md` 和根目录 `TASK.md`。\n\n状态机严格按以下顺序执行：\n`00-intake -> 01-observe -> 02-measure -> 03-pilot -> 04-library -> 05-replacement -> 06-encoded-review -> 07-html-preview -> 08-cleanroom -> 09-release`。\n\n每个节点都必须先运行 `next` 激活，再实际产出文件、填写当前报告，运行 `preflight`，最后运行 `accept`。不得修改 state.json、报告或收据来跳过节点；未完成项必须用 `block` 记录。\n\n03通过后，04-library、05-replacement、06-encoded-review和07-html-preview可以在同一个后处理批次连续执行。四个节点仍分别写报告、运行preflight并accept，不重复制作已完成结果。05支持generate和import两种模式，已有换人物、换内容或换字体结果时绑定证据后直接验收。\n\n项目自带入口：\n```powershell\npython `.pipeline\\motion_pipeline.py` status --project "."\npython `.pipeline\\motion_pipeline.py` next --project "."\npython `.pipeline\\motion_pipeline.py` preflight --project "." --report "reports\\<当前节点>.json"\n```\n\nHTML 和视频节点还必须分别运行 `validate-html` 和 `validate-video`。只写计划、只截帧、只做静态网页或只看落定帧都不能标记完成。\n""", encoding="utf-8")
    with (project/'SKILL.md').open('a',encoding='utf-8') as stream:
        stream.write('\n拆解用户反馈环节：先读 `.pipeline/references/decomposition-feedback.md`。运行 `.pipeline/prepare_observation_review.py --project .` 生成中文手动校正页；测试反馈模式不得自行进入03。\n')
        stream.write('\n进入03复刻/返工先读 `.pipeline/references/replication-calibration.md`；同字校准、语义角色、可见阴影、分层时钟、编码同钟对照与干净输入迁移分别验证。默认复审每组仅展示对标＋应用结果。\n')
        stream.write('\n后处理批次先读 library-intake.md：04到07可连续执行，节点收据分别保留；05已有替换结果使用import模式。\n')
        stream.write('\n复用架构先读 `.pipeline/references/library-composition.md`：两类库＋引用式完整组合配方＋搭配规则。完整组是学习/验证单位，配方不复制组件实现。\n')
        stream.write('\n认可成果入库：读 .pipeline/references/library-intake.md，使用 .pipeline/library_intake.py 生成映射并重跑原配方；04的 preflight 将验证回归收据。\n')
    write_json(project / "source-manifest.json", {"references": references})
    save_state(project, state)
    print(json.dumps({"project": str(project), "next": STAGES[0][0], "handoff": str(project / "HANDOFF.md")}, ensure_ascii=False, indent=2))


def status(args):
    project = args.project.resolve()
    state = load_state(project)
    print(json.dumps({"current": current(state), "stages": state["stages"], "blocker": state.get("blocker")}, ensure_ascii=False, indent=2))


def next_stage(args):
    project = args.project.resolve()
    state = load_state(project)
    stage = current(state)
    if stage is None:
        raise SystemExit("所有节点已经通过")
    context_path=project/'workflow-context.json'
    context=read_json(context_path) if context_path.exists() else {}
    if context.get('mode')=='skill-test-feedback' and stage['id'] not in {'00-intake','01-observe','02-measure'}:
        raise SystemExit('当前为skill测试反馈模式；保持拆解反馈范围，不激活03或后续复刻节点。')
    if stage["status"] == "active":
        raise SystemExit(f"当前节点已经 active，请先读取 TASK.md：{stage['id']}")
    stage["status"] = "active"
    stage["started_at"] = now()
    ident, title, roles = stage_info(stage["id"])
    report_path = project / "reports" / f"{ident}.json"
    write_json(report_path, {"stage": ident, "unresolved": ["待实际执行；不能直接接受此模板"], "artifacts": [{"role": role, "path": ""} for role in roles], "checks": [], "notes": "", "applied_lessons": []})
    (project / "TASK.md").write_text(f"# {ident} {title}\n\n实际执行本节点，完成后编辑 `reports/{report_path.name}`，填写真实产物、检查方法和证据。\n\n必需角色：{', '.join(roles)}\n\n未完成前不要 accept。\n", encoding="utf-8")
    state["history"].append({"at": now(), "event": "next", "stage": ident, "report": str(report_path)})
    save_state(project, state)
    print(json.dumps({"stage": ident, "title": title, "report": str(report_path), "roles": roles}, ensure_ascii=False, indent=2))


def report_path_for(project: Path, value: str) -> Path:
    path = Path(value)
    return (project / path).resolve() if not path.is_absolute() else path.resolve()


def check_report(project: Path, state, report_path: Path):
    stage = current(state)
    if stage is None:
        raise SystemExit("没有待接受节点")
    if stage["status"] != "active":
        raise SystemExit(f"请先运行 next 激活当前节点：{stage['id']}")
    context_path=project/'workflow-context.json'
    context=read_json(context_path) if context_path.exists() else {}
    if context.get('mode')=='skill-test-feedback':
        if stage['id'] not in {'00-intake','01-observe','02-measure'}:
            raise SystemExit('当前为skill测试反馈模式，只允许拆解，不允许验收复刻节点。')
        if stage['id'] in {'01-observe','02-measure'} and context.get('feedbackRequired'):
            raw=project/'observations/manual-review/adjustments.json'
            receipt=project/'observations/manual-review/feedback-applied.json'
            if not raw.exists() or not receipt.exists():
                raise SystemExit('缺少真实用户标注或反馈应用记录。')
            data=read_json(receipt)
            if data.get('sourceSha256')!=digest(raw) or data.get('status') not in {'applied-not-stage-approved','applied'}:
                raise SystemExit('用户反馈尚未应用，或应用记录对应旧版本；先重新读取真实标注。')
    if stage["id"] in {"00-intake", "01-observe", "02-measure"}:
        existing = reconstruction_snapshot(project)
        preserved = state.get("preserved_reconstruction", {})
        changed = [name for name, sha in existing.items() if preserved.get(name) != sha]
        removed = [name for name in preserved if name not in existing]
        if changed or removed:
            raise SystemExit("拆解阶段出现新增或变更的复刻产物：" + "; ".join((changed + removed)[:5]))
    report = read_json(report_path)
    if report.get("stage") != stage["id"]:
        raise SystemExit(f"当前节点是 {stage['id']}，报告却是 {report.get('stage')}")
    roles = stage_info(stage["id"])[2]
    actual_roles = {item.get("role") for item in report.get("artifacts", [])}
    missing = [role for role in roles if role not in actual_roles]
    if missing:
        raise SystemExit("缺少产物角色：" + ", ".join(missing))
    if report.get("unresolved") != []:
        raise SystemExit("仍有 unresolved findings")
    if stage['id'] in {'02-measure','03-pilot'} and report.get('fidelityAudit'):
        checker = Path(__file__).resolve().with_name('validate_fidelity_contract.py')
        audit_path = project / report['fidelityAudit']
        minimum_schema = context.get('fidelityAuditSchema', 1)
        if audit_path.is_file() and read_json(audit_path).get('schema', 1) < minimum_schema:
            raise SystemExit(f'构图与字幕证据须使用 schema {minimum_schema} 或更新版本。')
        spec = importlib.util.spec_from_file_location('fidelity_checker', checker)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        errors = module.validate(project, audit_path, stage['id'] == '03-pilot')
        if errors:
            raise SystemExit('构图与字幕保真检查失败：' + '; '.join(errors))
    elif stage['id'] in {'02-measure','03-pilot'} and context.get('requireFidelityAudit'):
        raise SystemExit('缺少 fidelityAudit。需绑定人物占幅、字幕可见性及阶段编舞证据。')
    if stage['id'] in {'01-observe','02-measure'}:
        checker=Path(__file__).resolve().with_name('validate_decomposition.py')
        if checker.exists():
            spec=importlib.util.spec_from_file_location('decomposition_checker',checker)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            errors=module.validate(project)
            if errors:
                raise SystemExit('拆解结构不一致：'+'; '.join(errors))
    if stage['id'] == '04-library' and (context.get('requireLibraryRegression') or report.get('libraryRegression')):
        try:
            from library_intake import local, verify_receipts
            regression = report['libraryRegression']
            catalog_artifact = next(item for item in report['artifacts'] if item['role'] == 'library-catalog')
            verify_receipts(project, local(project, regression['plan']), regression['receipts'], catalog_artifact['path'])
        except (ImportError, ValueError, TypeError, IndexError, KeyError, OSError) as exc:
            raise SystemExit(f'04 原配方回归未通过：{exc}') from exc
    checks = report.get("checks", [])
    if not checks or not all(item.get("passed") is True and item.get("finding") and item.get("evidence") for item in checks):
        raise SystemExit("每项检查必须有 passed=true、finding 和 evidence")
    for item in report["artifacts"]:
        path_value = item.get("path")
        if not path_value:
            raise SystemExit(f"产物路径为空：{item.get('role')}")
        path = Path(path_value)
        if not path.is_absolute():
            path = project / path
        if not path.exists():
            raise SystemExit(f"产物不存在：{path.resolve()}")
    return stage, report


def preflight(args):
    project = args.project.resolve()
    state = load_state(project)
    stage = current(state)
    if stage is None:
        raise SystemExit("所有节点已经通过")
    report_path = report_path_for(project, args.report)
    check_report(project, state, report_path)
    print(json.dumps({"stage": stage["id"], "report": str(report_path), "preflight": True}, ensure_ascii=False, indent=2))


def accept(args):
    project = args.project.resolve()
    state = load_state(project)
    report_path = report_path_for(project, args.report)
    stage, report = check_report(project, state, report_path)
    stage["status"] = "passed"
    stage["accepted_at"] = now()
    stage["report"] = str(report_path.relative_to(project)) if report_path.is_relative_to(project) else str(report_path)
    state["blocker"] = None
    state["history"].append({"at": now(), "event": "accepted", "stage": stage["id"], "report": stage["report"]})
    save_state(project, state)
    print(json.dumps({"accepted": stage["id"], "next": current(state)["id"] if current(state) else "COMPLETE"}, ensure_ascii=False, indent=2))


def reopen(args):
    project = args.project.resolve()
    state = load_state(project)
    ids = [item[0] for item in STAGES]
    if args.stage not in ids:
        raise SystemExit(f"未知节点：{args.stage}")
    start = ids.index(args.stage)
    has_reconstruction = any(item.get('event') == 'next' and item.get('stage') == '03-pilot' for item in state['history'])
    if start <= ids.index('02-measure') and has_reconstruction:
        state['preserved_reconstruction'] = reconstruction_snapshot(project)
    for stage in state["stages"][start:]:
        stage["status"] = "pending"
        stage.pop("accepted_at", None)
        stage.pop("report", None)
    state["blocker"] = None
    state["history"].append({"at": now(), "event": "reopen", "stage": args.stage, "reason": args.reason})
    save_state(project, state)
    print(json.dumps({"reopened": args.stage, "reason": args.reason}, ensure_ascii=False, indent=2))


def block(args):
    project = args.project.resolve()
    state = load_state(project)
    state["blocker"] = args.reason
    state["history"].append({"at": now(), "event": "block", "reason": args.reason})
    save_state(project, state)
    print(json.dumps({"blocked": current(state)["id"] if current(state) else "COMPLETE", "reason": args.reason}, ensure_ascii=False, indent=2))


def probe(args):
    project = args.project.resolve()
    load_state(project)
    config = read_json(project / "project.json")
    output = {"created_at": now(), "files": []}
    for item in config["references"]:
        path = Path(item["path"])
        command = ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
        except FileNotFoundError:
            raise SystemExit("ffprobe 是 00-intake 必需工具")
        except subprocess.CalledProcessError as exc:
            raise SystemExit(exc.stderr or "ffprobe 失败")
        output["files"].append({"path": str(path), "sha256": digest(path), "probe": json.loads(result.stdout)})
    target = project / "artifacts" / "00-intake" / "source-probe.json"
    write_json(target, output)
    print(json.dumps({"source_probe": str(target), "files": len(output["files"])}, ensure_ascii=False, indent=2))


def validate_html(args):
    project = args.project.resolve()
    load_state(project)
    html = Path(args.html)
    if not html.is_absolute():
        html = project / html
    html = html.resolve()
    if not html.is_file():
        raise SystemExit(f"HTML 不存在：{html}")
    text = html.read_text(encoding="utf-8", errors="replace").lower()
    for marker in ("<html", "<script", "<video"):
        if marker not in text:
            raise SystemExit(f"HTML 缺少标记：{marker}")
    metadata = html.parent / "metadata.json"
    if not metadata.is_file():
        raise SystemExit(f"HTML 旁边缺少 metadata.json：{metadata}")
    print(json.dumps({"html": str(html), "metadata": str(metadata), "valid": True}, ensure_ascii=False, indent=2))


def validate_video(args):
    project = args.project.resolve()
    load_state(project)
    video = Path(args.video)
    if not video.is_absolute():
        video = project / video
    video = video.resolve()
    if not video.is_file():
        raise SystemExit(f"视频不存在：{video}")
    command = ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(video)]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except FileNotFoundError:
        raise SystemExit("ffprobe 是视频验收必需工具")
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.stderr or "视频解码探测失败")
    data = json.loads(result.stdout)
    if not any(stream.get("codec_type") == "video" for stream in data.get("streams", [])):
        raise SystemExit("视频流不存在")
    print(json.dumps({"video": str(video), "streams": data.get("streams", []), "valid": True}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init"); p.add_argument("--project", type=Path, required=True); p.add_argument("--name", required=True); p.add_argument("--style-id", required=True); p.add_argument("--reference", action="append", required=True); p.add_argument("--layouts", nargs="+", default=["landscape", "portrait"]); p.add_argument("--no-presenter", action="store_true"); p.set_defaults(func=init)
    for name, function in (("status", status), ("next", next_stage), ("probe", probe)):
        p = sub.add_parser(name); p.add_argument("--project", type=Path, required=True); p.set_defaults(func=function)
    p = sub.add_parser("preflight"); p.add_argument("--project", type=Path, required=True); p.add_argument("--report", required=True); p.set_defaults(func=preflight)
    p = sub.add_parser("accept"); p.add_argument("--project", type=Path, required=True); p.add_argument("--report", required=True); p.set_defaults(func=accept)
    p = sub.add_parser("reopen"); p.add_argument("--project", type=Path, required=True); p.add_argument("--stage", required=True); p.add_argument("--reason", required=True); p.set_defaults(func=reopen)
    p = sub.add_parser("block"); p.add_argument("--project", type=Path, required=True); p.add_argument("--reason", required=True); p.set_defaults(func=block)
    p = sub.add_parser("validate-html"); p.add_argument("--project", type=Path, required=True); p.add_argument("--html", required=True); p.set_defaults(func=validate_html)
    p = sub.add_parser("validate-video"); p.add_argument("--project", type=Path, required=True); p.add_argument("--video", required=True); p.set_defaults(func=validate_video)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
