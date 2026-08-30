---
title: Encode GS1QR Barcodes with Byte-Mode Separators in python-net
seoTitle: Encode GS1QR Barcodes with Byte-Mode Separators in python-net
description: Learn how to generate GS1QR barcodes with byte‑mode separators using
  Aspose.BarCode for python-net. Step‑by‑step tutorial with code, verification, and
  free resources.
date: Fri, 28 Aug 2026 05:01:50 +0000
draft: true
url: /barcode/gs1qr-byte-mode-separators-python-net/
author: Muzammil Khan
summary: This article shows how to create GS1QR barcodes that include GS1 group separators
  and the '%' character by enabling the byte‑mode option in Aspose.BarCode for python‑net.
  You’ll see a complete generate‑and‑read workflow, how to install the SDK, and where
  to obtain a free license.
tags: ['gs1qr barcodes with byte-mode separators in python-net', 'barcode generation and recognition in python-net', 'qrparametersencodegs1separatorinbytemode', 'barcode for python-net']
categories: ["Aspose.BarCode Product Family"]
showtoc: true
cover:
  image: images/gs1qr-byte-mode-separators-python-net.jpg
  alt: Encode GS1QR Barcodes with Byte-Mode Separators in python-net
  caption: Encode GS1QR Barcodes with Byte-Mode Separators in python-net
  hidden: false
steps:
- Install Aspose.BarCode for Python via .NET using "pip install aspose-barcode".
- Create a BarcodeGenerator instance for the GS1QR format.
- Enable the encode_gs1_separator_in_byte_mode flag on the QR parameters.
- Save the generated barcode image to a file.
- Read the saved image with BarCodeReader to confirm the encoded data.
faqs:
- q: What does the encode_gs1_separator_in_byte_mode option do?
  a: It forces the QR encoder to treat GS1 group separator characters (ASCII 29) and
    the '%' character as raw byte data, allowing them to appear in the barcode payload.
- q: Do I need a special license to use the GS1QR features?
  a: The GS1QR format is available in the standard Aspose.BarCode library. You can
    obtain a temporary free license from the Aspose website to evaluate the feature.
- q: Can I use this feature with other QR code types?
  a: The byte‑mode separator option is specific to the GS1QR EncodeTypes value; other
    QR types ignore it.
- q: Is the generated barcode image lossless?
  a: When you save to PNG (the default) the image is lossless, preserving exact module
    data for reliable reading.
- q: How do I verify that the separator was encoded correctly?
  a: Read the barcode back with BarCodeReader using DecodeType.GS1QR and inspect the
    CodeText; the presence of the group separator character (shown as a control character)
    confirms correct encoding.
- q: Does enabling byte‑mode affect barcode size?
  a: Byte‑mode may increase the number of data bits needed, which can slightly enlarge
    the QR matrix, but the library automatically selects the smallest version that
    fits the data.
---

Generating GS1QR barcodes that contain GS1 group separators or the '%' character has traditionally required low‑level byte manipulation. With Aspose.BarCode for python‑net 26.6, the **encode_gs1_separator_in_byte_mode** option simplifies this task, allowing developers to encode those characters directly in byte mode. This tutorial walks through the full workflow—from installing the SDK to verifying the result—so you can integrate GS1QR barcodes with byte‑mode separators into any Python application.

## Why This Feature Matters

GS1QR barcodes are widely used in supply‑chain, healthcare, and retail to encode structured data such as product IDs, batch numbers, and expiration dates. The GS1 Application Identifier (AI) syntax relies on the Group Separator (ASCII 29) to delimit variable‑length fields. Prior to version 26.6, developers had to manually split the payload or use work‑arounds that could break compliance. By enabling **encode_gs1_separator_in_byte_mode**, the barcode engine treats the separator as raw byte data, preserving the exact GS1 format and ensuring downstream scanners interpret the data correctly. This improves data integrity, reduces code complexity, and shortens time‑to‑market.

## Brief Introduction to the API

Aspose.BarCode for Python via .NET provides a high‑level API for both barcode generation and recognition. The package is installed from PyPI with the following command:

```
pip install aspose-barcode
```

