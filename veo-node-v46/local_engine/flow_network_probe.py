"""Passive Flow JSON evidence recorder; candidate facts never prove attribution.

No route interception, requests, retries, Generate clicks, downloads or ledger
updates. Facts are candidates, never proof of task attribution by themselves.
Raw bodies, auth headers, cookies, prompts and media URLs are not exported.
"""
import asyncio
import copy
import hashlib
import json
import math
import re
import time
from urllib.parse import urlsplit

MAX_BODY=2*1024*1024
SECRET_KEY=re.compile(r'token|authorization|cookie|password|secret|credential|headers?|url|uri|href|base64|bytes|encoded',re.I)
ID_KEYS={'operationid':'operation_id','generationid':'generation_id','mediaid':'media_id',
         'videoid':'video_id','assetid':'asset_id','jobid':'job_id','projectid':'project_id',
         'requestid':'request_id','taskid':'task_id','operationname':'operation_name','medianame':'media_name'}
STATUS_KEYS={'status','state','generationstatus','videogenerationstatus','operationstatus','mediagenerationstatus','videostatus','taskstatus','taskstate','operationstate'}
PROGRESS_KEYS={'progress','progresspercent','percentcomplete','percentage'}
CONTEXT=re.compile(r'operations?|generations?|media|videos?|assets?|jobs?|requests?|results?',re.I)
SAFE_ID=re.compile(r'^[A-Za-z0-9_/-]{1,240}$')
ENDPOINT_HINT=re.compile(r'generat|operation|media|video|batchexecute',re.I)


def normalized(value):
    return re.sub(r'\s+',' ',str(value)).strip()


def endpoint_summary(url):
    parsed=urlsplit(url)
    # No query, fragment, credentials or opaque path segments in output.
    fixed={'video','videos','media','operations','projects','assets','status','generate','batch',
           '_','AiSandboxAngularFrontend','data','batchexecute'}
    parts=[]
    for part in parsed.path.split('/'):
        if not part:continue
        resource,_,action=part.partition(':')
        public_rpc=resource in fixed and bool(re.fullmatch(r'(?:batch|async|get|create|generate|fetch|list|check|download)[A-Za-z]*',action,re.I))
        parts.append(part if part in fixed or public_rpc or re.fullmatch(r'v\d+(?:alpha|beta)?\d*',part) else '[segment]')
    return {'origin':parsed.scheme+'://'+(parsed.hostname or ''),'path_shape':'/'+('/'.join(parts)),
            'path_sha256':hashlib.sha256(parsed.path.encode()).hexdigest()}


def json_document(raw):
    if isinstance(raw,bytes):
        if len(raw)>MAX_BODY:raise ValueError('body_limit')
        raw=raw.decode('utf-8')
    if not isinstance(raw,str) or len(raw.encode('utf-8'))>MAX_BODY:raise ValueError('body_limit')
    # Google sometimes prefixes JSON with an anti-XSSI line.
    text=raw.lstrip()
    if text.startswith(")]}'"):
        if '\n' not in text:raise ValueError('unsupported_json_prefix')
        text=text.split('\n',1)[1]
    result=json.loads(text)
    if not isinstance(result,(dict,list)):raise ValueError('non_container_json')
    return result


def candidate_facts(document,expected_prompt):
    facts=[];matches=[];visited=0;truncated=False
    def walk(value,path='$',depth=0,context=''):
        nonlocal visited,truncated
        visited+=1
        if visited>800 or depth>10:
            truncated=True;return
        if isinstance(value,list):
            if len(value)>40:truncated=True
            for i,item in enumerate(value[:40]):walk(item,f'{path}[{i}]',depth+1,context)
        elif isinstance(value,str):
            if expected_prompt and normalized(value)==expected_prompt:matches.append(path)
        elif isinstance(value,dict):
            if len(value)>80:truncated=True
            for key,item in list(value.items())[:80]:
                if not isinstance(key,str) or SECRET_KEY.search(key):continue
                safe_key=key if re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}',key) else '[key]'
                child=f'{path}.{safe_key}';plain=key.replace('_','').lower()
                kind=ID_KEYS.get(plain)
                if plain in ('id','name') and CONTEXT.search(context):kind='context_'+plain
                if plain=='name' and isinstance(item,str) and re.match(r'^(projects|operations|media|videos|assets)/',item):kind='resource_name'
                if plain in ('operation','generation','media','asset','video','job','task') and isinstance(item,str):kind=plain+'_reference'
                if kind and isinstance(item,str) and SAFE_ID.fullmatch(item) and not item.startswith('eyJ'):
                    facts.append({'path':child,'kind':kind,'value':item})
                elif plain in STATUS_KEYS and isinstance(item,str) and re.fullmatch(r'[A-Za-z][A-Za-z_-]{0,63}',item):
                    facts.append({'path':child,'kind':'state_candidate','value':item})
                elif plain in ('done','success','failed','completed') and type(item)is bool:
                    facts.append({'path':child,'kind':'boolean_state_candidate','value':item})
                elif plain in PROGRESS_KEYS and type(item)in(int,float) and math.isfinite(item) and 0<=item<=100:
                    facts.append({'path':child,'kind':'progress_candidate','value':item})
                elif plain=='code' and 'error'in context.lower() and type(item)is int:
                    facts.append({'path':child,'kind':'error_code','value':item})
                if plain in ('prompt','textprompt','positiveprompt','text','userinput') and isinstance(item,str) and expected_prompt and normalized(item)==expected_prompt:
                    matches.append(child)  # No prompt text is stored.
                if isinstance(item,(dict,list)):walk(item,child,depth+1,key)
                if len(facts)>=160 or visited>800:
                    truncated=True;return
    walk(document)
    return {'facts':facts[:160],'exact_prompt_paths':matches[:10],'schema_truncated':truncated}


