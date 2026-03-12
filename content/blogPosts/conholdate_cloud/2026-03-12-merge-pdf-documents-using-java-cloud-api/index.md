---
title: "Merge PDF Documents using Java Cloud API"
seoTitle: "Merge PDF Documents Using Java Cloud API: Step by Step Guide"
description: "Learn how to merge PDF documents using Java cloud API with Conholdate.Total Cloud SDK for Java. This guide provides setup and cURL examples for PDF merging."
date: Thu, 12 Mar 2026 14:40:26 +0000
lastmod: Thu, 12 Mar 2026 14:40:26 +0000
draft: false
url: /total/merge-pdf-documents-using-java-cloud-api/
author: "Muhammad Mustafa"
summary: "This guide shows Java developers how to merge PDF documents using Conholdate.Total Cloud SDK for Java. It covers setup, Java code that combines PDFs, and executing the operation via REST API with cURL. Includes tips for large files and licensing."
tags: ["merge PDF documents using Java cloud api", "merge PDF files in Java", "combine PDF documents using Java"]
categories: ["Conholdate.Total Cloud Product Family"]
showtoc: true
cover:
   image: images/merge-pdf-documents-using-java-cloud-api.png
   alt: "Merge PDF Documents using Java Cloud API"
   caption: "Merge PDF Documents using Java Cloud API"
steps:
  - "Step 1: Install the library via Maven."
  - "Step 2: Configure authentication with your client credentials."
  - "Step 3: Upload or reference the source PDF files."
  - "Step 4: Call the merge operation."
  - "Step 5: Download or save the merged PDF."
faqs:
  - q: "Can I merge PDF documents using Java cloud API in a single request?"
    a: "Yes, the [Conholdate.Total Cloud SDK for Java](https://products.conholdate.cloud/total/) lets you merge multiple PDFs in one API call, reducing network overhead."
  - q: "What file size limits apply when merging PDFs with the Java library?"
    a: "The cloud service accepts files up to 100 MB each. For larger documents, split them before merging or use streaming options described in the [API reference](https://reference.conholdate.cloud/)."
  - q: "Do I need a license to run the merge PDF documents using Java cloud API example?"
    a: "A valid license is required for production use. You can obtain a subscription at the [pricing page](https://purchase.conholdate.cloud/pricing/total) and use a temporary trial key for testing."
  - q: "Is it possible to merge PDFs without writing Java code?"
    a: "The same operation can be performed via REST calls using cURL; see the dedicated cURL section below for a code‑free alternative."
---

