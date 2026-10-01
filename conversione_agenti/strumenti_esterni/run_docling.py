import sys,os,time
from pathlib import Path
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import ImageRefMode
o=PdfPipelineOptions(); o.generate_picture_images=True; o.images_scale=2.0
c=DocumentConverter(format_options={InputFormat.PDF:PdfFormatOption(pipeline_options=o)})
out=Path('out_docling'); out.mkdir(exist_ok=True)
for f in sorted(Path('pagine').glob('*.pdf')):
    t=time.time(); r=c.convert(f); d=out/f.stem; d.mkdir(exist_ok=True)
    r.document.save_as_markdown(d/f'{f.stem}.md', image_mode=ImageRefMode.REFERENCED)
    print(f.stem, round(time.time()-t,1), flush=True)
