#!/usr/bin/env python3
"""Create a supplemented catalogue here. The historical catalogue is read, never edited."""
import copy
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[1]/'data/works.json'
base_bytes=SOURCE.read_bytes()
base=json.loads(base_bytes)
delta=json.loads((HERE/'registry-delta.json').read_text(encoding='utf-8'))
rows=copy.deepcopy(base['works'])
by_id={row['id']:row for row in rows}
assert len(by_id)==len(rows)
added=[]; updated=[]; corrected=[]
for change in delta['records']:
    key=change['id']; action=change['action']
    event={'date':change['version_date'] if 'version_date' in change else delta['checked_at'],'checked_at':delta['checked_at'],'what':change['claim'],'url':change['url'],'limitations':change['limits']}
    if action=='add':
        assert key not in by_id,key
        if change.get('arxiv'):
            assert not any(r.get('identifiers',{}).get('arxiv')==change['arxiv'] for r in rows),change['arxiv']
        assert not any(r.get('urls',{}).get('primary')==change['url'] for r in rows),change['url']
        row={'id':key,'aliases':[],'kind':change['kind'],'title':change['title'],'authors':change['authors'],'n_authors':len(change['authors']),'orgs':change['orgs'],'date_first_public':change['first_public'],'year':int(change['first_public'][:4]),'identifiers':{'arxiv':change.get('arxiv'),'doi':None},'urls':{'primary':change['url'],'code':change.get('code')},'in_analytic_corpus':False,'level':'dated_supplement','chapters':change['chapters'],'updates':[event],'added':delta['checked_at'],'status_note':'Qualified in dated supplement; not included in historical 153-work analytics.'}
        rows.append(row);by_id[key]=row;added.append(key)
    elif action=='update':
        row=by_id[key]
        assert row.get('identifiers',{}).get('arxiv')==change['arxiv'],key
        row['authors']=change['authors'];row['n_authors']=len(change['authors'])
        row.setdefault('updates',[]).append(event);updated.append(key)
    elif action=='correct':
        row=by_id[key]
        expected=change['remove_own_identifier'].split(':',1)[1]
        assert row['identifiers']['arxiv']==expected,key
        row['identifiers']['arxiv']=None
        assert change['remove_own_identifier'] in row['related_keys']
        row.setdefault('updates',[]).append(event);corrected.append(key)
    else:
        raise ValueError(action)
result={'version':'dated-supplement-2026-10-19','generated_by':'updates/2026-10-19/merge_catalogue.py','base_commit':delta['base_commit'],'base_registry_sha256':hashlib.sha256(base_bytes).hexdigest(),'base_source_cutoff':base['source_cutoff'],'supplement_checked_at':delta['checked_at'],'coverage':delta['coverage'],'counts':{'base_records':len(base['works']),'added_records':len(added),'updated_records':len(updated),'corrected_records':len(corrected),'total_records':len(rows),'historical_analytic_corpus':base['stats']['corpus']},'added_ids':added,'updated_ids':updated,'corrected_ids':corrected,'works':rows}
(HERE/'catalogue.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert SOURCE.read_bytes()==base_bytes
print(json.dumps(result['counts']))
