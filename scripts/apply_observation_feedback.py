"""Import human review as the current decomposition; never rewrite raw annotations."""
import argparse,copy,hashlib,json
from pathlib import Path

def read(path):return json.loads(path.read_text('utf-8'))
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf-8')

def apply(project,interpretations=None):
    raw=project/'observations/manual-review/adjustments.json'
    data=read(raw);sha=hashlib.sha256(raw.read_bytes()).hexdigest()
    fps=data['fps'];overrides=read(interpretations) if interpretations else {}
    meta_path=project/'observations/decomposition-preview/metadata.json';meta=read(meta_path)
    analysis={};groups=[];decisions=[];unresolved=[];excluded=[];splits=[]
    expanded=[]
    for source in data['groups']:
        override=overrides.get(source['id'],{})
        children=override.get('split')
        if children is None:
            expanded.append((source,source['id'],source));continue
        if override.get('sourceNote')!=source.get('note','') or not override.get('reason') or len(children)<2:
            raise ValueError('拆分必须引用原备注、说明理由并提供至少两个子组')
        cursor=source['startFrame'];child_ids=[]
        for child in children:
            if child['startFrame']!=cursor or child['endFrame']<=cursor or child['id'] in {g['id'] for g in data['groups']}:
                raise ValueError('拆分须用新ID并连续完整覆盖父组范围')
            g=copy.deepcopy(source);g.update(child);g['sourceAnnotationId']=source['id'];g['members']=source['members']
            cursor=g['endFrame'];child_ids.append({'id':g['id'],'sourceAnnotationId':g.get('sourceAnnotationId'),'startFrame':g['startFrame'],'endFrame':g['endFrame']});expanded.append((g,source['id'],source))
        if cursor!=source['endFrame']:raise ValueError('拆分子组未覆盖父组终点')
        splits.append({'id':source['id'],'startFrame':source['startFrame'],'endFrame':source['endFrame'],'members':source['members'],'children':child_ids,'sourceNote':source.get('note',''),'reason':override['reason']})
    for source,origin_id,raw_source in expanded:
        g=copy.deepcopy(source);gid=g['id']
        override=overrides.get(origin_id)
        if override:
            if not override.get('reason') or override.get('sourceNote')!=raw_source.get('note',''):
                raise ValueError(f'{gid}: 解释修订必须引用当前原备注并说明理由')
            g.update(override.get('fields',{}));decisions.append({'id':gid,**override})
            if override.get('fields',{}).get('excluded') is True:
                excluded.append({'id':gid,'sourceNote':raw_source.get('note',''),'reason':override['reason']});continue
        if not g.get('sourceAnnotationId') and any(g.get(k)!=raw_source.get(k) for k in ('id','startFrame','endFrame','members')):
            raise ValueError(gid+':非拆分解释不得改变用户边界、ID或成员')
        mode=g.get('compositionMode')
        if mode not in {'visual-only','subtitle-only','combined'}:
            raise ValueError(f'{gid}: 缺少完整组构成类型')
        for kind,disabled in [('visual',mode=='subtitle-only'),('subtitle',mode=='visual-only')]:
            comp=[] if disabled else list(dict.fromkeys(g.get(kind+'Components') or ([g[kind]] if g.get(kind) else [])))
            g[kind+'Components']=comp;g[kind]=comp[0] if comp else None
        v,t=g.get('visual'),g.get('subtitle')
        if mode=='subtitle-only':g['visual']=None
        if mode=='visual-only':g['subtitle']=None
        if (mode=='combined' and not(v and t)) or (mode=='visual-only' and not v) or (mode=='subtitle-only' and not t):
            raise ValueError(f'{gid}: 活动组件与构成方式不一致')
        start,end=g['startFrame'],g['endFrame']
        if type(start) is not int or type(end) is not int or not 0<=start<end<=meta['totalFrames']:
            raise ValueError(f'{gid}: 帧范围无效')
        def tc(f):
            sec=meta['frameTimes'][f] if meta.get('frameTimes') else f/fps;return f'{int(sec//60):02d}:{sec%60:06.3f}'
        g.update(timecode=tc(start)+'-'+tc(end),durationFrames=end-start,boundaryAuthority='interpreted-split-of-user-range' if g.get('sourceAnnotationId') else 'user-saved-frames',sourceType='original-reference')
        g['source']={'start':meta['frameTimes'][start] if meta.get('frameTimes') else start/fps,'end':meta['frameTimes'][end] if meta.get('frameTimes') else end/fps}
        g['classificationRevision']='feedback-'+sha[:16]
        g.pop('reference',None)
        previous=meta.get('feedbackAnalysis',{}).get(gid,{})
        purpose=g.get('purpose',previous.get('purpose','待确认表达目的'))
        analysis[gid]={'name':g['name'],'visual':g.get('visual'),'subtitle':g.get('subtitle'),'visualComponents':g.get('visualComponents',[g['visual']] if g.get('visual') else []),'subtitleComponents':g.get('subtitleComponents',[g['subtitle']] if g.get('subtitle') else []),'layerOrder':g.get('layerOrder',[]),'compositionMode':mode,'purpose':purpose,'completeGroup':gid,'relation':g.get('relation',previous.get('relation','待核对接力')),'boundaryEvidence':g.get('boundaryEvidence'),'confidence':'反馈已应用；量测未验收','userNote':raw_source.get('note',''),'ordinarySpeechCaption':g.get('ordinarySpeechCaption',False)}
        groups.append(g)
    receipt={'schema':3,'status':'applied-not-stage-approved','source':'observations/manual-review/adjustments.json','sourceSha256':sha,'annotationCount':len(data['groups']),'completeGroupCount':len(groups),'excluded':excluded,'splits':splits,'sourceUpdatedAt':data.get('updatedAt'),'sourceSavedAt':data.get('savedAt'),'rawPreserved':True,'decisions':decisions,'unresolved':overrides.get('_unresolved',unresolved),'lessons':overrides.get('_lessons',meta.get('feedbackReceipt',{}).get('lessons',[]))}
    if len({g['id'] for g in groups})!=len(groups):raise ValueError('最终子组ID重复')
    # Regenerate all family membership from live IDs, not obsolete merged children.
    for field,component in [('visualFamilies','visual'),('subtitleFamilies','subtitle')]:
        families=[]
        for f in overrides.get('_families',{}).get(component,meta.get(field,[])):
            members=[g['id'] for g in groups if g.get(component)==f['id'] or f['id'] in g.get(component+'Components',[])]
            if members:families.append({**f,'groups':members,'occurrences':members})
        meta[field]=families
    meta.update(completeGroups=groups,reviewedOccurrences=groups,feedbackAnalysis=analysis,feedbackReceipt=receipt,classificationRevision='feedback-'+sha[:16],complete_group_count=len(groups),visual_family_count=len(meta.get('visualFamilies',[])),subtitle_family_count=len(meta.get('subtitleFamilies',[])))
    meta['pairings']=[]
    for f in meta.get('visualFamilies',[]):
        gs=[g for g in groups if g.get('visual')==f['id'] or f['id'] in g.get('visualComponents',[])]
        names=[s['name'] for s in meta.get('subtitleFamilies',[]) if any(s['id'] in g.get('subtitleComponents',[]) for g in gs)]
        meta['pairings'].append({'visual':f['name'],'withSubtitles':names,'ordinaryCaptionOnly':all(g['compositionMode']=='visual-only' for g in gs),'purpose':f.get('mechanism','待确认'),'evidence':[g['id'] for g in gs],'sequences':[{'id':g['id'],'purpose':g.get('purpose'),'relation':g.get('relation')} for g in gs],'reuseStatus':'本片证据，跨内容复用未验证'})
    old=read(project/'observations/group-catalog.json')
    old.update(status='feedback-applied-not-stage-approved',families={'visual':meta.get('visualFamilies',[]),'subtitle':meta.get('subtitleFamilies',[])},occurrences=groups,completeGroups=groups,feedback=receipt)
    old['variants']=[{'visualFamily':f['id'],'occurrences':f['groups'],'reason':'共同核心动作；背景、描边、素材和字幕差异作为实例变体','details':[{'id':g['id'],'variant':g.get('visualVariant',''),'relation':g.get('relation','')} for g in groups if f['id'] in g.get('visualComponents',[])]} for f in meta.get('visualFamilies',[]) if len(f['groups'])>1]
    write(project/'observations/group-catalog.json',old)
    write(project/'observations/shot-index.json',{'fps':fps,'endFrameConvention':'exclusive','sourceSha256':sha,'occurrences':[{'id':g['id'],'sourceAnnotationId':g.get('sourceAnnotationId'),'startFrame':g['startFrame'],'endFrame':g['endFrame'],'members':g['members']} for g in groups]})
    for target,field in [('visual-groups.json','visualFamilies'),('subtitle-groups.json','subtitleFamilies')]:
        write(project/'measurements'/target,{'status':'最终用户拆解反馈已应用；数值量测未验收','sourceSha256':sha,'families':meta[field],'measurements':[],'unknowns':['未完成的逐帧轨迹/字级时钟/声音落点须保持未知。']})
    write(meta_path,meta);write(project/'observations/manual-review/feedback-applied.json',receipt)
    return receipt

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--project',type=Path,required=True);parser.add_argument('--interpretations',type=Path)
    args=parser.parse_args();print(json.dumps(apply(args.project.resolve(),args.interpretations),ensure_ascii=False,indent=2))
