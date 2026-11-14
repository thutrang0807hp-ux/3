async function openRoom(id,view=null){
 const navigation=navigationEpoch;if(switching)return;const room=roomFor(id);if(!room)return;
 if(activeWorkers.has(id)){toast('Phòng đang dò cảnh cục bộ. Bạn có thể mở khi dò xong.');return;}
 const previous={room:currentRoom,view:currentView,frameRoom,lastRoom:prefs.lastRoom};let departure=null,restored=false,disposed=false;
 switching=true;document.body.classList.add('branchSwitching');$('#roomLoading').hidden=false;
 try{
  if(frameRoom!==id){
   await flushFrames();if(navigation!==navigationEpoch)return;
   disposed=true;
   for(const frame of [...$('#roomFrames').children]){
    if(currentView==='analysis'&&(view||'analysis')==='analysis'&&frame.id==='workflowFrame'){
     departure=frame;frame.id='departingWorkflowFrame';frame.dataset.branchDeparture='true';frame.inert=true;
     frame.contentWindow.postMessage({type:'sceneforge:workflow-pause'},location.origin);
    }else frame.remove();
   }
   frameRoom=id;
  }
  if(navigation!==navigationEpoch)return;
  currentRoom=room;prefs.lastRoom=id;await savePrefs();if(navigation!==navigationEpoch)return;
  await showView(view||(['editing','exported'].includes(room.stage)?'editor':'analysis'),true);
  await yieldNavigationPaint();
 }catch(e){
  if(disposed&&navigation===navigationEpoch&&previous.room){
   for(const frame of [...$('#roomFrames').children])if(frame!==departure)frame.remove();
   if(departure){departure.id='workflowFrame';delete departure.dataset.branchDeparture;departure.hidden=false;departure.inert=false;departure.setAttribute('aria-hidden','false');restored=true;}
   currentRoom=previous.room;frameRoom=departure?previous.frameRoom:null;prefs.lastRoom=previous.lastRoom;await savePrefs();
   await showView(previous.view,true);
  }
  fail(e);
 }finally{
  if(departure&&!restored)departure.remove();switching=false;document.body.classList.remove('branchSwitching');
  if(navigation===navigationEpoch)$('#roomLoading').hidden=true;
 }
}
