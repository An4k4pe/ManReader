"""Chiamata singola al modello locale (llama-server, API OpenAI) con limiti espliciti.
Ogni chiamata: max_tokens fissato, ragionamento spento, timeout. Restituisce testo,
token generati e secondi, cosi' ogni prova registra anche quanto costa.
"""
import base64, io, json, time, urllib.request
from PIL import Image

URL = 'http://localhost:11435/v1/chat/completions'


def image_part(path, max_side=1024):
    im = Image.open(path).convert('RGBA')
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
    im = bg.convert('RGB'); im.thumbnail((max_side, max_side))
    buf = io.BytesIO(); im.save(buf, 'JPEG', quality=90)
    return {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()}}


def chiedi(prompt, images=(), max_tokens=200, timeout=300, temperature=0.2, system=None, thinking=False):
    content = [image_part(p) for p in images] + [{'type': 'text', 'text': prompt}]
    msgs = ([{'role': 'system', 'content': system}] if system else []) + [{'role': 'user', 'content': content}]
    body = dict(messages=msgs, max_tokens=max_tokens,
                temperature=temperature, chat_template_kwargs={'enable_thinking': thinking})
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    t = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    dt = time.time() - t
    u = r.get('usage', {})
    return r['choices'][0]['message']['content'].strip(), u.get('prompt_tokens'), u.get('completion_tokens'), round(dt, 1), r.get('timings', {})
