---
title: QR Compaction Modes in python-net with QrExtCodetextBuilder
seoTitle: QR Compaction Modes in python-net with QrExtCodetextBuilder
description: Learn how to use QR Compaction Modes in python-net with QrExtCodetextBuilder
  to control data encoding, generate extended QR barcodes, and verify them using Aspose.BarCode
  for Python.
date: Fri, 28 Aug 2026 05:06:58 +0000
draft: true
url: /barcode/qr-compaction-modes-python-net/
author: Muzammil Khan
summary: This article shows how to select explicit QR compaction modes with QrExtCodetextBuilder,
  generate an EXTENDED QR barcode, and read it back using Aspose.BarCode for Python
  via .NET.
tags: ['qr compaction modes in python-net with qrextcodetextbuilder', 'qr code library in python-net', 'barcode generation and recognition via python-net', 'set qr compaction mode qrextcodetextbuilder in python-net']
categories: ["Aspose.BarCode Product Family"]
showtoc: true
cover:
  image: images/qr-compaction-modes-python-net.jpg
  alt: QR Compaction Modes in python-net with QrExtCodetextBuilder
  caption: QR Compaction Modes in python-net with QrExtCodetextBuilder
  hidden: false
steps:
- Install Aspose.BarCode for Python via pip.
- Import the required Aspose.BarCode classes and create a QrExtCodetextBuilder.
- Add data segments with explicit compaction modes using QrExtCompactionMode.
- Generate the QR barcode in EXTENDED mode and save the image.
- Read the saved QR barcode to verify the encoded text.
faqs:
- q: What is a QR compaction mode and why would I use it?
  a: Compaction mode tells the QR encoder how to treat a segment of data—numeric,
    alphanumeric, byte, or Kanji—optimizing size and error correction for that specific
    content.
- q: Which compaction modes does QrExtCompactionMode support?
  a: QrExtCompactionMode provides NUMERIC, ALPHA_NUMERIC, BYTES, and KANJI, matching
    the four QR data modes defined in the ISO/IEC 18004 specification.
- q: How does the EXTENDED encode mode differ from the standard QR encode mode?
  a: EXTENDED mode lets you combine multiple data segments, each with its own compaction
    mode, inside a single QR symbol, giving fine‑grained control over encoding efficiency.
- q: Can I mix different compaction modes in one QR code?
  a: Yes. By using QrExtCodetextBuilder you can add several segments, each with a
    different QrExtCompactionMode, and the builder will produce a single extended
    QR code.
- q: Do I need a license to use QrExtCodetextBuilder?
  a: A temporary license is required for evaluation; production use requires a full
    Aspose.BarCode license. You can obtain a free temporary license from the Aspose
    website.
- q: Is there a limit on how much data I can put in a single segment?
  a: The limit depends on the QR version and error correction level you select. Each
    compaction mode has its own capacity rules defined by the QR standard.
---

Aspose.BarCode for Python via .NET now lets developers pick a specific QR compaction mode for each data segment through the **QrExtCodetextBuilder** class. By explicitly selecting a mode—numeric, alphanumeric, byte, or Kanji—you gain tighter control over barcode size and readability, especially when dealing with mixed‑type payloads. This post walks through the entire workflow: configuring compaction modes, generating an EXTENDED QR barcode, and reading the result back, all with Python.

## Why This Feature Matters
When generating QR codes that contain heterogeneous data (for example, a numeric ID followed by an alphanumeric product code and a block of UTF‑8 text), the default automatic mode selection can produce larger symbols than necessary. Each compaction mode has a different data density: numeric mode stores three digits per 10 bits, alphanumeric stores two characters per 11 bits, byte mode stores 8 bits per character, and Kanji mode stores 13 bits per character. By telling the encoder which mode to use for each segment, you reduce the overall symbol size, improve scan reliability, and keep the QR version as low as possible. This is especially valuable for mobile apps, printed media, or any scenario where space is at a premium.

## Brief Introduction to Aspose.BarCode for Python
Aspose.BarCode for Python via .NET is a cross‑platform library that supports barcode generation, recognition, and manipulation for over 50 symbologies, including QR codes. Install the package via pip:

```bash
pip install aspose-barcode
```

