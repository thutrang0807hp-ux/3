/* Small authoring options; no model, dependency or automatic requests. */
(()=>{
 const options=[['general','Theo ý tưởng của bạn'],['intro','Quảng cáo / giới thiệu'],['problem_solution','Vấn đề → giải pháp'],['demo','Hướng dẫn sử dụng'],['review','Review / tư vấn'],['story','Kể chuyện'],['offer','Ưu đãi / chốt đơn']];
 window.SFScriptKinds={options,label:id=>options.find(x=>x[0]===id)?.[1]||options[0][1]};
})();
