---
title: "How to Convert PDF Pages to PNG images in Python"
seoTitle: "How to Convert PDF Pages to PNG images in Python"
description: "Discover how to convert PDF pages to PNG images in Python with GroupDocs.Viewer Cloud SDK. The guide covers setup, code samples, conversion and cURL REST calls."
date: Fri, 20 Nov 2026 08:18:32 +0000
lastmod: Fri, 20 Nov 2026 08:18:32 +0000
draft: false
url: /viewer/how-to-convert-pdf-pages-to-png-images-in-python/
author: "Muhammad Mustafa"
summary: "This tutorial shows how to convert PDF pages to PNG images in Python with GroupDocs.Viewer Cloud SDK. You'll install the library, set credentials, convert all pages or selected pages, batch convert several PDFs, and see equivalent cURL REST commands."
tags: ['python pdf conversion', 'pdf to png', 'batch image processing']
categories: ["GroupDocs.Viewer Cloud Product Family"]
showtoc: true
cover:
   image: images/how-to-convert-pdf-pages-to-png-images-in-python.jpg
   alt: "How to Convert PDF Pages to PNG images in Python"
   caption: "How to Convert PDF Pages to PNG images in Python"
steps:
  - "Step 1: Install the GroupDocs Viewer Cloud SDK for Python"
  - "Step 2: Configure your Cloud credentials"
  - "Step 3: Convert all pages or selected pages to PNG"
  - "Step 4: Batch convert multiple PDFs"
  - "Step 5: Use cURL for REST API conversion"
faqs:
  - q: "How can I extract PNG images from a PDF using Python?"
    a: "You can use [GroupDocs.Viewer Cloud SDK for Python](https://products.groupdocs.cloud/viewer/python/) to convert PDF pages to PNG images in Python. The SDK provides methods to convert all pages or specific pages with just a few lines of code."
  - q: "Is it possible to convert only certain pages of a PDF to PNG?"
    a: "Yes, the SDK lets you specify a list of page numbers via the `pages` property in `PdfConvertOptions`. See the API reference for `PdfConvertOptions` for details."
  - q: "Can I batch convert several PDFs to PNG in one run?"
    a: "The provided `batch_convert_pdfs_to_png` function demonstrates how to loop through multiple PDF files and convert each to its own PNG folder using the same SDK."
  - q: "What are the licensing options for GroupDocs Viewer Cloud?"
    a: "GroupDocs offers subscription plans with usage‑based pricing. You can also obtain a temporary license for evaluation from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/)."
---