The main classes you’ll interact with are **BarcodeGenerator** (for creating barcodes) and **BarCodeReader** (for decoding them). Both classes live in the `aspose.barcode.generation` and `aspose.barcode.barcoderecognition` namespaces respectively. Detailed documentation is available on the [product page](https://products.aspose.com/barcode/python-net/), the [official docs site](https://docs.aspose.com/barcode/python-net/), and the [API reference](https://reference.aspose.com/barcode/python-net/).

## Generate GS1QR Barcode with Byte‑Mode Separator

### Steps

1. **Import the required namespaces** – `BarcodeGenerator`, `EncodeTypes`, `BarCodeReader`, and `DecodeType`.
2. **Instantiate `BarcodeGenerator`** with `EncodeTypes.GS1QR` and the GS1 payload string. The string uses parentheses to denote AI sections, e.g., `(10)ASPOSE2001(21)ASPOSE2026`.
3. **Enable the byte‑mode separator flag** by setting `gen.parameters.barcode.qr.encode_gs1_separator_in_byte_mode = True`.
4. **Save the barcode image** to a file (PNG is the default format).
5. **Read the generated image** with `BarCodeReader` to confirm that the separator was encoded correctly.

The following example demonstrates these steps using Python:

```python
from aspose.barcode.barcoderecognition import BarCodeReader, DecodeType
from aspose.barcode.generation import BarcodeGenerator, EncodeTypes

# 1. Create a GS1QR Barcode with Sample AI Data
gen = BarcodeGenerator(EncodeTypes.GS1QR, "(10)ASPOSE2001(21)ASPOSE2026")

# 2. Turn on Byte‑mode Encoding for GS1 Group Separators
gen.parameters.barcode.qr.encode_gs1_separator_in_byte_mode = True

# 3. Save the Barcode to a PNG File
gen.save("gs1qr_test.png")

# 4. Verify by Reading the Barcode Back
reader = BarCodeReader("gs1qr_test.png", DecodeType.GS1QR)
for result in reader.read_bar_codes():
    print("BarCode CodeText: " + result.code_text)
```

**Explanation**

- `BarcodeGenerator(EncodeTypes.GS1QR, "(10)ASPOSE2001(21)ASPOSE2026")` creates a generator configured for the GS1QR symbology. The payload string follows the GS1 syntax, where `(10)` denotes the **Batch or Lot Number** AI and `(21)` denotes the **Serial Number** AI.
- `gen.parameters.barcode.qr.encode_gs1_separator_in_byte_mode = True` activates the new option introduced in version 26.6. When true, the internal QR encoder treats the GS1 group separator (ASCII 29) as raw bytes, allowing it to appear in the encoded data without being interpreted as a structural marker.
- `gen.save("gs1qr_test.png")` writes the barcode to a PNG file. PNG is lossless, ensuring the exact module pattern is preserved for subsequent scanning.
- `BarCodeReader("gs1qr_test.png", DecodeType.GS1QR)` constructs a reader that expects GS1QR data. The `read_bar_codes()` method returns an iterable of `BarCodeResult` objects.
- `result.code_text` contains the decoded string, including any group separator characters. In a console view, the separator may appear as an invisible control character; you can examine its Unicode code point (`ord(char)`) for validation.

> **Note:** This code sample is reproduced from the official Aspose.BarCode release notes and has not been executed in a sandbox. Verify it in your own environment before using it in production.

## Read and Verify the Generated Barcode

While the previous section already read back the barcode, a dedicated verification routine can help developers automate testing.

### Steps

1. Load the saved PNG file using `BarCodeReader` with `DecodeType.GS1QR`.
2. Iterate over all decoded results (a single result is expected for a single barcode image).
3. Extract `result.code_text` and split it by the GS1 group separator (ASCII 29) if needed.
4. Optionally compare the decoded fields against the original input to assert correctness.

```python
from aspose.barcode.barcoderecognition import BarCodeReader, DecodeType

# Load the Barcode Image Generated Earlier
reader = BarCodeReader("gs1qr_test.png", DecodeType.GS1QR)
for result in reader.read_bar_codes():
    decoded = result.code_text
    print("Decoded GS1QR payload:", decoded)
    # Show the Unicode code point of each character for debugging
    for idx, ch in enumerate(decoded):
        print(f"Char {idx}: '{ch}' (U+{ord(ch):04X})")
```

**Explanation**

- The `BarCodeReader` instance is configured with `DecodeType.GS1QR`, ensuring the library applies the GS1‑specific parsing rules.
- The loop prints the raw decoded string. Because the group separator is a non‑printable control character, the helper loop displays each character’s Unicode code point. You should see `U+001D` for the GS1 separator if the byte‑mode flag worked correctly.
- This verification step is useful for unit tests or CI pipelines where you need to guarantee that the barcode payload matches the expected GS1 format exactly.

## Get a Free License

Aspose offers a temporary free license that removes evaluation watermarks and enables full functionality for testing. Request one at the [Aspose temporary license page](https://purchase.aspose.com/temporary-license/).

## Free Additional Resources

- [Product Documentation](https://docs.aspose.com/barcode/python-net/)
- [API Reference](https://reference.aspose.com/barcode/python-net/)
- [Free Online Barcode Apps](https://products.aspose.app/barcode/family)

## Conclusion

By leveraging the **encode_gs1_separator_in_byte_mode** option, developers can now generate GS1QR barcodes that faithfully embed GS1 group separators and the '%' character without manual byte handling. The tutorial covered installation, barcode creation, enabling byte‑mode, saving the image, and reading it back for verification. With the free license and the rich set of resources provided by Aspose, you can quickly integrate compliant GS1QR barcodes into Python applications ranging from inventory management systems to healthcare tracking solutions.

## FAQs

1. **What does the encode_gs1_separator_in_byte_mode option do?**
   It forces the QR encoder to treat GS1 group separator characters (ASCII 29) and the '%' character as raw byte data, allowing them to appear in the barcode payload.

2. **Do I need a special license to use the GS1QR features?**
   The GS1QR format is available in the standard Aspose.BarCode library. You can obtain a temporary free license from the Aspose website to evaluate the feature.

3. **Can I use this feature with other QR code types?**
   The byte‑mode separator option is specific to the GS1QR EncodeTypes value; other QR types ignore it.

4. **Is the generated barcode image lossless?**
   When you save to PNG (the default) the image is lossless, preserving exact module data for reliable reading.

5. **How do I verify that the separator was encoded correctly?**
   Read the barcode back with BarCodeReader using DecodeType.GS1QR and inspect the CodeText; the presence of the group separator character (shown as a control character) confirms correct encoding.

6. **Does enabling byte‑mode affect barcode size?**
   Byte‑mode may increase the number of data bits needed, which can slightly enlarge the QR matrix, but the library automatically selects the smallest version that fits the data.

## Read More

- [Generate MaxiCode Barcode in Python](https://blog.aspose.com/barcode/generate-maxicode-barcode-in-python/)
- [Build Code 93 Barcode Generator in Python](https://blog.aspose.com/barcode/build-code-93-barcode-generator-in-python/)
- [Generate Barcode and QR Code with Logo in Python](https://blog.aspose.com/barcode/generate-barcode-and-qr-code-with-logo-in-python/)

