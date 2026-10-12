---
title: "Extract Images from PDF Documents in C#"
seoTitle: "Extract Images from PDF Documents in C#"
description: "Learn how to extract images from PDF documents in C# using GroupDocs.Parser Cloud SDK for .NET. Follow this step‑by‑step guide with code, cURL and tips."
date: Mon, 12 Oct 2026 17:04:44 +0000
lastmod: Mon, 12 Oct 2026 17:04:44 +0000
draft: false
url: /parser/extract-images-from-pdf-documents-in-csharp/
author: "Muhammad Mustafa"
summary: "This tutorial shows C# developers how to extract images from PDF documents using GroupDocs.Parser Cloud SDK for .NET. You'll learn to upload a PDF, retrieve all embedded images, save them locally, and optionally clean up storage, with full code and REST examples."
tags: ['pdf image extraction', 'csharp pdf processing', 'image extraction techniques']
categories: ["GroupDocs.Parser Cloud Product Family"]
showtoc: true
cover:
   image: images/extract-images-from-pdf-documents-in-csharp.jpg
   alt: "Extract Images from PDF Documents in C#"
   caption: "Extract Images from PDF Documents in C#"
steps:
  - "Step 1: Upload the PDF to GroupDocs Cloud storage"
  - "Step 2: Request document images via the Parser API"
  - "Step 3: Decode Base64 data and save each image"
  - "Step 4: (Optional) Delete the PDF from storage"
  - "Step 5: Review console output for extracted image details"
faqs:
  - q: "How do I extract images from PDF documents using C#?"
    a: "Use the [GroupDocs.Parser Cloud SDK for .NET](https://products.groupdocs.cloud/parser/net/) to upload the PDF, call GetDocumentImages, decode the Base64 data and write the files to disk."
  - q: "Can I extract images from encrypted PDF documents?"
    a: "The SDK supports encrypted PDFs; provide the correct password in the request. See the [official documentation](https://docs.groupdocs.cloud/parser/) for details."
  - q: "What image formats are returned by the API?"
    a: "Images are returned in their original format (PNG, JPEG, BMP, etc.) as Base64 strings, which you can save using the appropriate file extension."
  - q: "Is there a way to limit extraction to specific pages?"
    a: "Yes, you can specify page ranges in the GetDocumentImages request. Refer to the [API reference](https://reference.groupdocs.cloud/parser/) for the exact parameters."
---

