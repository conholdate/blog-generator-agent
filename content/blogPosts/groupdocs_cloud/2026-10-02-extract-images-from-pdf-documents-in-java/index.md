---
title: "Extract Images from PDF Documents in Java"
seoTitle: "Extract Images from PDF Documents in Java"
description: "Learn how to extract images from PDF documents in Java using GroupDocs.Parser Cloud SDK. Guide covers setup, code example, cURL calls, and best practices."
date: Fri, 02 Oct 2026 10:36:06 +0000
lastmod: Fri, 02 Oct 2026 10:36:06 +0000
draft: false
url: /parser/extract-images-from-pdf-documents-in-java/
author: "Muhammad Mustafa"
summary: "This tutorial shows how to extract images from PDF documents in Java with GroupDocs.Parser Cloud SDK for Java. You'll set credentials, initialize the parser, run the extraction request, save each image, and use cURL with best practices for PDF image extraction."
tags: ['java pdf', 'pdf image extraction', 'pdf parsing']
categories: ["GroupDocs.Parser Cloud Product Family"]
showtoc: true
cover:
   image: images/extract-images-from-pdf-documents-in-java.jpg
   alt: "Extract Images from PDF Documents in Java"
   caption: "Extract Images from PDF Documents in Java"
steps:
  - "Step 1: Configure API credentials"
  - "Step 2: Initialize the Parser API"
  - "Step 3: Build the image‑extraction request"
  - "Step 4: Execute extraction and retrieve images"
  - "Step 5: Save each image to local storage"
faqs:
  - q: "How can I extract images from PDF documents in Java using GroupDocs.Parser?"
    a: "Use the [GroupDocs.Parser Cloud SDK for Java](https://products.groupdocs.cloud/parser/java/) to create an ExtractImagesRequest, call the parserApi.extractImages method, and iterate over the returned Image objects."
  - q: "Do I need to upload the PDF file before extracting images?"
    a: "Yes. The file must be stored in GroupDocs Cloud storage. You can upload it via the SDK or the REST API before running the extraction request."
  - q: "Can I extract images from password‑protected PDFs?"
    a: "The SDK supports protected PDFs. Set the password on the FileInfo object before calling extractImages. See the [API reference](https://reference.groupdocs.cloud/parser/) for details."
  - q: "Is there a way to test image extraction without writing code?"
    a: "You can try the operation using the cURL examples below or the online demo on the [GroupDocs.Parser Cloud product page](https://products.groupdocs.cloud/parser/java/)."
---

