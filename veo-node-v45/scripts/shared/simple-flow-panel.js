/* Compatibility for older toolbars: all Flow login belongs to Accounts. */
(()=>{
async function open(){
 try{if(parent!==window&&parent.SceneForgeApp?.accounts?.open)return parent.SceneForgeApp.accounts.open('flow');}catch{}
 if(window.SceneForgeApp?.accounts?.open)return window.SceneForgeApp.accounts.open('flow');
 if(typeof accountScreen==='function')return accountScreen('flow');
 if(typeof storeProject==='function')await storeProject();
 location.assign('/?accounts=flow');
}
window.SFSimpleFlow={open,close(){}};
})();