Extracting images from [PDF](https://docs.fileformat.com/pdf) documents is a frequent requirement when building document‑processing pipelines, especially for generating thumbnails or re‑using graphics elsewhere. [GroupDocs.Parser Cloud SDK for .NET](https://products.groupdocs.cloud/parser/net/) provides a powerful API that makes this task straightforward in C#. In this guide you will learn how to upload a PDF, retrieve all embedded images, save them locally, and optionally clean up the remote file, with complete code and REST examples.

## Steps to Extract Images from PDF Documents in C#

1. **Upload PDF to GroupDocs Cloud storage**: Use `StorageApi.UploadFile` to place the source PDF in the cloud.  
   ```csharp
   var uploadRequest = new UploadFileRequest(remotePdfPath, File.ReadAllBytes(localPdfPath));
   storageApi.UploadFile(uploadRequest);
   ```
   
   This call ensures the file is accessible for parsing.

2. **Request document images**: Call `ParserApi.GetDocumentImages` with a `GetDocumentImagesRequest`.  
   ```csharp
   var imagesRequest = new GetDocumentImagesRequest(remotePdfPath);
   ImagesResult imagesResult = parserApi.GetDocumentImages(imagesRequest);
   ```
   
   The response contains a collection of `ImageInfo` objects, each holding Base64 data and metadata. See the [API reference](https://reference.groupdocs.cloud/parser/) for full details.

3. **Decode and save each image**: Iterate through `imagesResult.Images`, convert the Base64 string to a byte array, and write the file to disk.  
   ```csharp
   foreach (ImageInfo imgInfo in imagesResult.Images)
   {
       byte[] imageBytes = Convert.FromBase64String(imgInfo.Base64Data);
       string extension = imgInfo.FileExtension?.TrimStart('.').ToLower() ?? "bin";
       string fileName = $"extracted_page{imgInfo.PageNumber}_img{imgInfo.ImageIndex}_{imageCounter}.{extension}";
       File.WriteAllBytes(fileName, imageBytes);
   }
   ```
   
   The console logs the saved file name, dimensions and DPI for verification.

4. **(Optional) Clean up remote PDF**: After extraction you may delete the uploaded file to keep storage tidy.  
   ```csharp
   var deleteRequest = new DeleteFileRequest(remotePdfPath);
   storageApi.DeleteFile(deleteRequest);
   ```
   
   This step is wrapped in a try‑catch block to ignore any cleanup errors.

5. **Review output**: The console will display a summary like `Total images extracted: 12`, confirming successful extraction.

## Complete Code Example: Extract Images from PDF Documents with GroupDocs.Parser

The following example demonstrates the full workflow described above. It includes configuration, upload, image extraction, saving, and optional cleanup.

```csharp
using System;
using System.IO;
using System.Collections.Generic;
using GroupDocs.Parser.Cloud.Sdk.Api;
using GroupDocs.Parser.Cloud.Sdk.Client;
using GroupDocs.Parser.Cloud.Sdk.Model;
using GroupDocs.Parser.Cloud.Sdk.Model.Requests;

namespace ExtractImagesFromPdf
{
    class Program
    {
        static void Main(string[] args)
        {
            // Configuration – replace with your actual credentials
            var config = new Configuration
            {
                ClientId = "YOUR_CLIENT_ID",
                ClientSecret = "YOUR_CLIENT_SECRET"
            };

            // APIs
            var storageApi = new StorageApi(config);
            var parserApi = new ParserApi(config);

            // Input PDF path (local) and remote name in storage
            const string localPdfPath = "input.pdf";
            const string remotePdfPath = "input.pdf";

            try
            {
                // -------------------------------------------------
                // 1. Upload PDF to GroupDocs Cloud storage (if not already there)
                // -------------------------------------------------
                if (!File.Exists(localPdfPath))
                    throw new FileNotFoundException($"Local file not found: {localPdfPath}");

                var uploadRequest = new UploadFileRequest(remotePdfPath, File.ReadAllBytes(localPdfPath));
                storageApi.UploadFile(uploadRequest);

                // -------------------------------------------------
                // 2. Retrieve document images (all pages)
                // -------------------------------------------------
                var imagesRequest = new GetDocumentImagesRequest(remotePdfPath);
                ImagesResult imagesResult = parserApi.GetDocumentImages(imagesRequest);

                // -------------------------------------------------
                // 3. Save each extracted image to disk
                // -------------------------------------------------
                int imageCounter = 0;
                foreach (ImageInfo imgInfo in imagesResult.Images)
                {
                    // Image data is returned as Base64 string
                    byte[] imageBytes = Convert.FromBase64String(imgInfo.Base64Data);

                    // Build a descriptive file name
                    string extension = imgInfo.FileExtension?.TrimStart('.').ToLower() ?? "bin";
                    string fileName = $"extracted_page{imgInfo.PageNumber}_img{imgInfo.ImageIndex}_{imageCounter}.{extension}";
                    File.WriteAllBytes(fileName, imageBytes);

                    Console.WriteLine($"Saved: {fileName} ({imgInfo.Width}x{imgInfo.Height} px, {imgInfo.Resolution} DPI)");
                    imageCounter++;
                }

                Console.WriteLine($"Total images extracted: {imageCounter}");
            }
            catch (ApiException apiEx)
            {
                Console.Error.WriteLine($"GroupDocs API error: {apiEx.ErrorCode} - {apiEx.Message}");
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Unexpected error: {ex.Message}");
            }
            finally
            {
                // -------------------------------------------------
                // 4. Optional cleanup – delete the uploaded PDF from storage
                // -------------------------------------------------
                try
                {
                    var deleteRequest = new DeleteFileRequest(remotePdfPath);
                    storageApi.DeleteFile(deleteRequest);
                }
                catch
                {
                    // Ignored – cleanup is optional
                }
            }
        }
    }
}
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.groupdocs.cloud/parser/) or reach out to the [support team](https://forum.groupdocs.cloud/c/parser/19) for assistance.

## Extract Images via REST API Using cURL

The same operation can be performed with direct REST calls. Below is a minimal cURL workflow.

1. **Obtain an access token** (OAuth 2.0 client credentials grant).  
   ```bash
   curl -X POST "https://api.groupdocs.cloud/v2.0/oauth2/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET"
   ```
   
   The response contains `access_token`.

2. **Upload the PDF** to the cloud storage.  
   ```bash
   curl -X PUT "https://api.groupdocs.cloud/v2.0/storage/file/input.pdf" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -H "Content-Type: application/pdf" \
        --data-binary "@input.pdf"
   ```
   

3. **Request images** for the uploaded document.  
   ```bash
   curl -X GET "https://api.groupdocs.cloud/v2.0/parser/input.pdf/images" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```
   
   The [JSON](https://docs.fileformat.com/web/json/) response includes an array of images with `base64Data`, `fileExtension`, `pageNumber`, etc.

4. **Save each image** locally (example using `jq` and `base64`).  
   ```bash
   curl -X GET "https://api.groupdocs.cloud/v2.0/parser/input.pdf/images" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" | \
        jq -r '.images[] | "\(.pageNumber)_\(.imageIndex).\(.fileExtension) \(.base64Data)"' | \
        while read filename b64; do
            echo "$b64" | base64 -d > "$filename"
        done
   ```

For more details on endpoints and parameters, see the [official API documentation](https://docs.groupdocs.cloud/parser/).

## Getting the Environment Ready

1. Install the .NET client library via NuGet:  
   ```bash
   dotnet add package GroupDocs.Parser-Cloud
   ```
   
   The package is available from the official [download page](https://releases.groupdocs.cloud/parser/net/).

2. Ensure you have .NET 6.0 or later installed and a valid GroupDocs Cloud account with client credentials.

3. (Optional) Clone the sample repository for reference:  
   ```bash
   git clone https://github.com/groupdocs-parser-cloud/groupdocs-parser-cloud-dotnet.git
   ```
   

## What Makes GroupDocs.Parser Suitable for Image Extraction

- **Direct image retrieval**: The `GetDocumentImages` call returns images in their original format without additional conversion steps.  
- **Base64 delivery**: Images are provided as Base64 strings, making them easy to decode in any language.  
- **Page‑level metadata**: Each `ImageInfo` includes page number, dimensions, resolution and index, which helps organize extracted assets.  
- **Support for all common raster formats**: [PNG](https://docs.fileformat.com/image/png/), [JPEG](https://docs.fileformat.com/image/jpeg/), [BMP](https://docs.fileformat.com/image/bmp/), [GIF](https://docs.fileformat.com/image/gif/), [TIFF](https://docs.fileformat.com/image/tiff/) and more are preserved exactly as stored in the PDF.  
- **Scalable cloud processing**: Large PDFs are handled on GroupDocs servers, reducing memory pressure on your application.

## Configuring Image Extraction Options

While the basic example works out‑of‑the‑box, you can fine‑tune the request:

- **Specify page range**: Add `pages = "1-5"` to `GetDocumentImagesRequest` to limit extraction.  
- **Set image quality**: Use the `imageQuality` parameter (0‑100) if you need [compressed](https://docs.fileformat.com/web/compressed/) output.  
- **Filter by format**: Provide `fileExtensions = ["png","jpeg"]` to receive only selected formats.  

These options are documented in the [API reference](https://reference.groupdocs.cloud/parser/).

## Conclusion

Extracting images from PDF documents in C# becomes a simple, reliable process when you leverage the [GroupDocs.Parser Cloud SDK for .NET](https://products.groupdocs.cloud/parser/net/). The SDK handles upload, parsing and Base64 conversion, letting you focus on saving files and integrating them into your workflow. Remember to secure your client credentials, respect licensing terms, and consider a temporary license for evaluation at the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/). With the code and REST examples provided, you're ready to add robust PDF image extraction to any .NET application.

## FAQs

**How do I extract images from PDF documents using C#?**  
Use the Parser API's `GetDocumentImages` method after uploading the PDF with `StorageApi.UploadFile`. Decode the returned Base64 strings and write them to disk, as shown in the code example.

**What if the PDF is password protected?**  
Include the password in the request model. The SDK will decrypt the file before extracting images. See the [documentation](https://docs.groupdocs.cloud/parser/) for the exact property name.

**Can I limit extraction to specific pages?**  
Yes, set the `pages` property on `GetDocumentImagesRequest` to a comma‑separated list or range (e.g., `"1-3,5"`). The API will return images only from those pages.

**Are there any size limits for the extracted images?**  
The SDK returns the original image data without resizing. If you need smaller files, post‑process the saved images using any image‑processing library.

## Read More
- [Extract Images from PDF in C# .NET | PDF Image Extractor API](https://blog.groupdocs.cloud/parser/extract-images-from-pdf-using-csharp/)
- [Extract Images from PDF Documents in Java](https://blog.groupdocs.cloud/parser/extract-images-from-pdf-documents-in-java/)
- [Extract Text from PDF Using .NET REST API | Document to Text Converter](https://blog.groupdocs.cloud/parser/extract-text-from-word-document-csharp/)