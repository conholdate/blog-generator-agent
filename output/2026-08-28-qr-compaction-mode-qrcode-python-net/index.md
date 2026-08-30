---
title: QR Compaction Mode QREncodeMode.EXTENDED in python-net
seoTitle: QR Compaction Mode QREncodeMode.EXTENDED in python-net - Aspose.BarCode
  Tutorial
description: Learn how to control QR compaction mode with QREncodeMode.EXTENDED in
  python-net using Aspose.BarCode. Step‑by‑step guide with code and decoding.
date: Fri, 28 Aug 2026 05:11:21 +0000
draft: true
url: /barcode/qr-compaction-mode-qrcode-python-net/
author: Muzammil Khan
summary: This article shows how to enable precise QR compaction control by using QREncodeMode.EXTENDED
  in Aspose.BarCode for python‑net. You will install the SDK, generate a QR code with
  explicit mode selectors, and decode it to verify the result.
tags: ['qr compaction mode qrencodemodeextended in python-net', 'set qrencodemode to extended for qr compaction in python-net', 'extended qr compaction mode qrencodemode in python-net', 'use qrencodemodeextended for qr compaction in python-net']
categories: ["Aspose.BarCode Product Family"]
showtoc: true
cover:
  image: images/qr-compaction-mode-qrcode-python-net.jpg
  alt: QR Compaction Mode QREncodeMode.EXTENDED in python-net
  caption: QR Compaction Mode QREncodeMode.EXTENDED in python-net
  hidden: false
steps:
- Install Aspose.BarCode for Python via pip using "pip install aspose-barcode".
- Import the required classes and set the QR encode mode to QREncodeMode.EXTENDED.
- Create a codetext string that includes explicit compaction selectors (\auto, \num,
  \alnum, \byte, \kanji).
- Generate the QR code image and save it to disk.
- Read the saved QR image with BarCodeReader to verify the encoded data.
faqs:
- q: What does QREncodeMode.EXTENDED do?
  a: It enables the QR generator to read explicit compaction selectors inside the
    codetext, letting you force numeric, alphanumeric, byte, kanji or automatic encoding
    for each segment.
- q: Do I need a paid license to use QREncodeMode.EXTENDED?
  a: A free temporary license can be obtained from Aspose; full functionality, including
    EXTENDED mode, works with that license during evaluation.
- q: Can I mix different selectors in a single QR code?
  a: Yes. The codetext can contain multiple selectors (e.g., \num followed by \alnum)
    and the generator will apply the corresponding compaction for each part.
- q: Is the generated QR code compatible with standard QR readers?
  a: Absolutely. The QR spec defines these compaction modes, so any compliant scanner
    will decode the data correctly.
- q: How can I verify which compaction mode was used for each segment?
  a: Read the QR code with BarCodeReader and inspect the returned CodeText; the selector
    strings are stripped out, confirming that the data was encoded as intended.
- q: What version of Aspose.BarCode for python‑net supports QREncodeMode.EXTENDED?
  a: Support was added in Aspose.BarCode for Python via .NET 26.6.
---

Aspose.BarCode for python‑net now lets you dictate the exact QR compaction mode by using **QREncodeMode.EXTENDED**.  This tutorial walks you through installing the SDK, creating a QR code with explicit numeric, alphanumeric, byte, kanji and automatic selectors, and finally decoding the QR to ensure the data was encoded exactly as you intended.  By the end of the guide you will understand how to harness this new feature to optimise QR size and improve scan reliability.

## Why This Feature Matters

QR codes can store a lot of data, but the amount of space they occupy depends heavily on the compaction mode chosen for each segment of the payload.  The default automatic mode works well for most scenarios, yet there are cases where you know the data type in advance (for example, a long numeric identifier or a block of Japanese kanji).  Selecting the optimal compaction manually reduces the QR version, making the symbol smaller and easier to scan on low‑resolution cameras.  **QREncodeMode.EXTENDED** gives developers that fine‑grained control directly in the codetext string, eliminating the need for post‑processing or external libraries.

## API Introduction

