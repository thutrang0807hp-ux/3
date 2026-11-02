"""Draft bounded JSON/form/Google-style batch envelope decoding, never execution.

Decoded documents are transient. Export only structural metadata and the caller's
sanitized facts. RPC method hashes/positional UUID hashes are not task identities.
"""
import hashlib
import json
import re
from urllib.parse import parse_qsl

LIMIT=2*1024*1024
SECRET=re.compile(r'token|authorization|cookie|password|secret|credential|headers?|url|uri|href|base64|bytes|encoded',re.I)
RPC_ID=re.compile(r'^[A-Za-z0-9_-]{2,24}$')
UUID=re.compile(r'^[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$')
FORM_NAMES={'f.req','request','payload','at','bl','hl','authuser','rpcids'}


def media_type(value):
    value=str(value or '').split(';',1)[0].strip().lower()
    return value if re.fullmatch(r'[a-z0-9.+-]+/[a-z0-9.+-]+',value) and len(value)<=100 else 'unknown'


def readable_type(value):
    kind=media_type(value)
    return 'json' in kind or kind in ('text/plain','application/javascript','application/x-www-form-urlencoded')


def _bytes(raw):
    if isinstance(raw,str):raw=raw.encode('utf-8')
    if not isinstance(raw,bytes) or len(raw)>LIMIT:raise ValueError('body_limit_or_type')
    return raw


def _json_stream(raw):
    raw=_bytes(raw);meta={'anti_xssi':False,'length_prefixed':False};docs=[]
    wire=raw.lstrip(b' \t\r\n')
    if wire.startswith(b")]}'"):
        meta['anti_xssi']=True
        if b'\n' not in wire:return [],{**meta,'format':'unknown_text','decode_error':'xssi_line_incomplete'}
        wire=wire.split(b'\n',1)[1].lstrip(b' \t\r\n')
    if not wire:return [],{**meta,'format':'empty'}
    try:
        value=json.loads(wire.decode('utf-8-sig'))
        if isinstance(value,(dict,list)):return [value],{**meta,'format':'json'}
    except (ValueError,UnicodeError):pass
    # Length prefixes are consumed as UTF-8 BYTES, not Python character counts.
    if re.match(rb'^\d{1,10}\r?\n',wire):
        meta['length_prefixed']=True;offset=0
        try:
            while offset<len(wire) and len(docs)<24:
                while offset<len(wire) and wire[offset:offset+1] in (b' ',b'\t',b'\r',b'\n'):offset+=1
                if offset==len(wire):break
                end=wire.find(b'\n',offset)
                if end<0:raise ValueError()
                line=wire[offset:end].rstrip(b'\r')
                if not re.fullmatch(rb'\d{1,10}',line):raise ValueError()
                length=int(line);offset=end+1
                if not 0<length<=LIMIT or offset+length>len(wire):raise ValueError()
                value=json.loads(wire[offset:offset+length].decode('utf-8'))
                if not isinstance(value,(dict,list)):raise ValueError()
                docs.append(value);offset+=length
            meta.update(format='length_prefixed_json',frames=len(docs),truncated=offset<len(wire))
            return docs,meta
        except (ValueError,UnicodeError):
            return docs,{**meta,'format':'length_prefixed_json','frames':len(docs),'decode_error':'framing_mismatch','partial':bool(docs)}
    # Support a sequence of complete JSON containers, not arbitrary substring scraping.
    try:
        text=wire.decode('utf-8');offset=0;decoder=json.JSONDecoder()
        while offset<len(text) and len(docs)<24:
            while offset<len(text) and text[offset].isspace():offset+=1
            if offset==len(text):break
            value,end=decoder.raw_decode(text,offset)
            if not isinstance(value,(dict,list)):raise ValueError()
            docs.append(value);offset=end
        return docs,{**meta,'format':'json_sequence','frames':len(docs),'truncated':offset<len(text)}
    except (ValueError,UnicodeError):
        return docs,{**meta,'format':'unknown_text','decode_error':'not_supported_json_envelope','partial':bool(docs)}


def decode_transport(raw,content_type,*,direction):
    raw=_bytes(raw);kind=media_type(content_type)
    summary={'media_type':kind,'bytes':len(raw),'direction':direction}
    documents=[]
    if kind=='application/x-www-form-urlencoded':
        try:fields=parse_qsl(raw.decode('utf-8'),keep_blank_values=True,max_num_fields=40,encoding='utf-8',errors='strict')
        except (ValueError,UnicodeError):return [],{**summary,'format':'form_urlencoded','decode_error':'form_limit_or_encoding'}
        summary.update(format='form_urlencoded',field_count=len(fields),
                       known_field_names=sorted({key for key,_ in fields if key in FORM_NAMES}),
                       unknown_field_count=sum(key not in FORM_NAMES for key,_ in fields))
        summaries=[]
        # Never decode/log auth form values such as at/token/cookie.
        for index,(key,value) in enumerate(fields):
            if key not in ('f.req','request','payload'):continue
            docs,meta=_json_stream(value)
            source='$form.'+key.replace('.','_')+'['+str(index)+']'
            summaries.append({'source':source,**meta})
            documents.extend((source,doc,key=='f.req' and direction=='request') for doc in docs)
        summary['payload_envelopes']=summaries
    else:
        docs,meta=_json_stream(raw);summary.update(meta)
        documents=[('$' if len(docs)==1 else '$frame['+str(i)+']',doc,False) for i,doc in enumerate(docs)]
    return documents[:24],summary