[Conholdate.Total Cloud SDK for Java](https://products.conholdate.cloud/total/) enables developers to work with [PDF](https://docs.fileformat.com/pdf) files programmatically on the server side. This library provides high‑performance operations such as merging, splitting, and editing PDFs without leaving the Java ecosystem. In this guide we will demonstrate how to merge PDF documents using Java cloud API, covering setup, code implementation, and a REST API alternative with cURL.

## Prerequisites and Setup

To start, ensure you have Java 11 or higher installed and Maven available on your development machine.

* **Download the library**: Get the latest version from [this page](https://releases.aspose.cloud/total/).
* **Maven dependency**:

<!--[CODE_SNIPPET_START]-->
```xml
<dependency>
    <groupId>com.conholdate.total</groupId>
    <artifactId>total-sdk</artifactId>
    <version>23.10</version>
</dependency>
```
<!--[CODE_SNIPPET_END]-->

* **Authentication**: Register your application in the Conholdate Cloud console to obtain `client_id` and `client_secret`. You will use these credentials to request an access token.

The library runs on your local server or any Java‑compatible environment; it is not a [browser](https://docs.fileformat.com/web/browser/)‑based solution. Licensing is required for production use; see the licensing note after the code example.

## Key Features of Conholdate.Total Cloud SDK for Java

* **Merge PDF Documents** - Combine any number of PDF files into a single document while preserving bookmarks, annotations, and metadata.
* **Cloud‑Based Processing** - Heavy lifting is performed on Conholdate's servers, keeping your application lightweight.
* **Cross‑Platform Compatibility** - Works on Windows, Linux, and macOS with the same API.
* **Secure Access** - All communication is encrypted via HTTPS and authenticated with OAuth 2.0 tokens.

## Modify PDF Document Properties in Java using Conholdate.Total Cloud SDK

Beyond merging, the SDK lets you edit document properties such as title, author, and keywords. You can set these values before or after the merge operation by using the `PdfInfo` class (see the [API reference](https://reference.conholdate.cloud/)).

## Steps to Merge PDF Documents Using Java Cloud API

1. **Create an API client**: Initialize the `PdfApi` class with your access token.  
   <!--[CODE_SNIPPET_START]-->
   ```java
   PdfApi pdfApi = new PdfApi("YOUR_ACCESS_TOKEN");
   ```
   <!--[CODE_SNIPPET_END]-->

2. **Prepare the list of source files**: Provide the URLs or upload IDs of the PDFs you want to merge.  
   <!--[CODE_SNIPPET_START]-->
   ```java
   List<String> sourceFiles = Arrays.asList("file1.pdf", "file2.pdf", "file3.pdf");
   ```
   <!--[CODE_SNIPPET_END]-->

3. **Call the merge operation**: Use the `mergePdf` method to combine the files.  
   <!--[CODE_SNIPPET_START]-->
   ```java
   MergePdfRequest request = new MergePdfRequest()
       .setInputFiles(sourceFiles)
       .setOutputFile("merged_output.pdf");
   pdfApi.mergePdf(request);
   ```
   <!--[CODE_SNIPPET_END]-->

4. **Handle the response**: Check the HTTP status and download the resulting PDF if needed.  
   <!--[CODE_SNIPPET_START]-->
   ```java
   if (request.getStatusCode() == 200) {
       System.out.println("PDFs merged successfully.");
   } else {
       System.err.println("Merge failed: " + request.getErrorMessage());
   }
   ```
   <!--[CODE_SNIPPET_END]-->

These steps illustrate the core workflow for **merge PDF documents using Java cloud api**.

## Merge PDF Documents Using Java Cloud API - Complete Code Example

The following example puts everything together: authentication, file upload, merging, and downloading the final PDF.

<!--[COMPLETE_CODE_SNIPPET_START]-->
```java
import com.conholdate.total.sdk.ApiClient;
import com.conholdate.total.sdk.auth.OAuthApi;
import com.conholdate.total.sdk.pdf.PdfApi;
import com.conholdate.total.sdk.pdf.model.MergePdfRequest;
import java.io.File;
import java.util.Arrays;
import java.util.List;

public class MergePdfDemo {
    public static void main(String[] args) throws Exception {
        // 1. Obtain access token
        ApiClient authClient = new ApiClient();
        OAuthApi oauth = new OAuthApi(authClient);
        String token = oauth.getAccessToken("YOUR_CLIENT_ID", "YOUR_CLIENT_SECRET");

        // 2. Initialize PDF API with the token
        PdfApi pdfApi = new PdfApi(token);

        // 3. Upload source PDF files to cloud storage (optional if files are already there)
        // For simplicity, assume files are already accessible via URLs or storage IDs.

        // 4. Prepare list of source files
        List<String> sourceFiles = Arrays.asList(
                "https://example.com/files/first.pdf",
                "https://example.com/files/second.pdf",
                "https://example.com/files/third.pdf"
        );

        // 5. Create merge request
        MergePdfRequest mergeRequest = new MergePdfRequest()
                .setInputFiles(sourceFiles)
                .setOutputFile("merged_result.pdf");

        // 6. Execute merge operation
        pdfApi.mergePdf(mergeRequest);

        // 7. Download the merged PDF
        File mergedFile = pdfApi.downloadFile("merged_result.pdf");
        System.out.println("Merged PDF saved to: " + mergedFile.getAbsolutePath());
    }
}
```
<!--[COMPLETE_CODE_SNIPPET_END]-->

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update the file paths (`first.pdf`, `second.pdf`, etc.) to match your actual file locations, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://reference.conholdate.cloud/) or reach out to the [support team](https://forum.conholdate.cloud/) for assistance.

## Merge PDF Documents via REST API using cURL

If you prefer not to install the Java library, you can call the same operation directly through the REST API.

1. **Obtain an access token**  

   ```bash
   curl -X POST "https://api.conholdate.cloud/v1/oauth2/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET"
   ```

2. **Upload source PDF files** (if they are not already stored)  

   ```bash
   curl -X POST "https://api.conholdate.cloud/v1/storage/file" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -F "file=@first.pdf" \
        -F "path=/input/first.pdf"
   ```

   Repeat for each file.

3. **Execute the merge operation**  

   ```bash
   curl -X POST "https://api.conholdate.cloud/v1/pdf/merge" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
              "inputFiles": ["/input/first.pdf", "/input/second.pdf", "/input/third.pdf"],
              "outputFile": "/output/merged_result.pdf"
            }'
   ```

4. **Download the merged PDF**  

   ```bash
   curl -X GET "https://api.conholdate.cloud/v1/storage/file/output/merged_result.pdf" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -o merged_result.pdf
   ```

These cURL commands perform the same **merge PDF documents** operation without writing any Java code.

## Conclusion

In this tutorial we covered everything you need to **merge PDF documents using Java cloud api** with the [Conholdate.Total Cloud SDK for Java](https://products.conholdate.cloud/total/). You learned how to configure the library, write Java code that merges multiple PDFs, and invoke the same functionality via REST API with cURL. Remember to secure your credentials, handle large files efficiently, and apply a valid license for production details are available on the [pricing page](https://purchase.conholdate.cloud/pricing/total). With these tools you can automate PDF merging in any Java‑based backend system.

## FAQs

**Can I merge PDF documents using Java cloud API without uploading them first?**  
Yes. If the PDFs are already stored in Conholdate Cloud storage, you can reference their storage IDs directly in the merge request, avoiding an extra upload step.

**What formats are supported for the source files when merging PDFs?**  
The merge operation works exclusively with PDF inputs. If you need to combine other formats, convert them to PDF first using the appropriate SDK methods.

**Is there a limit on the number of PDFs I can merge in a single call?**  
The API accepts up to 20 files per request. For larger batches, split the operation into multiple calls and then merge the intermediate results.

**Do I need a license to run the merge PDF documents using Java cloud API example?**  
A licensed subscription is required for production deployments. You can start with a trial key for evaluation, then purchase a plan from the [pricing page](https://purchase.conholdate.cloud/pricing/total).

## Read More
- [Manipulate PDF Documents using Conholdate.Cloud](https://blog.conholdate.cloud/total/manipulate-pdf-documents/)
- [Convert HTML Files using Conholdate.Cloud](https://blog.conholdate.cloud/total/convert-html-files/)
- [Manipulate Excel Spreadsheets using Conholdate.Cloud](https://blog.conholdate.cloud/total/manipulate-excel-spreadsheets/)