Aspose.BarCode for python‑net provides a rich set of classes for barcode generation and recognition.  The primary classes used in this tutorial are:

- `BarcodeGenerator` – creates barcodes, including QR codes.
- `EncodeTypes` – enumeration of supported barcode symbologies; we will use `EncodeTypes.QR`.
- `QREncodeMode` – controls QR compaction; the new `EXTENDED` value parses explicit selectors.
- `BarCodeReader` – reads barcodes from images and returns the decoded text.
- `DecodeType` – specifies the type of barcode to decode; we will use `DecodeType.QR`.

To start, install the package via pip (skip this step if the SDK is already installed):

```bash
pip install aspose-barcode
```

You can find more details on the product page at https://products.aspose.com/barcode/python-net/ and explore the full API reference at https://reference.aspose.com/barcode/python-net/.

## 1. Install and Prepare the Development Environment

1. Open a terminal or command prompt.
2. Run the pip install command shown above.
3. Verify the installation by importing the package in a Python REPL.
4. (Optional) Obtain a free temporary license from https://purchase.aspose.com/temporary-license/ and apply it before generating any barcodes.

The following snippet shows a quick import check:

The following example shows how to import the necessary classes and confirm that the package is available using Python.
```python
import aspose.barcode
print("Aspose.BarCode version:", aspose.barcode.__version__)
```

Running this script will print the installed version, confirming that the SDK is ready for use.

## 2. Generate a QR Code Using QREncodeMode.EXTENDED

This section demonstrates the core workflow: creating a QR code where the codetext contains explicit compaction selectors.  The selectors are prefixed with a backslash (e.g., `\num`, `\alnum`, `\byte`, `\kanji`, `\auto`).  When `QREncodeMode.EXTENDED` is active, the generator interprets these markers and applies the corresponding mode to the following characters until the next selector appears.

1. Import the generation classes.
2. Build a codetext string that mixes numeric, alphanumeric, byte and kanji segments.
3. Instantiate `BarcodeGenerator` with `EncodeTypes.QR` and the composed codetext.
4. Set the QR encode mode to `QREncodeMode.EXTENDED`.
5. Save the resulting image to disk.

The following example shows how to implement these steps in Python.  It is reproduced from the official release notes and has not been executed in a sandbox; verify it in your own environment before using it in production.
```python
from aspose.barcode.generation import BarcodeGenerator, EncodeTypes, QREncodeMode

# Compose a Codetext with Explicit Selectors for Each Segment.
# \Num   – Numeric Mode
# \Alnum – Alphanumeric Mode
# \Byte  – Byte Mode (UTF‑8)
# \Kanji – Kanji Mode (Shift‑JIS)
# \Auto  – Switch Back to Automatic Mode
codetext = (
    "\\num1234567890"            # numeric segment
    "\\alnumASPOSE2026"          # alphanumeric segment
    "\\byteaspose2026"           # byte segment (UTF‑8)
    "\\kanji\u3062\u3063\u3064\u3065\u3066\u3067\u3068\u3069\u306A"  # kanji segment
    "\\auto"                    # return to automatic mode for any trailing data
)

# Create the QR Generator with the Combined Codetext.
generator = BarcodeGenerator(EncodeTypes.QR, codetext)

# Enable the Extended Mode So the Selector Strings Are Processed.
generator.parameters.barcode.qr.encode_mode = QREncodeMode.EXTENDED

# Save the QR Code as a PNG File.
generator.save("extended_qr.png")

print("QR code generated and saved as extended_qr.png")
```

**Explanation of the code**:

- `codetext` concatenates several substractive segments, each prefixed with a selector.  The backslash must be escaped in the Python string, hence the double backslashes.
- `BarcodeGenerator` receives the QR symbology and the full codetext.
- Setting `generator.parameters.barcode.qr.encode_mode` to `QREncodeMode.EXTENDED` tells the engine to interpret the selectors.
- `save` writes the generated QR image to the file system.  The resulting QR will be smaller than a fully automatic QR containing the same raw data, because numeric and kanji portions are compressed using their optimal modes.

