"""Supported single-video settings shared by admission, CLI and result validation."""
DEFAULTS={'kind':'video','mode':'ingredients','ratio':'9:16','model':'lite','outputs':1}
MODELS={'lite':'veo-lite','fast':'veo-fast','quality':'veo-quality','omni-1.2-flash':'omni-1.2-flash'}

def normalize_settings(value=None):
    if value is not None and not isinstance(value,dict):raise ValueError('Cấu hình phải là một đối tượng.')
    cfg=dict(DEFAULTS if value is None else value)
    if set(cfg)!=set(DEFAULTS) or cfg['kind']!='video' or cfg['mode'] not in ('ingredients','frames') or cfg['ratio'] not in ('9:16','16:9') or cfg['model'] not in MODELS or type(cfg['outputs']) is not int or cfg['outputs']!=1:
        raise ValueError('Cấu hình chưa hỗ trợ; cần một video, tỉ lệ 9:16 hoặc 16:9 và model hợp lệ.')
    if cfg['mode']=='ingredients' and cfg['model']=='quality':
        raise ValueError('Veo Quality không hỗ trợ Ingredients; chọn Khung hình hoặc model Lite/Fast.')
    return cfg

def model_id(settings):
    cfg=normalize_settings(settings)
    return (cfg['model'] if cfg['model']=='omni-1.2-flash' else 'veo-3.1-'+cfg['model'])+'-i2v-8s-'+('portrait' if cfg['ratio']=='9:16' else 'landscape')

def request_settings(payload):
    return normalize_settings(payload.get('settings') or payload.get('generation_settings'))


def catalog():
    """Declared single-clip routes; availability is still checked by Flow on send."""
    return [dict(id=model_id(dict(DEFAULTS,model=model,ratio=ratio,mode='frames')),
                 description=('Omni 1.2 Flash' if model=='omni-1.2-flash' else 'Veo 3.1 '+model.title())+' · 8s · '+ratio,
                 accepts_images=True,video_type='i2v',max_images=1)
            for model in ('omni-1.2-flash','lite','fast','quality') for ratio in ('9:16','16:9')]
