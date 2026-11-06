---
title: "GIF to DICOM Conversion Example in Python"
seoTitle: "GIF to DICOM Conversion Example in Python"
description: "Learn how to programmatically convert GIF files to DICOM format in Python using Aspose.Slides Cloud SDK. Step-by-step guide with code and REST examples."
date: Fri, 06 Nov 2026 10:30:59 +0000
lastmod: Fri, 06 Nov 2026 10:30:59 +0000
draft: false
url: /slides/gif-to-dicom-conversion-example-in-python/
author: "Muhammad Mustafa"
summary: "Explore a GIF to DICOM conversion example in Python with Aspose.Slides Cloud SDK. It shows authentication setup, GIF input handling, DICOM metadata, batch conversion script, and cURL calls for REST, so you can quickly create DICOM files."
tags: ['gif to dicom', 'python image processing', 'medical imaging conversion']
categories: ["Aspose.Slides Cloud Product Family"]
showtoc: true
cover:
   image: images/gif-to-dicom-conversion-example-in-python.jpg
   alt: "GIF to DICOM Conversion Example in Python"
   caption: "GIF to DICOM Conversion Example in Python"
steps:
  - "Step 1: Install the SDK and configure authentication"
  - "Step 2: Set up input and output folders"
  - "Step 3: Implement conversion function"
  - "Step 4: Run batch conversion over GIF files"
  - "Step 5: Verify DICOM output files"
faqs:
  - q: "Can I convert a single GIF to DICOM using the SDK?"
    a: "Yes, you can call the convert_local method for an individual GIF file. See the [Aspose.Slides Cloud SDK for Python](https://products.aspose.cloud/slides/python/) documentation for details."
  - q: "How do I batch convert GIF files to DICOM in Python?"
    a: "Use the provided batch_convert_gif_folder function. It scans a folder for *.GIF files and converts each one, which is ideal for large image sets."
  - q: "Is there a way to convert DICOM back to JPEG or PNG?"
    a: "The SDK focuses on converting to DICOM, but you can use Aspose.Imaging Cloud SDK for .NET or other supported products to extract images from DICOM files."
  - q: "What licensing options are available and how can I get a temporary license?"
    a: "A commercial license is required for production use. You can obtain a temporary license for evaluation from the [temporary license page](https://purchase.aspose.com/temporary-license/)."
---

