"""Validate decomposition structure, component modes and applied feedback provenance."""
import argparse,hashlib,json
from pathlib import Path

def validate(project):
    catalog=json.loads((project/'observations/group-catalog.json').read_text('utf-8'))
    errors=[];occ=catalog.get('occurrences',[]);families=catalog.get('families',{})
    if not isinstance(families,dict):return ['families必须分为visual与subtitle两套']
    vi={f['id'] for f in families.get('visual',[])};ti={f['id'] for f in families.get('subtitle',[])}
    ids={g['id'] for g in occ}
    if len(ids)!=len(occ) or not occ:errors.append('occurrence为空或ID重复')
    for g in occ:
        gid=g['id'];mode=g.get('compositionMode');v=g.get('visual');t=g.get('subtitle')
        if mode=='visual-only' and (not v or t):errors.append(gid+':仅画面必须有画面组件且无字幕动效组件；普通口播主字幕另行注明')
        elif mode=='subtitle-only' and (v or not t):errors.append(gid+':仅字幕不得附加普通人物底片为画面组件')
        elif mode=='combined' and not(v and t):errors.append(gid+':组合缺少活动组件')
        elif mode not in {'visual-only','subtitle-only','combined'}:errors.append(gid+':缺少构成类型')
        if mode=='visual-only' and g.get('subtitleComponents'):errors.append(gid+':仅画面残留字幕组件')
        if mode=='subtitle-only' and g.get('visualComponents'):errors.append(gid+':仅字幕残留画面组件')
        if v and v not in vi:errors.append(gid+':画面family不存在')
        if t and t not in ti:errors.append(gid+':字幕family不存在')
        if any(i not in vi for i in g.get('visualComponents',[])):errors.append(gid+':画面组件不存在')
        if any(i not in ti for i in g.get('subtitleComponents',[])):errors.append(gid+':字幕组件不存在')
        if not isinstance(g.get('name'),str) or not g['name'].strip():errors.append(gid+':缺少当前名称')
        a,b=g.get('startFrame'),g.get('endFrame')
        if type(a)is not int or type(b)is not int or not 0<=a<b:errors.append(gid+':帧范围无效')
    for kind,component in [('visual','visual'),('subtitle','subtitle')]:
        for family in families.get(kind,[]):
            members=set(family.get('occurrences',family.get('groups',[])))
            expected={g['id'] for g in occ if g.get(component)==family['id'] or family['id'] in g.get(component+'Components',[])}
            if members!=expected:errors.append(family['id']+':family包含旧ID或漏掉当前实例')
    raw=project/'observations/manual-review/adjustments.json'
    if raw.exists():
        receipt=project/'observations/manual-review/feedback-applied.json'
        if not receipt.exists():errors.append('存在用户标注但未应用')
        else:
            feedback=json.loads(receipt.read_text('utf-8'))
            if feedback.get('sourceSha256')!=hashlib.sha256(raw.read_bytes()).hexdigest():errors.append('反馈应用对应旧版本')
            saved=json.loads(raw.read_text('utf-8'))['groups']
            exclusions={g['id'] for g in feedback.get('excluded',[]) if g.get('reason') and any(s['id']==g['id'] and s.get('note','')==g.get('sourceNote') for s in saved)}
            split_map={x['id']:x for x in feedback.get('splits',[])}
            original={g['id']:g for g in saved}
            for sid,split in split_map.items():
                source=original.get(sid)
                if not source or split.get('sourceNote')!=source.get('note','') or not split.get('reason'):
                    errors.append(sid+':拆分缺少原备注依据');continue
                cursor=source['startFrame']
                for child in split['children']:
                    if child['startFrame']!=cursor or child['endFrame']<=cursor:errors.append(sid+':拆分覆盖不连续')
                    cursor=child['endFrame']
                if cursor!=source['endFrame']:errors.append(sid+':拆分未覆盖最终边界')
            ranges={g['id']:(g['startFrame'],g['endFrame'],g['members']) for g in saved if g['id'] not in exclusions and g['id'] not in split_map}
            for sid,split in split_map.items():
                for child in split['children']:ranges[child['id']]=(child['startFrame'],child['endFrame'],original[sid]['members'])
            current={g['id']:(g['startFrame'],g['endFrame'],g['members']) for g in occ}
            if ranges!=current:errors.append('未逐项保留最终用户边界与合并成员')
    return errors

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);a=p.parse_args()
    errors=validate(a.project.resolve());print(json.dumps({'structureValid':not errors,'errors':errors,'limit':'仅校验结构和版本；不证明真实动作、词级时钟、声音或裁切语义正确。'},ensure_ascii=False,indent=2));raise SystemExit(bool(errors))
