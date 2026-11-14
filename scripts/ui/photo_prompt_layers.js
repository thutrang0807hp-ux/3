/* Opt-in rollout for existing photo rooms: no silent rewriting of approved work. */
(()=>{
 const enabled=()=>draft.storyboardLook?.layered===true;
 const still='LAYERED PHOTO DIRECTIONS v1: Use only the attached role references. Identity is separate from wardrobe, product geometry and background; do not blend faces or clothing. Bind these roles to the actual supplied reference map, never assume that the first reference is source composition. Preserve visible face structure, skin tone, garment construction, colors and genuine product labels. Describe one feasible static moment: body orientation, gaze, hand ownership, grip and object scale/occlusion. Follow the authored shot and shared look. Match light direction, softness, shadows and reflections; request natural skin/fabric/material texture and low-noise resolved detail without waxy smoothing or sharpening halos. Do not add studio light, props or a lens brand without intent/evidence. Do not invent hidden product details, benefits or text. Keep authentic packaging lettering while excluding added overlays. The overview is planning evidence, never a collage to animate. Resolution is a generator setting, not enabled by writing 4K.';
 const motion='LAYERED MOTION DIRECTIONS v1: Preserve exact beat/part IDs, dialogue and durations. The actual per-clip start image, when present, defines the initial appearance and state; an end image defines the target state, not another character. Describe initial -> action -> final, separating camera motion from subject/object motion. Keep visible wardrobe, facial identity, product construction, hand contact and object orientation stable through motion. Use clip-relative timing only when supported by the scene plan. Do not squeeze neighboring scene actions into this clip or repeat an action already completed in the start frame. Original product references define product truth, never unsupported new claims. Preserve compatible manual composition and movement. Output English production directions in the existing schema; do not translate dialogue, change speech timing or introduce music/subtitles.';
 const settings=SFStoryboardGuide.settings;
 SFStoryboardGuide.settings=function(value){const out=settings(value);if(value?.layered===true)out.layered=true;return out;};
 const image=SFStoryboardGuide.imagePrompt;
 SFStoryboardGuide.imagePrompt=function(text,data){const original=image(text,data);return enabled()?original+'\n'+still:original;};
 const writing=photoWritingPrompt;
 photoWritingPrompt=function(batch){const original=writing(batch);if(!enabled())return original;const at=original.indexOf('\n'),data=JSON.parse(original.slice(at+1));data.promptLayers={version:1,identityPolicy:'assigned-role references',qualityPolicy:'grounded visible detail; no resolution promise'};return original.slice(0,at)+' '+still+' '+motion+'\n'+JSON.stringify(data);};
 const initial=newDraft;
 newDraft=function(...args){const d=initial(...args);d.storyboardLook={...d.storyboardLook,layered:true};return d;};
 const node=storyboardNode;
 storyboardNode=function(...args){const t=document.createElement('template');t.innerHTML=node(...args);const box=t.content.querySelector('.sbSharedLook');if(box){const row=document.createElement('label');row.style.cssText='display:flex;align-items:center;gap:8px;margin:10px 0';row.innerHTML='<input type="checkbox" data-photo-prompt-layers '+(enabled()?'checked':'')+'> Prompt phân tầng · giữ người & chi tiết đồ';box.append(row);}return t.innerHTML;};
 document.addEventListener('change',async e=>{
  if(!e.target.matches('[data-photo-prompt-layers]'))return;
  try{
   if(photoToolbar.busy||photoMediaBusy||photoProductionWorking||SFStoryboard.isBusy()||window.SFPhotoPromptPipeline?.isRunning())throw Error('Đợi lượt hiện tại xong rồi đổi cách viết prompt.');
   draft.storyboardLook={...draft.storyboardLook,layered:e.target.checked};
   photoMarkPromptDirty(draft.beats.map(b=>b.id),'Cách viết prompt phân tầng đã đổi');
   await save();render();toast('Đã lưu. Giữ ảnh/clip cũ; chưa gửi tạo mới.');
  }catch(err){toast(err.message);render();}
 });
 window.SFPhotoPromptLayers={enabled,still,motion};
})();
