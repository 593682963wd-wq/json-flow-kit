"""作者：Wangyuan；日期：2026-10-29；职责：无网络的显式数据转换流水线。"""
import json,csv,io
from transforms import _resolve_path,_dedupe_rows,_to_rows,_to_markdown

def run(payload):
    if not isinstance(payload,dict):raise TypeError('输入须为对象')
    data=payload.get('data',[]);steps=payload.get('steps',[]);trace=[]
    if not isinstance(steps,list):raise TypeError('steps须为数组')
    for step in steps:
        kind=step['type']
        if kind=='select':data=_resolve_path(data,step['path'])
        elif kind=='map':
            rows=_to_rows(data);data=[{key:_resolve_path(row,path) for key,path in step['fields'].items()} for row in rows]
        elif kind=='dedupe':data=_dedupe_rows(_to_rows(data),step.get('key'))
        elif kind=='filter':data=[row for row in _to_rows(data) if _resolve_path(row,step['path'])==step['equals']]
        elif kind=='sort':data=sorted(_to_rows(data),key=lambda row:_resolve_path(row,step['path']),reverse=bool(step.get('descending')))
        elif kind=='limit':
            count=step['count']
            if type(count)!=int or count<0:raise ValueError('count须非负整数')
            data=_to_rows(data)[:count]
        elif kind=='markdown':data=_to_markdown(data)
        elif kind=='csv':
            rows=_to_rows(data);out=io.StringIO();headers=list(dict.fromkeys(key for row in rows for key in row));w=csv.DictWriter(out,fieldnames=headers);w.writeheader();w.writerows(rows);data=out.getvalue()
        else:raise ValueError('不支持的步骤；此发行版没有HTTP/脚本执行器')
        trace.append({'type':kind,'size':len(data) if isinstance(data,(list,dict,str)) else None})
    return {'data':data,'trace':trace}