def unpack_payloads(documents):
    output=[];rpc=[];errors=[];visited=0;decoded_bytes=0;decoded_count=0;truncated=False
    def decode(value,source):
        nonlocal decoded_bytes,decoded_count,truncated
        if not isinstance(value,str) or not value.lstrip().startswith(('{','[')):return
        size=len(value.encode('utf-8'))
        if decoded_count>=16 or decoded_bytes+size>LIMIT:
            truncated=True;return
        try:parsed=json.loads(value)
        except ValueError:return
        if not isinstance(parsed,(dict,list)):return
        decoded_count+=1;decoded_bytes+=size
        output.append((source,parsed));scan(parsed,source,False,0)
    def scan(value,path,request_rpc,depth):
        nonlocal visited,truncated
        visited+=1
        if visited>1000 or depth>8:truncated=True;return
        if isinstance(value,list):
            if len(value)>=3 and value[0]=='wrb.fr' and isinstance(value[1],str):
                rpc.append({'path':path,'wire_tag':'wrb.fr','rpc_id_sha256':hashlib.sha256(value[1].encode()).hexdigest()})
                decode(value[2],path+'.rpc_payload')
                return
            if value and value[0]=='er':
                errors.append({'path':path,'wire_tag':'er','integer_candidates':[{'index':i,'value':v} for i,v in enumerate(value[:8]) if type(v)is int and 0<=v<=9999]})
                return
            if request_rpc and depth<=2 and len(value)>=2 and isinstance(value[0],str) and RPC_ID.fullmatch(value[0]) and isinstance(value[1],str):
                rpc.append({'path':path,'wire_tag':'form_rpc_candidate','rpc_id_sha256':hashlib.sha256(value[0].encode()).hexdigest()})
                decode(value[1],path+'.rpc_payload')
                return
            if len(value)>40:truncated=True
            for i,item in enumerate(value[:40]):
                if isinstance(item,(list,dict)):scan(item,path+'['+str(i)+']',request_rpc,depth+1)
        elif isinstance(value,dict):
            if len(value)>80:truncated=True
            for key,item in list(value.items())[:80]:
                if not isinstance(key,str) or SECRET.search(key):continue
                safe=key if re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}',key) else '[key]'
                child=path+'.'+safe
                if key.lower() in ('payload','result','response','data') and isinstance(item,str):decode(item,child+'.decoded_json')
                elif isinstance(item,(dict,list)):scan(item,child,False,depth+1)
    for source,document,request_rpc in documents:
        output.append((source,document));scan(document,source,request_rpc,0)
        if len(output)>=40:truncated=True;break
    return output[:40],{'rpc_records':rpc[:24],'error_envelopes':errors[:16],
                        'nested_json_documents':decoded_count,'unpack_truncated':truncated}


def structural_summary(payloads):
    budget=80
    def shape(value,depth=0):
        nonlocal budget
        if budget<=0:return {'type':'budget_limit'}
        budget-=1
        if isinstance(value,dict):
            keys=[key for key in value if isinstance(key,str) and not SECRET.search(key)]
            result={'type':'object','key_count':len(value)}
            if depth<3:result['fields']={key if re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}',key) else '[key]':shape(value[key],depth+1) for key in keys[:8] if budget>0}
            return result
        if isinstance(value,list):
            result={'type':'array','length':len(value)}
            if depth<3:result['items']=[shape(item,depth+1) for item in value[:4] if budget>0]
            return result
        if isinstance(value,str):return {'type':'string','length':len(value),'uuid_shape':bool(UUID.fullmatch(value))}
        return {'type':'null' if value is None else 'boolean' if type(value)is bool else 'number'}
    results=[]
    for source,value in payloads[:6]:
        if budget<=0:break
        results.append({'source':source,'shape':shape(value)})
    return {'documents':results,'shape_truncated':budget<=0 or len(payloads)>6}


def decode_evidence(raw,content_type,expected_prompt,fact_reader,*,direction):
    documents,summary=decode_transport(raw,content_type,direction=direction)
    payloads,envelopes=unpack_payloads(documents)
    facts=[];matches=[];truncated=False
    for source,document in payloads:
        data=fact_reader(document,expected_prompt)
        for fact in data['facts']:
            facts.append({**fact,'path':source+fact['path'][1:]})
        matches.extend(source+path[1:] for path in data['exact_prompt_paths'])
        truncated|=data['schema_truncated']
        if len(facts)>=160 or len(matches)>=10:truncated=True;break
    summary.update(envelopes);summary.update(structural_summary(payloads))
    return {'facts':facts[:160],'exact_prompt_paths':matches[:10],'schema_truncated':truncated},summary
