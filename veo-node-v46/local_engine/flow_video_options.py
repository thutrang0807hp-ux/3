"""Supported single-video settings shared by admission, CLI and result validation."""
DEFAULTS={'kind':'video','mode':'ingredients','ratio':'9:16','model':'lite','outputs':1}
MODELS={'lite':'veo-lite','fast':'veo-fast','quality':'veo-quality'}

def normalize_settings(value=None):
    if value is not None and not isinstance(value,dict):raise ValueError('Cấu hình phải là một đối tượng.')
    cfg=dict(DEFAULTS if value is None else value)
    if set(cfg)!=set(DEFAULTS) or cfg['kind']!='video' or cfg['mode'] not in ('ingredients','frames') or cfg['ratio'] not in ('9:16','16:9') or cfg['model'] not in MODELS or type(cfg['outputs']) is not int or cfg['outputs']!=1:
        raise ValueError('Cấu hình chưa hỗ trợ; cần một video, tỉ lệ 9:16 hoặc 16:9 và model Veo hợp lệ.')
    if cfg['mode']=='ingredients' and cfg['model']=='quality':
        raise ValueError('Veo Quality không hỗ trợ Ingredients; chọn Khung hình hoặc model Lite/Fast.')
    return cfg

def model_id(settings):
    cfg=normalize_settings(settings)
    return 'veo-3.1-'+cfg['model']+'-i2v-8s-'+('portrait' if cfg['ratio']=='9:16' else 'landscape')

def request_settings(payload):
    return normalize_settings(payload.get('settings') or payload.get('generation_settings'))
