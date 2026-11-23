/* Only announce the local SceneForge origin; never read project content. */
(()=>{if(window.top!==window)return;function announce(){if(!document.title.startsWith('SceneForge'))return;chrome.runtime.sendMessage({type:'sceneforge-auto-discover'}).catch(()=>{});}announce();document.addEventListener('DOMContentLoaded',announce,{once:true});})();
