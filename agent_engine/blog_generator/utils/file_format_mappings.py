# file_format_map.py

FILE_FORMAT_MAPPINGS = {
    # Presentations
    "PPTX": "presentation/pptx/",
    "PPT": "presentation/ppt/",
    "PPSX": "presentation/ppsx/",
    "ODP": "presentation/odp/",

    # Word Processing & Markdown
    "MD": "word-processing/md/",
    "Markdown": "word-processing/md/",
    "DOCX": "word-processing/docx/",
    "DOC": "word-processing/doc/",
    "Word": "word-processing/doc/",
    "RTF": "word-processing/rtf/",
    "TXT": "word-processing/txt/",

    # Spreadsheets
    "XLSX": "spreadsheet/xlsx/",
    "XLS": "spreadsheet/xls/",
    "XLSM": "spreadsheet/xlsm/",
    "CSV": "spreadsheet/csv/",
    "ODS": "spreadsheet/ods/",

    # PDF & Fixed Layout
    "PDF": "pdf/",
    "XPS": "page-description-language/xps/",
    "EPUB": "ebook/epub/",

    # Images
    "PNG": "image/png/",
    "JPG": "image/jpeg/",
    "JPEG": "image/jpeg/",
    "TIFF": "image/tiff/",
    "SVG": "image/svg/",
    "BMP": "image/bmp/",

    # Web & Data
    "HTML": "web/html/",
    "JSON": "web/json/",
    "XML": "web/xml/",
    # Visio File Formats
    "VSDX": "visio/vsdx/",
    "VSD": "visio/vsd/",
    "VSSX": "visio/vssx/",
    "VSTX": "visio/vstx/",
    "VSDM": "visio/vsdm/",
    "VSSM": "visio/vssm/",
    "VSTM": "visio/vstm/",
    "VDX": "visio/vdx/",
    "VSX": "visio/vsx/",
    "VTX": "visio/vtx/",

    # 3D File Formats
    "STL": "3d/stl/",
    "OBJ": "3d/obj/",
    "FBX": "3d/fbx/",
    "3DS": "3d/3ds/",
    "GLB": "3d/glb/",
    "GLTF": "3d/gltf/",
    "MA": "3d/ma/",
    "U3D": "3d/u3d/",

    # Video File Formats
    "MP4": "video/mp4/",
    "AVI": "video/avi/",
    "MOV": "video/mov/",
    "WMV": "video/wmv/",
    "MKV": "video/mkv/",
    "MPEG": "video/mpeg/",
    "MPG": "video/mpg/",
    "3GP": "video/3gp/",
    "FLV": "video/flv/",

    # Email File Formats
    "MSG": "email/msg/",
    "PST": "email/pst/",
    "OST": "email/ost/",
    "EML": "email/eml/",
    "EMLX": "email/emlx/",
    "MBOX": "email/mbox/",
    "VCF": "email/vcf/",

    # Audio File Formats
    "MP3": "audio/mp3/",
    "WAV": "audio/wav/",
    "AAC": "audio/aac/",
    "FLAC": "audio/flac/",
    "OGG": "audio/ogg/",
    "M4A": "audio/m4a/",
    "WMA": "audio/wma/",

    # CAD File Formats
    "DWG": "cad/dwg/",
    "DXF": "cad/dxf/",
    "DGN": "cad/dgn/",
    "IFC": "cad/ifc/",
    "STL": "cad/stl/", # Previously added, categorized under CAD

    # Compression / Archive File Formats
    "ZIP": "compression/zip/",
    "RAR": "compression/rar/",
    "7Z": "compression/7z/",
    "TAR": "compression/tar/",
    "GZ": "compression/gz/",
    "BZ2": "compression/bz2/",
    "XZ": "compression/xz/"
}
BASE_URL = "https://docs.fileformat.com/"
