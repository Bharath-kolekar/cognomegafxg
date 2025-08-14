import os
os.environ['COQUI_TOS_AGREED'] = '1'
os.environ['HF_HOME'] = r'C:\cognomegafx_full_max\backend\.xtts_cache'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

from TTS.api import TTS

tts = TTS(model_name='tts_models/multilingual/multi-dataset/xtts_v2')
tts.tts_to_file(
    text='warming up the model',
    speaker_wav=r'C:\voices\me.wav',
    language='en',         # <-- REQUIRED for XTTS v2
    file_path='warmup.wav'
)
print('XTTS warmup OK')