Once installed, you can start using the API. For more information, visit the [product page](https://products.aspose.com/barcode/python-net/). The official documentation and API reference are also available at the links provided later in this article.

## Configure QR Compaction Modes
In this section we’ll build a **QrExtCodetextBuilder** instance and add four data segments, each with a distinct compaction mode. The builder then produces an extended‑mode code text that can be fed directly to the QR generator.

1. Import the required classes from the Aspose.BarCode namespace.
2. Create a **QrExtCodetextBuilder** object.
3. Add a numeric segment using `QrExtCompactionMode.NUMERIC`.
4. Add an alphanumeric segment using `QrExtCompactionMode.ALPHA_NUMERIC`.
5. Add a byte‑oriented segment using `QrExtCompactionMode.BYTES`.
6. Add a Kanji segment using `QrExtCompactionMode.KANJI`.
7. Retrieve the combined extended code text.

The following example demonstrates how to configure each segment using Python:

```python
from aspose.barcode.barcoderecognition import BarCodeReader, DecodeType
from aspose.barcode.generation import (
    BarcodeGenerator,
    EncodeTypes,
    QREncodeMode,
    QrExtCodetextBuilder,
    QrExtCompactionMode,
)

# Step 2: Instantiate the Builder
text_builder = QrExtCodetextBuilder()

# Step 3: Add a Numeric Segment (E.g., a Simple ID)
text_builder.add_codetext_with_compaction_mode(QrExtCompactionMode.NUMERIC, "1234567")

# Step 4: Add an Alphanumeric Segment (E.g., a Product Code)
text_builder.add_codetext_with_compaction_mode(QrExtCompactionMode.ALPHA_NUMERIC, "ASPOSE2026")

# Step 5: Add a Byte‑oriented Segment (E.g., UTF‑8 Text)
text_builder.add_codetext_with_compaction_mode(QrExtCompactionMode.BYTES, "aspose2026")

# Step 6: Add a Kanji Segment (Japanese Characters Encoded in Shift‑JIS)
text_builder.add_codetext_with_compaction_mode(QrExtCompactionMode.KANJI, "\u3062\u3063\u3064\u3065\u3066\u3067\u3068\u3069\u306A")

# Step 7: Retrieve the Final Extended Code Text
codetext = text_builder.get_extended_codetext()
```

**Explanation**:
- The `QrExtCodetextBuilder` holds an internal list of segments. Each call to `add_codetext_with_compaction_mode` appends a new segment together with the chosen mode.
- Numeric mode (`NUMERIC`) packs three digits into ten bits, making it the most space‑efficient for pure numbers.
- Alphanumeric mode (`ALPHA_NUMERIC`) handles characters from the QR alphanumeric set (0‑9, A‑Z, space, $%*+‑./:). It stores two characters per eleven bits.
- Byte mode (`BYTES`) stores raw 8‑bit bytes, suitable for UTF‑8 strings or binary data.
- Kanji mode (`KANJI`) expects Shift‑JIS‑encoded characters, storing each two‑byte character in thirteen bits.
- The `get_extended_codetext()` method concatenates the segments into the special EXTENDED format that the QR generator understands.

By explicitly setting each segment’s mode, you steer the encoder toward the most compact representation for the given data.

## Generate QR Barcode in Extended Mode
Now that we have an extended code text, we can generate the QR barcode. The generator must be instructed to use **EXTENDED** encode mode; otherwise it would treat the whole string as a single segment, ignoring the per‑segment mode hints.

1. Create a `BarcodeGenerator` instance with `EncodeTypes.QR` and the extended code text.
2. Set the QR encode mode to `QREncodeMode.EXTENDED`.
3. Optionally configure error correction level, module size, or margin.
4. Save the barcode to a PNG file.

The following snippet shows the complete generation step:

```python
# Create the QR Generator with the Extended Code Text
gen = BarcodeGenerator(EncodeTypes.QR, codetext)

# Switch to EXTENDED Mode So the Builder's Segment Information Is Respected
gen.parameters.barcode.qr.encode_mode = QREncodeMode.EXTENDED

# Save the Generated QR Code as an Image
gen.save("test.png")
```

**Explanation**:
- `BarcodeGenerator` is the central class for barcode creation. Passing `EncodeTypes.QR` tells the engine to produce a QR symbol.
- The `qr.encode_mode` property determines how the QR library interprets the supplied text. Setting it to `EXTENDED` makes the engine read the data as a series of pre‑defined segments rather than attempting automatic mode detection.
- The `save` method writes the barcode to a file; you can also obtain a stream or a Pillow image object if you need further processing.

At this point you have a QR image (`test.png`) that carries four distinct data segments, each encoded with its optimal compaction mode. Scanners that support the QR standard will automatically decode the mixed‑mode payload and return the original concatenated string.

## Read and Verify the Generated QR Barcode
Verification is a crucial step during development, ensuring that the barcode you generated matches the intended payload. Aspose.BarCode provides a straightforward API for reading QR codes from images.

1. Initialise a `BarCodeReader` with the file path and specify `DecodeType.QR`.
2. Iterate through the returned results (a QR code may contain multiple symbols, though in our case there is only one).
3. Print or otherwise handle the `code_text` property, which contains the concatenated decoded string.

Below is a minimal example that reads the barcode we just created:

```python
# Initialise the QR Code Reader
reader = BarCodeReader("test.png", DecodeType.QR)

# Iterate Through All Detected QR Codes (Usually Just One)
for result in reader.read_bar_codes():
    print("BarCode CodeText: " + result.code_text)
```

**Explanation**:
- `BarCodeReader` opens the image and looks for QR symbols. The second argument, `DecodeType.QR`, restricts the scan to QR codes only, speeding up detection.
- `read_bar_codes()` returns an iterable of `BarCodeResult` objects. Each result exposes `code_text`, which is the raw string after the library has merged all segments.
- The printed output should be the exact concatenation of the four segments we added earlier: `1234567ASPOSE2026aspose2026<kanji characters>`.

If the output matches the expected string, the entire pipeline—from compaction mode selection to barcode generation and decoding—is working correctly.

> **Note**: This code sample is reproduced from the official Aspose release notes and has not been executed in a sandbox. Verify it in your own environment before using it in production.

## Get a Free License
To evaluate Aspose.BarCode for Python you can obtain a temporary license that removes evaluation watermarks and enables full API functionality. Request one from the Aspose temporary‑license page: <https://purchase.aspose.com/temporary-license/>.

## Free Additional Resources
- [Product Documentation](https://docs.aspose.com/barcode/python-net/)
- [API Reference](https://reference.aspose.com/barcode/python-net/)
- [Free Online Barcode Generator App](https://products.aspose.app/barcode/family)

## Conclusion
By leveraging **QrExtCodetextBuilder** and the **QrExtCompactionMode** enumeration, developers can fine‑tune QR code generation for mixed data types, reducing symbol size and improving scan reliability. The workflow demonstrated here—building an extended code text, generating a QR barcode in EXTENDED mode, and reading it back—covers the entire life‑cycle of a compact, multi‑segment QR symbol in Python. Apply this technique wherever you need optimal QR encoding, such as inventory tags, mobile payments, or embedded device provisioning.

## FAQs
1. **What is a QR compaction mode and why would I use it?**
   Compaction mode tells the QR encoder how to treat a segment of data—numeric, alphanumeric, byte, or Kanji—optimizing size and error correction for that specific content.

2. **Which compaction modes does QrExtCompactionMode support?**
   QrExtCompactionMode provides NUMERIC, ALPHA_NUMERIC, BYTES, and KANJI, matching the four QR data modes defined in the ISO/IEC 18004 specification.

3. **How does the EXTENDED encode mode differ from the standard QR encode mode?**
   EXTENDED mode lets you combine multiple data segments, each with its own compaction mode, inside a single QR symbol, giving fine‑grained control over encoding efficiency.

4. **Can I mix different compaction modes in one QR code?**
   Yes. By using QrExtCodetextBuilder you can add several segments, each with a different QrExtCompactionMode, and the builder will produce a single extended QR code.

5. **Do I need a license to use QrExtCodetextBuilder?**
   A temporary license is required for evaluation; production use requires a full Aspose.BarCode license. You can obtain a free temporary license from the Aspose website.

6. **Is there a limit on how much data I can put in a single segment?**
   The limit depends on the QR version and error correction level you select. Each compaction mode has its own capacity rules defined by the QR standard.

## Read More

- [Generate MaxiCode Barcode in Python](https://blog.aspose.com/barcode/generate-maxicode-barcode-in-python/)
- [Build Code 93 Barcode Generator in Python](https://blog.aspose.com/barcode/build-code-93-barcode-generator-in-python/)
- [Generate Barcode and QR Code with Logo in Python](https://blog.aspose.com/barcode/generate-barcode-and-qr-code-with-logo-in-python/)

