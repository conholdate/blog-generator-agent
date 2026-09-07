---
title: "Remove Image Watermark from PDF in Java"
seoTitle: "Remove Image Watermark from PDF in Java"
description: "Remove an image watermark from a PDF with GroupDocs.Watermark Cloud SDK for Java. Follow a step-by-step guide with complete code and cURL examples."
date: Mon, 07 Sep 2026 13:44:25 +0000
lastmod: Mon, 07 Sep 2026 13:44:25 +0000
draft: false
url: /watermark/remove-image-watermark-from-pdf-in-java/
author: "Muhammad Mustafa"
summary: "Learn how Java developers can remove an image watermark from a PDF using GroupDocs.Watermark Cloud SDK for Java. The guide covers prerequisites, a step‑by‑step implementation, configuration tips, and cURL commands for cloud integration."
tags: ['java pdf processing', 'watermark removal', 'pdf image manipulation']
categories: ["GroupDocs.Watermark Cloud Product Family"]
showtoc: true
cover:
   image: images/remove-image-watermark-from-pdf-in-java.jpg
   alt: "Remove Image Watermark from PDF in Java"
   caption: "Remove Image Watermark from PDF in Java"
steps:
  - "Step 1: Add Maven dependency for GroupDocs.Watermark Cloud SDK."
  - "Step 2: Initialize the API client with your credentials."
  - "Step 3: Define the image watermark search criteria."
  - "Step 4: Configure removal options and execute the API call."
  - "Step 5: Process the result and retrieve the cleaned PDF."
faqs:
  - q: "How do I remove image watermark from PDF in Java?"
    a: "Use the [GroupDocs.Watermark Cloud SDK for Java](https://products.groupdocs.cloud/watermark/java/) and call the remove API with an ImageSearchCriteria. See the official [documentation](https://docs.groupdocs.cloud/watermark/) for details."
  - q: "Can the SDK handle password‑protected PDFs?"
    a: "Yes. Set the password on the FileInfo object before calling remove. The SDK will decrypt the file, process the watermark, and re‑encrypt the output."
  - q: "What image formats are supported for watermark detection?"
    a: "Common formats such as PNG, JPG, BMP, and GIF are supported. Provide the path to the image file in the ImageSearchCriteria."
  - q: "Is there a way to remove multiple watermarks in one call?"
    a: "You can add several ImageSearchCriteria objects to the RemoveOptions. The API will process all matching watermarks in a single request."
---