class FlowNetworkProbe:
    def __init__(self,page,request_id,expected_prompt,check,*,context=None,
                 max_requests=300,max_pending=8,duration=600,
                 allow_unannounced_json=True,initial_response_timeout=15,max_fact_bytes=4*1024*1024,
                 task_tracker=None):
        if type(max_requests)is not int or max_requests<1 or type(max_pending)is not int or max_pending<1:
            raise ValueError('Request/task limits must be positive integers')
        if any(type(value) not in (int,float) or not math.isfinite(value) or value<=0 for value in (duration,initial_response_timeout)):
            raise ValueError('Timeouts must be positive finite numbers')
        if type(max_fact_bytes)is not int or max_fact_bytes<1:raise ValueError('Fact byte limit must be positive')
        self.max_fact_bytes=max_fact_bytes;self.fact_bytes=0
        self.page=page;self.check=check;self.expected=normalized(expected_prompt)
        self.task_tracker=task_tracker
        self.max_requests=max_requests;self.max_pending=max_pending;self.duration=duration
        self.allow_unannounced_json=allow_unannounced_json
        self.initial_response_timeout=initial_response_timeout
        self.background_limit=max(1,max_requests//4);self.background_count=0
        self.watchdog=None
        self.started=None;self.click_time=None;self.accepting=False;self.tasks=set();self.requests={}
        self.handlers={'request':self._request,'response':self._response,'requestfailed':self._failed}
        allowed_context={k:v for k,v in (context or {}).items() if k in ('room_id','scene_id','part','account_id') and isinstance(v,str) and len(v)<=100}
        self.report={'request_id':request_id,'context':allowed_context,'mode':'passive_network_evidence',
            'expected_prompt_sha256':hashlib.sha256(self.expected.encode()).hexdigest(),
            'association_confirmed':False,'generation_submitted_by_probe':False,
            'requests':[],'warnings':[],'dropped_events':0,
            'candidate_response_count_after_generate_attempt':0,
            'initial_response_wait':'not_started','http_error_response_count':0,
            'limits':{'requests':max_requests,'background_summaries':self.background_limit,
                      'pending_tasks':max_pending,'duration_seconds':duration,
                      'initial_response_warning_seconds':initial_response_timeout,'fact_bytes':max_fact_bytes}}

    def _warn(self,value):
        if value not in self.report['warnings'] and len(self.report['warnings'])<20:self.report['warnings'].append(value)

    def _in_scope(self,request):
        if not self.accepting or time.monotonic()-self.started>self.duration:return False
        try:
            destination=urlsplit(request.url);host=destination.hostname or ''
            if destination.scheme!='https' or destination.username or destination.password:return False
            if host!='flow.google.com' and not host.endswith('.googleapis.com'):return False
            if request.resource_type not in ('xhr','fetch'):return False
            # Ignore auth/captcha/third-party iframe traffic.
            owner=urlsplit(request.frame.url)
            return owner.scheme=='https' and owner.hostname=='flow.google.com'
        except Exception:
            self._warn('request_frame_unavailable');return False

    def _spawn(self,coroutine,*,priority='high'):
        # Background parsing cannot occupy all capture slots when the limit is >2.
        limit=min(2,self.max_pending) if priority=='background' else self.max_pending
        if len(self.tasks)>=limit:
            coroutine.close();self.report['dropped_events']+=1;return
        task=asyncio.create_task(coroutine);self.tasks.add(task)
        def finished(done):
            self.tasks.discard(done)
            if not done.cancelled():
                error=done.exception()
                if error:self._warn('capture_error:'+type(error).__name__)
        task.add_done_callback(finished)

    def _entry(self,request):
        if request in self.requests:return self.requests[request]
        priority='high' if ENDPOINT_HINT.search(urlsplit(request.url).path) else 'background'
        if priority=='background' and self.background_count>=self.background_limit:
            self._warn('background_summary_limit');self.report['dropped_events']+=1;return None
        if len(self.requests)>=self.max_requests:
            self._warn('request_limit');self.report['dropped_events']+=1;return None
        now=time.monotonic()
        endpoint=endpoint_summary(request.url)
        entry={'http_request':'http-'+str(len(self.requests)+1),'priority':priority,
            'endpoint_label':request.method+' '+endpoint['origin']+endpoint['path_shape'],
            'request_at_unix':time.time(),
            'request_ms_from_generate':round((now-self.click_time)*1000) if self.click_time is not None else None,
            'method':request.method,'endpoint':endpoint,
            'started_ms':round((now-self.started)*1000),
            'request_after_generate_attempt':self.click_time is not None,
            'request_facts':None,'response_facts':None}
        self.requests[request]=entry;self.report['requests'].append(entry)
        if priority=='background':self.background_count+=1
        return entry

    def _save_facts(self,entry,key,facts):
        size=len(json.dumps(facts,ensure_ascii=False).encode('utf-8'))
        if self.fact_bytes+size>self.max_fact_bytes:
            entry[key+'_omitted']='fact_byte_limit';self._warn('fact_export_byte_limit');return False
        self.fact_bytes+=size;entry[key]=facts;return True

    def _request(self,request):
        if not self._in_scope(request):return
        entry=self._entry(request)
        if entry:
            if self.task_tracker:
                try:
                    self.task_tracker.observe_request(entry['http_request'],request.url,request.method,
                        request.headers.get('content-type',''),request.post_data,entry['request_after_generate_attempt'])
                except Exception as error:
                    try:self.task_tracker.invalidate('task_request_capture_failed')
                    except Exception:pass
                    self._warn('task_request_capture_failed:'+type(error).__name__)
            self._spawn(self._request_json(request,entry),priority=entry['priority'])

    async def _binding_ok(self):
        try:await asyncio.wait_for(self.check(),2);return True
        except Exception as error:
            self.accepting=False;self.report['initial_response_wait']='binding_check_failed'
            self._warn('binding_check_failed:'+type(error).__name__);return False

    async def _request_json(self,request,entry):
        if not await self._binding_ok():return
        from .flow_network_protocol import media_type,readable_type,decode_evidence
        kind=await request.header_value('content-type') or ''
        entry['request_media_type']=media_type(kind)
        if not readable_type(kind):
            entry['request_body']='unsupported_media_type';return
        try:
            raw=request.post_data
            if raw is None:entry['request_body']='empty';return
            facts,transport=decode_evidence(raw,kind,self.expected,candidate_facts,direction='request')
            self._save_facts(entry,'request_facts',facts)
            self._save_facts(entry,'request_transport',transport)
            entry['request_body']='decoded_not_saved'
        except Exception as error:entry['request_body']='unreadable:'+type(error).__name__

    def _response(self,response):
        request=response.request
        if not self._in_scope(request):return
        # Do not pretend a request first observed at response time started after click.
        entry=self.requests.get(request)
        if not entry:
            self._warn('response_without_observed_request');return
        now=time.monotonic()
        entry['http_status']=response.status
        entry['http_success']=200<=response.status<300
        entry['response_at_unix']=time.time()
        entry['response_ms']=round((now-self.started)*1000)
        entry['response_ms_from_generate']=round((now-self.click_time)*1000) if self.click_time is not None else None
        if response.status>=400:self.report['http_error_response_count']+=1
        # HTTP errors remain evidence; they are not filtered out.
        if entry['priority']=='high':self._candidate_response(entry,'endpoint_keyword')
        self._spawn(self._response_json(response,entry),priority=entry['priority'])

    async def _response_json(self,response,entry):
        if not await self._binding_ok():return
        from .flow_network_protocol import media_type,readable_type,decode_evidence
        kind=await response.header_value('content-type') or ''
        entry['response_media_type']=media_type(kind)
        if not readable_type(kind):
            entry['response_body']='unsupported_media_type';return
        length=await response.header_value('content-length')
        try:announced=int(length) if length is not None else None
        except ValueError:announced=None
        if announced is not None and announced>MAX_BODY:
            entry['response_body']='announced_body_limit';return
        if announced is None and not self.allow_unannounced_json:
            entry['response_body']='missing_content_length';return
        if announced is None:
            self._warn('unknown_length_json_body_read_then_size_checked')
        try:
            # Playwright exposes whole bodies, not a bounded stream. With unknown
            # Content-Length this limit is checked AFTER reading; not a hard RAM cap.
            raw=await asyncio.wait_for(response.body(),2)
            if self.task_tracker and len(raw)<=MAX_BODY:
                self.task_tracker.observe_response(entry['http_request'],response.status,raw)
            facts,transport=decode_evidence(raw,kind,self.expected,candidate_facts,direction='response')
            self._save_facts(entry,'response_facts',facts)
            self._save_facts(entry,'response_transport',transport)
            entry['response_body']='decoded_not_saved'
            if transport.get('rpc_records') or transport.get('error_envelopes'):
                self._candidate_response(entry,'rpc_envelope_candidate')
            if entry.get('response_facts',{} ) and entry['response_facts']['facts']:
                self._candidate_response(entry,'json_candidate_fields')
        except Exception as error:entry['response_body']='unreadable:'+type(error).__name__

    def _candidate_response(self,entry,reason):
        # A background response to a PRE-click request cannot count as a new send.
        if not entry['request_after_generate_attempt']:return
        reasons=entry.setdefault('candidate_response_reasons',[])
        if reason not in reasons:reasons.append(reason)
        if entry.get('candidate_response'):return
        entry['candidate_response']=True
        self.report['candidate_response_count_after_generate_attempt']+=1
        previous=self.report['initial_response_wait']
        self.report['initial_response_wait']='late_candidate_seen' if previous in ('warning_no_candidate_response','late_candidate_seen') else 'candidate_seen'
        # Candidate only: does NOT confirm acceptance, task identity or success.

    async def _initial_response_watchdog(self):
        await asyncio.sleep(self.initial_response_timeout)
        if not self.accepting:return
        if not self.report['candidate_response_count_after_generate_attempt']:
            self.report['initial_response_wait']='warning_no_candidate_response'
            self._warn('no_candidate_response_in_initial_window_keep_observing')
        # Keep the original observation duration. No Generate/retry/failure action.

    def _failed(self,request):
        entry=self.requests.get(request)
        if entry:entry['transport_failed']=True  # Not proof of generation failure.

    async def start(self):
        if self.started is not None:raise RuntimeError('Probe already started')
        await self.check()
        self.started=time.monotonic();self.accepting=True;self.report['started_at']=time.time()
        for event,handler in self.handlers.items():self.page.on(event,handler)

    async def mark_generate_attempt(self):
        """Call immediately BEFORE the existing button.click(), not instead of it."""
        if not self.accepting or self.click_time is not None:raise RuntimeError('Probe not ready or attempt already marked')
        await self.check();self.click_time=time.monotonic()
        if self.task_tracker:self.task_tracker.mark_generate_attempt()
        self.report['generate_attempt_ms']=round((self.click_time-self.started)*1000)
        self.report['generate_attempt_at_unix']=time.time()
        for entry in self.report['requests']:
            entry['request_ms_from_generate']=entry['started_ms']-self.report['generate_attempt_ms']
            if 'response_ms' in entry:
                entry['response_ms_from_generate']=entry['response_ms']-self.report['generate_attempt_ms']
        self.report['initial_response_wait']='waiting_for_candidate'
        self.watchdog=asyncio.create_task(self._initial_response_watchdog())

    def mark_click_returned(self):
        # A returned click is not proof Flow accepted/created a task.
        self.report['click_call_returned']=True

    def snapshot(self):
        result=copy.deepcopy(self.report)
        # Priority affects report order; the local HTTP labels/timestamps stay fixed.
        result['requests'].sort(key=lambda item:(item['priority']!='high',item['started_ms']))
        return result

    async def stop(self):
        self.accepting=False
        for event,handler in self.handlers.items():self.page.remove_listener(event,handler)
        if self.watchdog and not self.watchdog.done():
            self.watchdog.cancel();await asyncio.gather(self.watchdog,return_exceptions=True)
        if self.report['initial_response_wait']=='waiting_for_candidate':
            self.report['initial_response_wait']='stopped_before_initial_warning'
        if self.tasks:
            _,pending=await asyncio.wait(tuple(self.tasks),timeout=3)
            for task in pending:task.cancel()
            if pending:await asyncio.gather(*pending,return_exceptions=True)
        self.report['stopped_at']=time.time()
        result=self.snapshot();self.requests.clear()
        return result
