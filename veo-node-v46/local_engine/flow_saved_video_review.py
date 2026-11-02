"""explicit user acknowledgement unlocks NEW requests, never retries old ones."""
import time
from fastapi import HTTPException

async def acknowledge_saved_video(service,rid,body):
    service.valid_id(rid)
    if body.get('confirm_saved_video') is not True or body.get('allow_new_generation') is not True:
        raise HTTPException(400,'Cần xác nhận đã giữ video cũ và cho phép lượt mới.')
    async with service.gate:
        if service.busy():raise HTTPException(409,'Lượt đang chạy; chưa mở khóa bằng xác nhận này.')
        record=service.lookup(rid);meta=service.ledger.metadata(rid)
        if record['state']!='unknown':raise HTTPException(409,'Chỉ áp dụng cho lượt chưa rõ kết quả.')
        if body.get('store_id')!=service.ledger.store_id or body.get('room_id')!=meta.get('room_id'):
            raise HTTPException(409,'Kho dữ liệu hoặc phòng không khớp lượt cũ.')
        if not service.account_bridge:raise HTTPException(409,'Chọn đúng tài khoản đã gửi video.')
        selection=service.account_bridge.selection()
        if not selection['available'] or selection['account_id']!=meta.get('account_id'):
            raise HTTPException(409,'Tài khoản không khớp lượt đã gửi.')
        if meta.get('saved_video_review',{}).get('allow_new_generation') is True:
            return service.lookup(rid)
        review={'request_id':rid,'status':'user_kept_video','allow_new_generation':True,
                'old_request_retry_allowed':False,'confirmed_at':time.time(),
                'account_id':meta['account_id'],'room_id':meta['room_id'],
                'note':'Người dùng xác nhận đã kiểm tra và giữ video cũ trên Flow; app chưa nhận video về. Cho phép tạo lượt mới thủ công.'}
        events=list(meta.get('review_events',[]))[-19:]+[review]
        service.ledger.set_metadata(rid,{'saved_video_review':review,'review_events':events,
            'message':review['note']})
        # No ledger.finish(): unknown/result stay exactly as they were.
        return service.lookup(rid)
