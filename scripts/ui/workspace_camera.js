/* Save only three camera numbers; no extra frames, images or media cache. */
(()=>{
 const roomId=new URLSearchParams(location.search).get('room');if(!roomId)return;
 const key='sceneforge-workspace-camera-v130:'+roomId;let ready=false,timer=null,saved=null;
 const valid=v=>v&&['x','y','z'].every(k=>Number.isFinite(v[k]))&&Math.abs(v.x)<100000&&Math.abs(v.y)<100000&&v.z>=.25&&v.z<=1.8;
 try{const v=JSON.parse(sessionStorage.getItem(key));if(valid(v))saved=v;}catch{}
 function capture(){if(!ready)return;saved={x:view.x,y:view.y,z:view.z};try{sessionStorage.setItem(key,JSON.stringify(saved));}catch{}}
 function restore(){if(saved&&valid(saved)){Object.assign(view,saved);applyView();}ready=true;capture();}
 window.SFWorkspaceCamera={restore,capture};
 const apply=applyView;applyView=function(...args){const result=apply(...args);if(ready){clearTimeout(timer);timer=setTimeout(capture,120);}return result;};
 const attach=setInterval(()=>{const api=window.SceneForgeWorkflow;if(!api?.openRoom)return;clearInterval(attach);
  const open=api.openRoom;api.openRoom=async function(...args){ready=false;const result=await open.apply(this,args);restore();return result;};
  const flush=api.flushRoom;api.flushRoom=async function(...args){capture();return flush?.apply(this,args);};
  if(typeof photoFlowDialog==='function')api.openVideoSettings=()=>photoFlowDialog();
  api.getViewport=()=>({x:view.x,y:view.y,z:view.z});api.setViewport=v=>{if(!valid(v))return false;Object.assign(view,v);applyView();capture();return true;};
 },10);
 window.addEventListener('pagehide',capture);
})();