Unwanted image watermarks can make [PDF](https://docs.fileformat.com/pdf) documents look unprofessional and hinder downstream processing. [GroupDocs.Watermark Cloud SDK for Java](https://products.groupdocs.cloud/watermark/java/) offers a robust API that lets Java developers programmatically strip those watermarks from PDF files. This guide shows how to **remove image watermark from PDF in Java** using the SDK's removal endpoint. By the end, you'll be able to integrate automatic watermark removal into any Java application.

## Java Development Environment - Prerequisites and Setup

Before you start, make sure you have the following:

- Java 17 or higher installed.
- Maven or Gradle for dependency management.
- A GroupDocs Cloud account with **client ID** and **client secret**.

Add the SDK to your project with the Maven dependency below (you can also use the Gradle equivalent). The latest binaries are available on the [download page](https://releases.groupdocs.cloud/watermark/java/).

<!--[CODE_SNIPPET_START]-->
```xml
<dependency>
    <groupId>com.groupdocs</groupId>
    <artifactId>groupdocs-watermark-cloud</artifactId>
    <version>23.8</version>
</dependency>
```
<!--[CODE_SNIPPET_END]-->

Initialize the API client using your credentials. This snippet is taken directly from the sample code.

<!--[CODE_SNIPPET_START]-->
```java
ApiClient apiClient = new ApiClient("YOUR_CLIENT_ID", "YOUR_CLIENT_SECRET");
WatermarkApi watermarkApi = new WatermarkApi(apiClient);
```
<!--[CODE_SNIPPET_END]-->

With the client ready, you can move on to the actual removal workflow.

## Step-by-Step Guide to Remove Image Watermark from PDF in Java

### Step 1: Load the Source Document

First, specify the PDF you want to clean. The `FileInfo` object tells the API where the file lives and optionally supplies a password.

<!--[CODE_SNIPPET_START]-->
```java
FileInfo inputFile = new FileInfo();
inputFile.setFilePath("input.pdf");
// inputFile.setPassword("pdfPassword"); // Uncomment if needed
```
<!--[CODE_SNIPPET_END]-->

### Step 2: Define the Image Watermark Criteria

Create an `ImageSearchCriteria` that points to the watermark image you wish to delete. This is the core of the **remove image watermark from PDF in Java** operation.

<!--[CODE_SNIPPET_START]-->
```java
ImageSearchCriteria imageCriteria = new ImageSearchCriteria();
imageCriteria.setImagePath("watermark.png");
```
<!--[CODE_SNIPPET_END]-->

### Step 3: Set Up Removal Options

Combine the file information and search criteria into a `RemoveOptions` object. You also define where the cleaned PDF will be saved.

<!--[CODE_SNIPPET_START]-->
```java
RemoveOptions removeOptions = new RemoveOptions();
removeOptions.setFileInfo(inputFile);
removeOptions.setOutputPath("output.pdf");
removeOptions.setSearchCriteria(Collections.singletonList(imageCriteria));
```
<!--[CODE_SNIPPET_END]-->

### Step 4: Execute the Removal Call

Invoke the `remove` method on the `WatermarkApi`. The call returns a `RemoveResult` that contains the path to the processed file.

<!--[CODE_SNIPPET_START]-->
```java
RemoveResult result = watermarkApi.remove(removeOptions);
System.out.println("Watermark removal completed. Output file: " + result.getPath());
```
<!--[CODE_SNIPPET_END]-->

### Step 5: Process the Result

Handle any exceptions that may arise. The SDK throws `ApiException` for service‑side errors and generic `Exception` for unexpected issues.

<!--[CODE_SNIPPET_START]-->
```java
try {
    // removal code above
} catch (ApiException e) {
    System.err.println("API exception occurred: " + e.getMessage());
} catch (Exception e) {
    System.err.println("Unexpected error: " + e.getMessage());
}
```
<!--[CODE_SNIPPET_END]-->

## Complete Code Example: Remove Image Watermark Using GroupDocs

The following example demonstrates the full workflow from client initialization to result handling.

<!--[COMPLETE_CODE_SNIPPET_START]-->
```java
import com.groupdocs.watermark.cloud.api.WatermarkApi;
import com.groupdocs.watermark.cloud.client.ApiClient;
import com.groupdocs.watermark.cloud.client.ApiException;
import com.groupdocs.watermark.cloud.model.FileInfo;
import com.groupdocs.watermark.cloud.model.ImageSearchCriteria;
import com.groupdocs.watermark.cloud.model.RemoveOptions;
import com.groupdocs.watermark.cloud.model.RemoveResult;
import java.util.Collections;

public class RemoveImageWatermarkFromPdf {
    public static void main(String[] args) {
        // Initialize API client with your credentials
        ApiClient apiClient = new ApiClient("YOUR_CLIENT_ID", "YOUR_CLIENT_SECRET");
        WatermarkApi watermarkApi = new WatermarkApi(apiClient);

        // Prepare input file information
        FileInfo inputFile = new FileInfo();
        inputFile.setFilePath("input.pdf");
        // If the PDF is password protected, uncomment the following line and set the password
        // inputFile.setPassword("pdfPassword");

        // Define the image watermark to be removed
        ImageSearchCriteria imageCriteria = new ImageSearchCriteria();
        imageCriteria.setImagePath("watermark.png");

        // Set up removal options
        RemoveOptions removeOptions = new RemoveOptions();
        removeOptions.setFileInfo(inputFile);
        removeOptions.setOutputPath("output.pdf");
        removeOptions.setSearchCriteria(Collections.singletonList(imageCriteria));

        try {
            // Execute removal
            RemoveResult result = watermarkApi.remove(removeOptions);
            System.out.println("Watermark removal completed. Output file: " + result.getPath());
        } catch (ApiException e) {
            System.err.println("API exception occurred: " + e.getMessage());
        } catch (Exception e) {
            System.err.println("Unexpected error: " + e.getMessage());
        }
    }
}
```
<!--[COMPLETE_CODE_SNIPPET_END]-->

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.groupdocs.cloud/watermark/) or reach out to the [support team](https://forum.groupdocs.cloud/c/watermark/29) for assistance.

## Watermark Removal Operation via REST API using cURL

If you prefer a pure REST approach, the same operation can be performed with cURL commands.

1. **Authenticate and obtain an access token**

   ```bash
   curl -X POST "https://api.groupdocs.cloud/v2.0/auth/token" \
        -H "Content-Type: application/json" \
        -d '{"client_id":"YOUR_CLIENT_ID","client_secret":"YOUR_CLIENT_SECRET"}'
   ```

2. **Upload the source PDF**

   ```bash
   curl -X POST "https://api.groupdocs.cloud/v2.0/storage/upload?path=input.pdf" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -F "file=@/local/path/input.pdf"
   ```

3. **Execute the watermark removal**

   ```bash
   curl -X POST "https://api.groupdocs.cloud/v2.0/watermark/remove" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
              "fileInfo": {"filePath":"input.pdf"},
              "outputPath":"output.pdf",
              "searchCriteria":[{"type":"Image","imagePath":"watermark.png"}]
            }'
   ```

4. **Download the cleaned PDF**

   ```bash
   curl -X GET "https://api.groupdocs.cloud/v2.0/storage/download?path=output.pdf" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -o output.pdf
   ```

For a full reference, see the [API documentation](https://reference.groupdocs.cloud/watermark/).

## Fine-Tuning Removal Options

The SDK provides several properties you can adjust to suit different scenarios.

- **Password Protection** - If the source PDF is encrypted, set the password on `FileInfo`.

  ```java
  inputFile.setPassword("mySecret");
  ```

- **Multiple Search Criteria** - Remove several watermarks in one call by adding more `ImageSearchCriteria` objects to the list.

  ```java
  ImageSearchCriteria logoCriteria = new ImageSearchCriteria();
  logoCriteria.setImagePath("logo.png");
  removeOptions.setSearchCriteria(Arrays.asList(imageCriteria, logoCriteria));
  ```

- **Output Format** - Although the default is PDF, you can change the output format by setting `outputPath` with a different extension (e.g., `output.docx`).

  ```java
  removeOptions.setOutputPath("output.docx");
  ```

These options let you tailor the **remove image watermark from PDF in Java** process to your exact needs.

## Conclusion

Programmatically removing an image watermark from PDF files is straightforward with the [GroupDocs.Watermark Cloud SDK for Java](https://products.groupdocs.cloud/watermark/java/). By following the steps above, you can integrate watermark deletion into any Java backend, handle encrypted PDFs, and fine‑tune the operation with flexible options. Remember to obtain a proper license for production use; pricing details are available on the product page, and a temporary license can be requested via the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/). Start cleaning your PDFs today and deliver polished documents to your users.

## FAQs

- **How do I remove image watermark from PDF in Java?**  
  Use the `remove` method of `WatermarkApi` with an `ImageSearchCriteria` that points to the watermark image. The full code example in this article shows the exact steps.

- **What if my PDF is password protected?**  
  Set the password on the `FileInfo` object (`inputFile.setPassword("yourPassword")`) before calling the removal API. The SDK will decrypt, process, and re‑encrypt the file automatically.

- **Can I remove watermarks from other formats, such as [DOCX](https://docs.fileformat.com/word-processing/docx/)?**  
  Yes. The same API works with any format supported by GroupDocs.Watermark. Just change the `filePath` and `outputPath` extensions accordingly.

- **Are there limits on the size of the PDF I can process?**  
  The cloud service handles files up to 500 MB per request. For larger documents, consider splitting the PDF into smaller parts before processing.

## Read More
- [Add Image Watermark to PDF Documents in Java](https://blog.groupdocs.cloud/watermark/add-image-watermark-to-pdf-documents-in-java/)
- [Add Watermark to Images using Java](https://blog.groupdocs.cloud/watermark/add-watermark-to-images-using-java/)
- [Remove Image Watermark from PDF in C# | Delete PDF Watermark](https://blog.groupdocs.cloud/watermark/remove-image-watermark-from-pdf-in-csharp/)