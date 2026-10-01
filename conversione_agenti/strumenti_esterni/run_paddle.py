import time
from pathlib import Path
from paddleocr import PaddleOCRVL
p = PaddleOCRVL(vl_rec_backend="llama-cpp-server", vl_rec_server_url="http://127.0.0.1:8111/v1",
                vl_rec_api_model_name="PaddleOCR-VL-1.6-0.9B", device="cpu")
out = Path('out_paddle'); out.mkdir(exist_ok=True)
for f in sorted(Path('pagine').glob('*.pdf')):
    t = time.time(); d = out / f.stem; d.mkdir(exist_ok=True)
    for res in p.predict(str(f)):
        res.save_to_markdown(save_path=str(d))
    print(f.stem, round(time.time() - t, 1), flush=True)