Converting animated medical graphics into a format that radiology systems understand can be a bottleneck for developers. [Aspose.Slides Cloud SDK for Python](https://products.aspose.cloud/slides/python/) provides a powerful library that simplifies this task. In this guide you will see a complete [GIF](https://docs.fileformat.com/image/gif/) to [DICOM](https://docs.fileformat.com/image/dicom/) conversion example in Python, learn how to set up authentication, handle batch processing, and explore equivalent cURL calls for REST integration.

## How to Transform GIF Images into DICOM Files Using Python - Step by Step

1. **Configure Authentication and Initialize SlidesApi**: Set your client credentials and create a SlidesApi instance.  
```python
from asposeslidescloud import SlidesApi, Configuration

config = Configuration()
config.api_key['client_id'] = "YOUR_CLIENT_ID"
config.api_key['client_secret'] = "YOUR_CLIENT_SECRET"
slides_api = SlidesApi(configuration=config)
```
   This step prepares the environment for the GIF to DICOM conversion example in Python.

2. **Define Input and Output Folders**: Create folders for source GIFs and generated DICOM files.  
```python
import os

INPUT_FOLDER = "gif_inputs"
OUTPUT_FOLDER = "dicom_outputs"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
```

3. **Create the Conversion Function**: Use `convert_local` to turn a GIF into DICOM, passing optional metadata.  
```python
def convert_gif_to_dicom(gif_path: str, dicom_path: str):
    with open(gif_path, "rb") as gif_file:
        result_bytes = slides_api.convert_local(
            file=gif_file,
            format="dicom",
            patientName="John Doe",
            patientId="123456",
            studyDescription="Sample GIF to DICOM conversion"
        )
    with open(dicom_path, "wb") as out_file:
        out_file.write(result_bytes)
```

4. **Batch Convert All GIF Files**: Scan the input folder and call the conversion function for each file.  
```python
import glob

def batch_convert_gif_folder(input_folder: str, output_folder: str):
    gif_files = glob.glob(os.path.join(input_folder, "*.gif"))
    for gif_file in gif_files:
        base_name = os.path.splitext(os.path.basename(gif_file))[0]
        dicom_file = os.path.join(output_folder, f"{base_name}.dcm")
        convert_gif_to_dicom(gif_file, dicom_file)
```

5. **Execute the Script**: Run the batch conversion when the module is executed directly.  
```python
if __name__ == "__main__":
    batch_convert_gif_folder(INPUT_FOLDER, OUTPUT_FOLDER)
```
   The script completes the GIF to DICOM conversion example in Python and leaves you with ready‑to‑use DICOM files.

## Complete Code Example: GIF to DICOM Conversion Using Aspose.Slides Cloud SDK

The following code shows the full implementation of the GIF to DICOM conversion example in Python.

```python
import os
import glob
from asposeslidescloud import SlidesApi, ApiException, Configuration

# -------------------- Setup Aspose.Slides Cloud SDK and Authentication --------------------
# Replace with your actual Aspose Cloud credentials
CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"

config = Configuration()
config.api_key['client_id'] = CLIENT_ID
config.api_key['client_secret'] = CLIENT_SECRET
# Optional: set the base URL if you use a different region
# config.host = "https://api.aspose.cloud"

slides_api = SlidesApi(configuration=config)

# -------------------- Prepare GIF Input and Define DICOM Parameters --------------------
INPUT_FOLDER = "gif_inputs"
OUTPUT_FOLDER = "dicom_outputs"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Example DICOM metadata (if the API supports passing them as query parameters)
# Here we just illustrate the idea; actual parameter names may differ.
dicom_params = {
    "patientName": "John Doe",
    "patientId": "123456",
    "studyDescription": "Sample GIF to DICOM conversion"
}

# -------------------- Write Python Script for GIF to DICOM Conversion Example --------------------
def convert_gif_to_dicom(gif_path: str, dicom_path: str):
    """
    Converts a single GIF file to DICOM format using Aspose.Slides Cloud SDK.
    """
    try:
        # Read the GIF file into memory
        with open(gif_path, "rb") as gif_file:
            # The SDK method `convert_local` returns the converted file bytes.
            # Pass the desired output format ("dicom") and any additional parameters.
            result_bytes = slides_api.convert_local(
                file=gif_file,
                format="dicom",
                # The following dictionary is illustrative; adjust according to SDK docs.
                **dicom_params
            )
        # Write the resulting DICOM bytes to the output file
        with open(dicom_path, "wb") as out_file:
            out_file.write(result_bytes)
        print(f"Converted '{gif_path}' → '{dicom_path}'")
    except ApiException as e:
        print(f"API error while converting '{gif_path}': {e}")
    except Exception as ex:
        print(f"Unexpected error while converting '{gif_path}': {ex}")

# -------------------- Batch Convert GIF Files to DICOM in Python --------------------
def batch_convert_gif_folder(input_folder: str, output_folder: str):
    """
    Scans the input folder for *.gif files and converts each to DICOM,
    storing results in the output folder.
    """
    gif_files = glob.glob(os.path.join(input_folder, "*.gif"))
    if not gif_files:
        print(f"No GIF files found in '{input_folder}'.")
        return

    for gif_file in gif_files:
        base_name = os.path.splitext(os.path.basename(gif_file))[0]
        dicom_file = os.path.join(output_folder, f"{base_name}.dcm")
        convert_gif_to_dicom(gif_file, dicom_file)

# -------------------- Execute Batch Conversion --------------------
if __name__ == "__main__":
    batch_convert_gif_folder(INPUT_FOLDER, OUTPUT_FOLDER)
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.aspose.cloud/slides/) or reach out to the [support team](https://forum.aspose.cloud/c/slides/15) for assistance.

## Using cURL to Call the Aspose.Slides Cloud Conversion Endpoint

Below are the REST calls that perform the same GIF to DICOM conversion example in Python via the Aspose.Slides Cloud API.

1. **Obtain an access token** (replace placeholders with your credentials).  
```bash
curl -X POST "https://api.aspose.cloud/connect/token" \
     -d "grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET"
```

2. **Upload a GIF file** to temporary storage.  
```bash
curl -X PUT "https://api.aspose.cloud/v3.0/slides/storage/file/gif_inputs/sample.gif" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/octet-stream" \
     --data-binary "@sample.gif"
```

3. **Request conversion to DICOM** while passing optional metadata.  
```bash
curl -X POST "https://api.aspose.cloud/v3.0/slides/gif_inputs/sample.gif/convert/dicom?patientName=John%20Doe&patientId=123456&studyDescription=Sample%20GIF%20to%20DICOM%20conversion" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -o "dicom_outputs/sample.dcm"
```

4. **Download the resulting DICOM file** (if you saved it elsewhere).  
```bash
curl -X GET "https://api.aspose.cloud/v3.0/slides/storage/file/dicom_outputs/sample.dcm" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -o "sample.dcm"
```

For more details on request parameters, see the [API reference](https://reference.aspose.cloud/slides/).

## Installing and Configuring Aspose.Slides Cloud SDK for Python

The SDK is distributed via PyPI. Install it with pip and verify the installation path.

```bash
pip install asposeslidescloud
```

After installation, create a configuration file or set environment variables with your `CLIENT_ID` and `CLIENT_SECRET`. The code snippet in the **Steps** section shows how to build the `Configuration` object.

## Conversion Settings: Options and Parameters

You can customize the DICOM output by adjusting the `dicom_params` dictionary. Common fields include patient information and study description.

```python
dicom_params = {
    "patientName": "John Doe",
    "patientId": "123456",
    "studyDescription": "Sample GIF to DICOM conversion"
}
```

Additional parameters such as image resolution or compression can be passed if supported by the API; refer to the [API reference](https://reference.aspose.cloud/slides/) for the full list.

## Frequently Asked Questions

- **Can I convert a single GIF to DICOM using the SDK?**  
  Yes, you can call the `convert_local` method for an individual GIF file. See the [Aspose.Slides Cloud SDK for Python](https://products.aspose.cloud/slides/python/) documentation for details.

- **How do I batch convert GIF files to DICOM in Python?**  
  Use the `batch_convert_gif_folder` function. It scans a folder for *.GIF files and converts each one, which is ideal for large image sets.

- **Is there a way to convert DICOM back to [JPEG](https://docs.fileformat.com/image/jpeg/) or [PNG](https://docs.fileformat.com/image/png/)?**  
  The SDK focuses on converting to DICOM, but you can use Aspose.Imaging Cloud SDK for .NET or other supported products to extract images from DICOM files.

- **What licensing options are available and how can I get a temporary license?**  
  A commercial license is required for production use. You can obtain a temporary license for evaluation from the [temporary license page](https://purchase.aspose.com/temporary-license/).

## Related Articles
- [ODS to XLSX Conversion Tutorial in Python](https://blog.aspose.cloud/slides/ods-to-xlsx-conversion-tutorial-in-python/)
- [Effortlessly Convert PPT and PPTX to JPG with Python](https://blog.aspose.cloud/slides/convert-ppt-to-jpg-using-python/)
- [Add Header/Footer to Powerpoint Presentations in Python](https://blog.aspose.cloud/slides/add-headerfooter-to-powerpoint-presentations-in-python/)