Converting [PDF](https://docs.fileformat.com/pdf) pages to [PNG](https://docs.fileformat.com/image/png/) images is a frequent need when you want to generate thumbnails or display documents in web applications. [GroupDocs.Viewer Cloud SDK for Python](https://products.groupdocs.cloud/viewer/python/) provides a powerful library that handles this conversion entirely in the cloud. In this guide you will learn how to convert PDF pages to PNG images in Python, covering installation, single‑page and batch processing, as well as equivalent cURL calls for REST integration. By the end you'll have ready‑to‑use code that can be adapted to any Python project.

## Prerequisites and Setup

Before you start, make sure you have the following:

- Python 3.7 or newer installed on your development machine.  
- A GroupDocs Cloud account with **client_id** and **client_secret** values.  
- Access to the GroupDocs storage where your PDF files will reside.

Install the SDK with pip:

```bash
pip install groupdocs-viewer-cloud
```

Next, configure your credentials. Replace the placeholder values with the ones from your GroupDocs Cloud dashboard.

```python
from groupdocs_viewer_cloud import Configuration

config = Configuration()
config.client_id = "YOUR_CLIENT_ID"
config.client_secret = "YOUR_CLIENT_SECRET"
```

You'll also need to import the main API classes that will be used throughout the tutorial. See the full API reference at the [GroupDocs Viewer API Reference](https://reference.groupdocs.cloud/viewer/).

With the SDK installed and credentials set, you're ready to start converting PDFs to PNG images.

## How to Convert PDF Pages to PNG Images in Python: Step-by-Step Walkthrough

### Step 1: Load the Source Document

Create a `ViewerApi` instance and point it to the PDF file stored in GroupDocs Cloud.

```python
from groupdocs_viewer_cloud import ViewerApi, ApiClient

api_client = ApiClient(configuration=config)
viewer = ViewerApi(api_client)
```

This object will be used for all conversion calls.

### Step 2: Configure Conversion Options

Set the desired output format to **PNG** and specify the folder where the images will be saved.

```python
from groupdocs_viewer_cloud import models

options = models.PdfConvertOptions()
options.file_path = "sample.pdf"          # Path in GroupDocs Cloud storage
options.format = "PNG"                    # Output format
options.output_path = "output/all_pages"  # Destination folder
```

You can also define the `pages` list here if you only need specific pages.

### Step 3: Convert All Pages

Call the `convert_document` method without a pages list to convert every page.

```python
request = models.ConvertDocumentRequest(options)
result = viewer.convert_document(request)

for page in result.pages:
    print(f"Page {page.page_number} saved as {page.path}")
```

Each page is saved as an individual PNG file in the output folder.

### Step 4: Convert Selected Pages

If you need only certain pages, add the `pages` property to the options.

```python
options.pages = [1, 3, 5]   # Convert pages 1, 3 and 5 only
request = models.ConvertDocumentRequest(options)
result = viewer.convert_document(request)

for page in result.pages:
    print(f"Selected page {page.page_number} saved as {page.path}")
```

This gives you fine‑grained control over which pages are rendered.

### Step 5: Batch Convert Multiple PDFs

Loop through a list of PDF files and convert each one to its own PNG folder.

```python
pdf_files = ["sample.pdf", "another_document.pdf", "third_file.pdf"]
output_root = "output/batch"

for pdf_path in pdf_files:
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    out_folder = os.path.join(output_root, base_name)

    options.file_path = pdf_path
    options.output_path = out_folder

    request = models.ConvertDocumentRequest(options)
    result = viewer.convert_document(request)

    for page in result.pages:
        print(f"[{pdf_path}] Page {page.page_number} saved as {page.path}")
```

This approach scales easily for large document collections.

## Complete Code Example: How to Convert PDF Pages to PNG Images in Python - Full Implementation

The following script puts all the pieces together. It demonstrates converting all pages, selected pages, and batch processing multiple PDFs.

```python
# Install the SDK (run once):
# pip install groupdocs-viewer-cloud

import os
from groupdocs_viewer_cloud import ViewerApi, ApiClient, Configuration, models

# -------------------- Configuration --------------------
# Replace with your actual GroupDocs Cloud credentials
config = Configuration()
config.client_id = "YOUR_CLIENT_ID"
config.client_secret = "YOUR_CLIENT_SECRET"

api_client = ApiClient(configuration=config)
viewer = ViewerApi(api_client)

# -------------------- Helper Functions --------------------
def convert_pdf_to_png_all_pages(input_pdf: str, output_folder: str):
    """
    Convert every page of a PDF to separate PNG images.
    """
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    options = models.PdfConvertOptions()
    options.file_path = input_pdf          # Path in GroupDocs Cloud storage
    options.format = "PNG"                 # Desired output format
    options.output_path = output_folder    # Folder in storage where PNGs will be saved
    # No pages list -> all pages are converted

    request = models.ConvertDocumentRequest(options)
    result = viewer.convert_document(request)

    for page in result.pages:
        print(f"Page {page.page_number} saved as {page.path}")

def convert_pdf_to_png_selected_pages(input_pdf: str, output_folder: str, pages: list):
    """
    Convert only the specified pages of a PDF to PNG images.
    """
    os.makedirs(output_folder, exist_ok=True)

    options = models.PdfConvertOptions()
    options.file_path = input_pdf
    options.format = "PNG"
    options.output_path = output_folder
    options.pages = pages                     # e.g., [1, 3, 5]

    request = models.ConvertDocumentRequest(options)
    result = viewer.convert_document(request)

    for page in result.pages:
        print(f"Selected page {page.page_number} saved as {page.path}")

def batch_convert_pdfs_to_png(pdf_files: list, output_root: str):
    """
    Convert multiple PDF documents to PNG images in a single batch operation.
    Each PDF gets its own sub‑folder under `output_root`.
    """
    os.makedirs(output_root, exist_ok=True)

    for pdf_path in pdf_files:
        # Derive a folder name from the PDF file name (without extension)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        out_folder = os.path.join(output_root, base_name)

        options = models.PdfConvertOptions()
        options.file_path = pdf_path
        options.format = "PNG"
        options.output_path = out_folder

        request = models.ConvertDocumentRequest(options)
        result = viewer.convert_document(request)

        for page in result.pages:
            print(f"[{pdf_path}] Page {page.page_number} saved as {page.path}")

# -------------------- Example Usage --------------------
if __name__ == "__main__":
    # Paths are relative to the root of your GroupDocs Cloud storage
    input_pdf = "sample.pdf"
    all_pages_output = "output/all_pages"
    selected_pages_output = "output/selected_pages"
    batch_output_root = "output/batch"

    # 1. Convert all pages of a PDF to PNG
    convert_pdf_to_png_all_pages(input_pdf, all_pages_output)

    # 2. Convert only pages 1, 3 and 5 of the same PDF to PNG
    convert_pdf_to_png_selected_pages(input_pdf, selected_pages_output, pages=[1, 3, 5])

    # 3. Batch convert several PDFs
    pdf_list = ["sample.pdf", "another_document.pdf", "third_file.pdf"]
    batch_convert_pdfs_to_png(pdf_list, batch_output_root)
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.groupdocs.cloud/viewer/) or reach out to the [support team](https://forum.groupdocs.cloud/c/viewer/9) for assistance.

## Convert PDF to PNG via REST API using cURL

The same conversion can be performed through GroupDocs Viewer's REST endpoints. Below are the typical cURL calls you would execute.

First, obtain an access token using your client credentials.

```bash
curl -X POST "https://api.groupdocs.cloud/v2.0/oauth2/token" \
     -H "Content-Type: application/json" \
     -d '{"client_id":"YOUR_CLIENT_ID","client_secret":"YOUR_CLIENT_SECRET"}'
```

Assuming the response contains `"access_token":"YOUR_ACCESS_TOKEN"`, use that token for subsequent calls.

Upload the PDF file to GroupDocs storage.

```bash
curl -X POST "https://api.groupdocs.cloud/v2.0/storage/file/upload?path=sample.pdf" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -F "file=@/path/to/local/sample.pdf"
```

Request the conversion to PNG for all pages.

```bash
curl -X POST "https://api.groupdocs.cloud/v2.0/viewer/pdf/convert?format=PNG&outputPath=output/all_pages" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"filePath":"sample.pdf"}'
```

If you need only specific pages, add the `pages` query parameter (e.g., `pages=1,3,5`).

Download a generated PNG file.

```bash
curl -X GET "https://api.groupdocs.cloud/v2.0/storage/file/download?path=output/all_pages/page1.png" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -o page1.png
```

For more details on request parameters, see the [GroupDocs Viewer API Reference](https://reference.groupdocs.cloud/viewer/).

## Conversion Options for PDF to PNG: Settings and Tweaks

The SDK exposes several options you can adjust in `PdfConvertOptions`:

- **format** - Must be set to `"PNG"` to generate PNG images.  
- **output_path** - Destination folder in GroupDocs storage where the PNG files will be written.  
- **pages** - An optional list of page [numbers](https://docs.fileformat.com/spreadsheet/numbers/) to convert (e.g., `[1, 3, 5]`).  

You can also control image quality, DPI, and color mode by using additional properties documented in the API reference. For example, to change the DPI you would set `options.dpi = 300` (property not shown in the basic code snippets).

## Conclusion

You now know how to convert PDF pages to PNG images in Python using the [GroupDocs.Viewer Cloud SDK for Python](https://products.groupdocs.cloud/viewer/python/). The library handles single‑page, selective‑page, and batch conversions with minimal code, and the equivalent cURL commands let you integrate the same functionality into any environment that can make HTTP requests. Remember to review the licensing options on the product page; GroupDocs offers subscription‑based pricing and you can obtain a temporary license for testing from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/). Start integrating PDF‑to‑PNG conversion into your applications today and enjoy seamless document rendering.

## FAQs

- **How can I extract PNG images from a PDF using Python?**  
  Use the SDK's `convert_pdf_to_png_all_pages` or `convert_pdf_to_png_selected_pages` methods. They take a PDF stored in GroupDocs Cloud and output PNG files for each page. See the full example above.

- **Is it possible to convert only certain pages of a PDF to PNG?**  
  Yes. Set the `pages` property on `PdfConvertOptions` to a list of page numbers you want to render. The API reference provides details on this property.

- **Can I batch convert several PDFs to PNG in one run?**  
  The `batch_convert_pdfs_to_png` helper function loops through a list of PDFs and creates a separate output folder for each, allowing you to process many documents with a single script.

- **What are the licensing options for GroupDocs Viewer Cloud?**  
  GroupDocs offers flexible subscription plans based on usage. For evaluation you can request a temporary license from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/).

## Read More
- [Render Project Data to PDF using Python](https://blog.groupdocs.cloud/viewer/render-project-data-from-mpp-to-pdf-in-python/)
- [Display Word Document in HTML Page using PHP](https://blog.groupdocs.cloud/viewer/display-word-document-in-html-page-using-php/)
- [Render Excel Data to PDF using REST API in Node.js](https://blog.groupdocs.cloud/viewer/render-excel-data-to-pdf-using-rest-api-in-node-js/)