Extracting images from [PDF](https://docs.fileformat.com/pdf) files is a frequent requirement when building document‑processing pipelines, especially when you need to reuse graphics for thumbnails, reports, or further analysis. [GroupDocs.Parser Cloud SDK for Java](https://products.groupdocs.cloud/parser/java/) provides a straightforward API that lets you pull every embedded image from a PDF with just a few lines of code. This guide walks you through configuring the SDK, running a complete code example, using cURL for the same task, and applying best practices to ensure reliable PDF image extraction.

## Extract Images from PDF Documents in Java in 5 Steps

1. **Configure API credentials**: Create a `Configuration` object and set your client ID and secret.  
   ```java
   Configuration config = new Configuration();
   config.setClientId("YOUR_CLIENT_ID");
   config.setClientSecret("YOUR_CLIENT_SECRET");
   ```
   

2. **Initialize the Parser API**: Build an `ApiClient` with the configuration and instantiate `ParserApi`.  
   ```java
   ApiClient apiClient = new ApiClient(config);
   ParserApi parserApi = new ParserApi(apiClient);
   ```
   

3. **Build the image‑extraction request**: Specify the PDF file path using `FileInfo` and create an `ExtractImagesRequest`.  
   ```java
   String inputFilePath = "input.pdf";
   ExtractImagesRequest request = new ExtractImagesRequest()
           .setFileInfo(new FileInfo().setFilePath(inputFilePath));
   ```
   

4. **Execute extraction and retrieve images**: Call `extractImages` and obtain the list of `Image` objects.  
   ```java
   ImagesResult imagesResult = parserApi.extractImages(request);
   List<Image> images = imagesResult.getImages();
   ```
   

5. **Save each image to local storage**: Loop through the collection and write the binary data to files.  
   ```java
   for (int i = 0; i < images.size(); i++) {
       Image img = images.get(i);
       String outputFileName = "extracted_image_" + (i + 1) + "_" + img.getFileName();
       try (FileOutputStream fos = new FileOutputStream(outputFileName)) {
           fos.write(img.getData());
       }
       System.out.println("Saved image: " + outputFileName);
   }
   ```
   

For more details on each class, refer to the [official API reference](https://reference.groupdocs.cloud/parser/).

## Complete Code Example: Extract Images from PDF Documents in Java Using GroupDocs.Parser

The following example demonstrates the full workflow from credential setup to image saving.

```java
import com.groupdocs.parser.cloud.ApiClient;
import com.groupdocs.parser.cloud.Configuration;
import com.groupdocs.parser.cloud.api.ParserApi;
import com.groupdocs.parser.cloud.model.FileInfo;
import com.groupdocs.parser.cloud.model.Image;
import com.groupdocs.parser.cloud.model.ImagesResult;
import com.groupdocs.parser.cloud.model.requests.ExtractImagesRequest;

import java.io.FileOutputStream;
import java.util.List;

public class ExtractImagesFromPdf {
    public static void main(String[] args) {
        // Configure API credentials
        Configuration config = new Configuration();
        config.setClientId("YOUR_CLIENT_ID");
        config.setClientSecret("YOUR_CLIENT_SECRET");
        // config.setBaseUrl("https://api.groupdocs.cloud"); // optional, if needed

        // Initialize API client and Parser API
        ApiClient apiClient = new ApiClient(config);
        ParserApi parserApi = new ParserApi(apiClient);

        // Path to the PDF file stored in GroupDocs Cloud storage
        String inputFilePath = "input.pdf";

        // Build request for image extraction
        ExtractImagesRequest request = new ExtractImagesRequest()
                .setFileInfo(new FileInfo().setFilePath(inputFilePath));

        try {
            // Perform extraction
            ImagesResult imagesResult = parserApi.extractImages(request);
            List<Image> images = imagesResult.getImages();

            // Save each extracted image to local disk
            for (int i = 0; i < images.size(); i++) {
                Image img = images.get(i);
                String outputFileName = "extracted_image_" + (i + 1) + "_" + img.getFileName();
                try (FileOutputStream fos = new FileOutputStream(outputFileName)) {
                    fos.write(img.getData());
                }
                System.out.println("Saved image: " + outputFileName);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.groupdocs.cloud/parser/) or reach out to the [support team](https://forum.groupdocs.cloud/c/parser/19) for assistance.

## PDF Image Extraction via cURL and the REST API

You can achieve the same result without writing Java code by calling the GroupDocs.Parser Cloud REST endpoints directly.

1. **Obtain an access token**  
   ```bash
   curl -X POST "https://api.groupdocs.cloud/v2.0/connect/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET"
   ```

2. **Upload the PDF file**  
   ```bash
   curl -X POST "https://api.groupdocs.cloud/v2.0/storage/file/upload?path=input.pdf" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -F "file=@/path/to/input.pdf"
   ```

3. **Request image extraction**  
   ```bash
   curl -X POST "https://api.groupdocs.cloud/v2.0/parser/extractImages" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"fileInfo": {"filePath": "input.pdf"}}'
   ```

4. **Download extracted images** (the response contains base64 data; you can decode it locally)  

For a complete list of parameters, see the [official API documentation](https://reference.groupdocs.cloud/parser/).

## Installing and Configuring GroupDocs.Parser Cloud SDK for Java

Add the Maven dependency to your `pom.xml` (or the equivalent Gradle snippet).  
```xml
<dependency>
    <groupId>com.groupdocs</groupId>
    <artifactId>groupdocs-parser-cloud</artifactId>
    <version>26.2</version>
</dependency>
```

The SDK is delivered as a cloud library; no local binaries are required. Download the latest package from the [release page](https://releases.groupdocs.cloud/parser/java/). Ensure you have Java 8 or higher and a valid GroupDocs Cloud account with client ID and secret.

## GroupDocs.Parser Cloud SDK for Java Features Enabling Image Retrieval

- **Full PDF image extraction** - Retrieves every raster and vector image embedded in the document.  
- **Metadata for each image** - Returns file name, size, format, and page number.  
- **Support for all common image formats** - [PNG](https://docs.fileformat.com/image/png/), [JPG](https://docs.fileformat.com/image/jpg/), [BMP](https://docs.fileformat.com/image/bmp/), [GIF](https://docs.fileformat.com/image/gif/), [TIFF](https://docs.fileformat.com/image/tiff/), and more.  
- **Cloud storage integration** - Works directly with files stored in GroupDocs Cloud without downloading them first.  
- **Scalable REST‑based processing** - Handles large PDFs and high‑volume workloads via the cloud API.

## Fine‑Tuning Image Extraction Settings

While the basic request works out of the box, you can adjust options such as:

- **Password protection** - Set the `password` property on `FileInfo` for encrypted PDFs.  
- **Page range** - Limit extraction to specific pages by adding a `pages` array to the request JSON.  
- **Image format conversion** - Request conversion to a different format by specifying the desired output type in the request (refer to the [API reference](https://reference.groupdocs.cloud/parser/) for exact fields).

Example of setting a password (excerpted from the main code):

```java
FileInfo fileInfo = new FileInfo()
        .setFilePath("protected.pdf")
        .setPassword("mySecret");
```

## Practical Tips for Efficient PDF Image Extraction

- **Validate file existence** before sending the request to avoid unnecessary API calls.  
- **Process images in streams** when dealing with large files to reduce memory consumption.  
- **Use pagination** if you only need images from certain pages; this speeds up the response.  
- **Handle API rate limits** by implementing exponential back‑off on HTTP 429 responses.  
- **Log each saved file name** to simplify troubleshooting and audit trails.

## Conclusion

Extracting images from PDF documents in Java becomes a simple, reliable task when you leverage the power of the [GroupDocs.Parser Cloud SDK for Java](https://products.groupdocs.cloud/parser/java/). The SDK handles credential management, cloud storage interaction, and image decoding, letting you focus on your application logic. For production deployments, purchase a proper license on the [pricing page](https://purchase.groupdocs.cloud/temporary-license/) or obtain a temporary license for evaluation. With the code example, cURL guide, and best‑practice recommendations in this article, you're ready to integrate PDF image extraction into any Java‑based solution.

## FAQs

- **What formats can be extracted from a PDF?**  
  The SDK extracts raster formats such as PNG, JPG, BMP, GIF, and TIFF, as well as vector graphics when they are stored as images.  

- **Do I need to download the PDF before extracting images?**  
  No. The SDK works directly with files stored in GroupDocs Cloud storage, eliminating the need for local downloads.  

- **How does the SDK handle large PDFs?**  
  Extraction is performed on the server side, so memory usage on your machine stays low. You can also limit extraction to specific pages to improve performance.  

- **Is there a way to test the extraction without writing code?**  
  Yes, you can use the cURL commands provided above or try the interactive API console on the product page.

## Read More
- [Extract Images from PDF Files in Java using REST API](https://blog.groupdocs.cloud/parser/extract-images-from-pdf-files-in-java-using-rest-api/)
- [Extract Images from Word Documents Programmatically in Java](https://blog.groupdocs.cloud/parser/extract-images-from-word-documents-programmatically-in-java/)
- [Extract Images from PDF Documents using Python](https://blog.groupdocs.cloud/parser/extract-images-from-pdf-documents-using-python/)