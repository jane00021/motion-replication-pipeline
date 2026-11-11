"""Behavioral regression for immutable feedback, splits, modes, membership and timestamps."""
import copy,hashlib,json,tempfile
from pathlib import Path
from apply_observation_feedback import apply,write,read
from validate_decomposition import validate

def run():
    with tempfile.TemporaryDirectory(prefix='motion-feedback-test-') as root:
        p=Path(root)
        def group(i,a,b,n):return {'id':i,'name':i,'startFrame':a,'endFrame':b,'members':[i],'visual':'V','subtitle':'T','visualComponents':['V'],'subtitleComponents':['T'],'compositionMode':'combined','note':n,'purpose':'test','relation':'test'}
        raw={'fps':30,'updatedAt':'2026-01-01T00:00:00Z','groups':[group('A',0,4,'split here'),group('B',5,8,'subtitle only'),group('C',9,12,'remove')]}
        write(p/'observations/manual-review/adjustments.json',raw)
        meta={'totalFrames':12,'frameTimes':[0,.031,.067,.102,.140,.173,.211,.248,.282,.319,.352,.390,.430],'completeGroups':raw['groups'],'visualFamilies':[{'id':'V','name':'visual'}],'subtitleFamilies':[{'id':'T','name':'subtitle'}]}
        write(p/'observations/decomposition-preview/metadata.json',meta);write(p/'observations/group-catalog.json',{})
        overrides={'A':{'sourceNote':'split here','reason':'two mechanisms','fields':{},'split':[{'id':'A1','startFrame':0,'endFrame':2},{'id':'A2','startFrame':2,'endFrame':4}]},'B':{'sourceNote':'subtitle only','reason':'static shot is not motion','fields':{'compositionMode':'subtitle-only'}},'C':{'sourceNote':'remove','reason':'outside analysis scope','fields':{'excluded':True}}}
        path=p/'interpretations.json';write(path,overrides)
        before=(p/'observations/manual-review/adjustments.json').read_bytes()
        receipt=apply(p,path);assert validate(p)==[]
        cat=read(p/'observations/group-catalog.json');gs={g['id']:g for g in cat['occurrences']}
        assert set(gs)=={'A1','A2','B'} and gs['B']['visual'] is None and gs['B']['visualComponents']==[]
        assert gs['A2']['source']['start']==.067 and gs['A2']['source']['end']==.140
        assert gs['B']['startFrame']==5 and gs['B']['endFrame']==8
        assert cat['families']['visual'][0]['occurrences']==['A1','A2']
        assert (p/'observations/manual-review/adjustments.json').read_bytes()==before
        apply(p,path);assert validate(p)==[]  # idempotent rerun retains stable lineage
        bad=copy.deepcopy(overrides);bad['A']['split'][1]['startFrame']=3;write(path,bad)
        try:apply(p,path)
        except ValueError:pass
        else:raise AssertionError('split gap accepted')
        bad=copy.deepcopy(overrides);bad['B']['sourceNote']='stale';write(path,bad)
        try:apply(p,path)
        except ValueError:pass
        else:raise AssertionError('stale note accepted')
        bad=copy.deepcopy(overrides);bad['B']['fields']['startFrame']=4;write(path,bad)
        try:apply(p,path)
        except ValueError:pass
        else:raise AssertionError('user boundary overwritten')
        write(path,overrides);apply(p,path)
        cat=read(p/'observations/group-catalog.json');cat['families']['visual'][0]['occurrences'].append('A');write(p/'observations/group-catalog.json',cat)
        assert any('旧ID' in e for e in validate(p))
        print(json.dumps({'passed':True,'checks':['immutable raw','split coverage','split lineage','mode component cleanup','VFR source timing','preserved gaps','membership regeneration','idempotence','invalid split rejected','stale note rejected','boundary overwrite rejected','stale member detected']},ensure_ascii=False))

if __name__=='__main__':run()