## 3. Decode the QR Code and Verify the Compaction

After generating the QR code, you may want to confirm that the data was encoded correctly.  The `BarCodeReader` class can read QR symbols from an image file and return the decoded text without the selector markers.  This step ensures that the QR is readable by standard scanners and that the selectors did not become part of the data payload.

1. Import the recognition classes.
2. Create a `BarCodeReader` instance pointing to the saved image.
3. Specify `DecodeType.QR` to limit the scan to QR symbols.
4. Iterate through the results and print the decoded `code_text`.

The following example demonstrates decoding the QR code we just generated.  It is reproduced from the official release notes and has not been sandbox‑tested; please verify it before deploying.
```python
from aspose.barcode.barcoderecognition import BarCodeReader, DecodeType

# Initialise the Reader with the Image Path and QR Decode Type.
reader = BarCodeReader("extended_qr.png", DecodeType.QR)

# Iterate Over All Detected QR Symbols (Usually Just One).
for result in reader.read_bar_codes():
    print("BarCode CodeText: " + result.code_text)
```

**Explanation of the code**:

- `BarCodeReader` is constructed with the file name and a hint that we are interested in QR symbols only.
- `read_bar_codes()` returns an iterator of `BarCodeResult` objects.  Each result contains a `code_text` property that holds the decoded payload.
- The printed output will **not** include any of the selector prefixes (`\num`, `\alnum`, etc.) because those markers are processed only during generation.  The output should therefore be the concatenation of the raw data segments (`1234567890ASPOSE2026aspose2026<kanji characters>`), confirming that the QR is valid and the compaction was applied.

## Get a Free License

If you are evaluating Aspose.BarCode, you can obtain a temporary license at https://purchase.aspose.com/temporary-license/.  Apply the license before generating or reading barcodes to lift any evaluation restrictions.

## Free Additional Resources

- **Documentation** – https://docs.aspose.com/barcode/python-net/
- **API Reference** – https://reference.aspose.com/barcode/python-net/
- **Online Barcode Generator** – https://products.aspose.app/barcode/family

## Conclusion

By leveraging **QREncodeMode.EXTENDED** in python‑net, you gain precise control over QR compaction, allowing you to shrink QR symbols and improve scan reliability.  The tutorial walked you through installing the SDK, composing a codetext with explicit numeric, alphanumeric, byte and kanji selectors, generating the QR image, and finally decoding it to verify that the data matches expectations.  Remember to test the sample in your own environment and apply a valid license for production use.

## FAQs

1. **What does QREncodeMode.EXTENDED do?**
   It enables the QR generator to read explicit compaction selectors inside the codetext, letting you force numeric, alphanumeric, byte, kanji or automatic encoding for each segment.

2. **Do I need a paid license to use QREncodeMode.EXTENDED?**
   A free temporary license can be obtained from Aspose; full functionality, including EXTENDED mode, works with that license during evaluation.

3. **Can I mix different selectors in a single QR code?**
   Yes. The codetext can contain multiple selectors (e.g., \num followed by \alnum) and the generator will apply the corresponding compaction for each part.

4. **Is the generated QR code compatible with standard QR readers?**
   Absolutely. The QR spec defines these compaction modes, so any compliant scanner will decode the data correctly.

5. **How can I verify which compaction mode was used for each segment?**
   Read the QR code with BarCodeReader and inspect the returned CodeText; the selector strings are stripped out, confirming that the data was encoded as intended.

6. **What version of Aspose.BarCode for python‑net supports QREncodeMode.EXTENDED?**
   Support was added in Aspose.BarCode for Python via .NET 26.6.

## Read More

- [Generate MaxiCode Barcode in Python](https://blog.aspose.com/barcode/generate-maxicode-barcode-in-python/)
- [Build Code 93 Barcode Generator in Python](https://blog.aspose.com/barcode/build-code-93-barcode-generator-in-python/)
- [Generate Barcode and QR Code with Logo in Python](https://blog.aspose.com/barcode/generate-barcode-and-qr-code-with-logo-in-python/)

