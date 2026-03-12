---
title: "Merge PDF Documents using Java Cloud API"
seoTitle: "Merge PDF Documents Using Java Cloud API: Complete Guide"
description: "Learn to merge PDFs with Java using Conholdate.Total Cloud SDK. Follow our step guide with setup, code samples, and REST cURL examples for seamless merging."
date: Thu, 12 Mar 2026 14:49:59 +0000
lastmod: Thu, 12 Mar 2026 14:49:59 +0000
draft: false
url: /total/merge-pdf-documents-using-java-cloud-api/
author: "Muhammad Mustafa"
summary: "This guide teaches Java developers to merge PDF documents using the Conholdate.Total Cloud SDK for Java. It covers library installation, calling the merge API for many files, and performing the task via REST cURL commands. Full code samples and best practices included."
tags: ["merge PDF documents using Java cloud api", "merge PDF files in Java", "combine multiple PDFs using Java"]
categories: ["Conholdate.Total Cloud Product Family"]
showtoc: true
cover:
   image: images/merge-pdf-documents-using-java-cloud-api.png
   alt: "Merge PDF Documents using Java Cloud API"
   caption: "Merge PDF Documents using Java Cloud API"
steps:
  - "Step 1: Add the Conholdate.Total Cloud SDK for Java dependency to your project."
  - "Step 2: Initialize the PDF API client with your access credentials."
  - "Step 3: Upload the source PDF files to the cloud storage."
  - "Step 4: Call the merge endpoint, passing the list of uploaded files."
  - "Step 5: Download the merged PDF result and handle any errors."
faqs:
  - q: "How can I programmatically merge PDF documents in Java using a cloud API?"
    a: "Use the Conholdate.Total Cloud SDK for Java to call the merge endpoint. The library handles authentication, file upload, and merging, allowing you to combine PDFs with just a few lines of code."
  - q: "Is there a way to merge PDF files in Java without writing Java code?"
    a: "Yes, the same operation can be performed via REST calls. See the cURL example in this article or use any HTTP client to invoke the merge API directly."
  - q: "Can I combine multiple PDFs using Java and preserve document properties?"
    a: "The SDK lets you set PDF document properties before merging. Refer to the API reference for methods that modify metadata such as title, author, and keywords."
  - q: "Where can I find a java PDF merge library example for this task?"
    a: "The complete code example below demonstrates a java PDF merge library example using Conholdate.Total Cloud SDK for Java. It shows initialization, file upload, merge request, and result download."
---


Conholdate.Total Cloud SDK for Java empowers developers to programmatically manipulate [PDF](https://docs.fileformat.com/pdf) files in the cloud. This guide demonstrates how to merge PDF documents using Java cloud API, covering everything from project setup to a full working example. By the end you will be able to combine multiple PDFs using Java with just a few API calls.

## Prerequisites and Setup

To follow this tutorial you need:

- Java 8 or higher installed on your development machine.
- An active Conholdate.Total Cloud account with API credentials (client ID and client secret).
- Network access to the Conholdate.Total Cloud endpoints.

Download the latest version from [this page](https://releases.aspose.cloud/total/).

Add the SDK to your project using Maven:

<!--[CODE_SNIPPET_START]-->
```xml
<dependency>
    <groupId>com.conholdate.total</groupId>
    <artifactId>total-sdk</artifactId>
    <version>23.12</version>
</dependency>
```
<!--[CODE_SNIPPET_END]-->

If you prefer Gradle, use:

<!--[CODE_SNIPPET_START]-->
```gradle
implementation 'com.conholdate.total:total-sdk:23.12'
```
<!--[CODE_SNIPPET_END]-->

After adding the dependency, import the required classes in your Java source files.

## Key Features of Conholdate.Total Cloud SDK for Java

The SDK offers a comprehensive set of PDF manipulation capabilities, including:

- Merging, splitting, and reordering pages.
- Editing document properties such as title, author, and keywords.
- Converting PDFs to other formats (e.g., images, [HTML](https://docs.fileformat.com/web/html/)).
- Secure cloud storage and access control.

These features are exposed through a clean, fluent API that works on any Java platform, from desktop applications to server‑side services.

## Modify PDF Document Properties in Java using Conholdate.Total Cloud SDK

Before merging, you may want to adjust metadata on each source file. The SDK provides methods like `setTitle`, `setAuthor`, and `setKeywords` that can be called on a `PdfDocument` instance. Changing properties before the merge ensures the final document inherits the desired metadata.

```java
PdfDocument doc = new PdfDocument();
doc.setTitle("Quarterly Report");
doc.setAuthor("Finance Team");
doc.setKeywords("Q1, Finance, Report");
```

These adjustments are optional but useful for compliance and document management.

## Steps to Merge PDF Documents Using Java Cloud API

1. **Create the API client**: Initialize `PdfApi` with your client credentials.  
   <!--[CODE_SNIPPET_START]-->  
   ```java
   PdfApi pdfApi = new PdfApi("YOUR_CLIENT_ID", "YOUR_CLIENT_SECRET");
   ```  
   <!--[CODE_SNIPPET_END]-->  

2. **Upload source PDFs**: Use `uploadFile` to place each PDF in cloud storage.  
   <!--[CODE_SNIPPET_START]-->  
   ```java
   String fileId1 = pdfApi.uploadFile("input1.pdf");
   String fileId2 = pdfApi.uploadFile("input2.pdf");
   ```  
   <!--[CODE_SNIPPET_END]-->  

3. **Prepare merge request**: Build a `MergePdfRequest` with the uploaded file IDs.  
   <!--[CODE_SNIPPET_START]-->  
   ```java
   MergePdfRequest request = new MergePdfRequest();
   request.setFileIds(Arrays.asList(fileId1, fileId2));
   ```  
   <!--[CODE_SNIPPET_END]-->  

4. **Execute merge**: Call `mergePdf` to combine the files. The method returns the ID of the merged document.  
   <!--[CODE_SNIPPET_START]-->  
   ```java
   String mergedFileId = pdfApi.mergePdf(request);
   ```  
   <!--[CODE_SNIPPET_END]-->  

5. **Download the result**: Retrieve the merged PDF and save it locally.  
   <!--[CODE_SNIPPET_START]-->  
   ```java
   byte[] mergedPdf = pdfApi.downloadFile(mergedFileId);
   Files.write(Paths.get("merged_output.pdf"), mergedPdf);
   ```  
   <!--[CODE_SNIPPET_END]-->  

These steps illustrate how to programmatically merge PDF files in Java using the cloud API.

## Merge PDF Documents Using Java Cloud API - Complete Code Example

The following example puts all the steps together into a single, runnable program.

{{< gist "conholdate-cloud-gists" "1069fa33621a860fc73e91f339617f9a" "merge_pdf_documents_using_java_cloud_api_complete_.java" >}}

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update the file paths (`input1.pdf`, `input2.pdf`, etc.) to match your actual file locations, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://reference.conholdate.cloud/) or reach out to the [support team](https://forum.conholdate.cloud/) for assistance.

## Merge PDF Documents via REST API using cURL

If you prefer not to use the Java library, you can call the same service directly through HTTP. The following cURL commands illustrate the complete workflow.

**1. Authenticate and obtain an access token**

<!--[CODE_SNIPPET_START]-->
```bash
curl -X POST "https://api.conholdate.cloud/v1.0/oauth2/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET"
```
<!--[CODE_SNIPPET_END]-->

**2. Upload the source PDF files**

Replace `YOUR_ACCESS_TOKEN` with the token from the previous step.

<!--[CODE_SNIPPET_START]-->
```bash
curl -X POST "https://api.conholdate.cloud/v1.0/storage/file/input1.pdf" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -F "file=@input1.pdf"
```
<!--[CODE_SNIPPET_END]-->

Repeat the upload command for `input2.pdf`.

**3. Execute the merge operation**

<!--[CODE_SNIPPET_START]-->
```bash
curl -X POST "https://api.conholdate.cloud/v1.0/pdf/merge" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"fileIds":["input1.pdf","input2.pdf"],"outputFile":"merged_output.pdf"}'
```
<!--[CODE_SNIPPET_END]-->

**4. Download the merged PDF**

<!--[CODE_SNIPPET_START]-->
```bash
curl -X GET "https://api.conholdate.cloud/v1.0/storage/file/merged_output.pdf" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -o merged_output.pdf
```
<!--[CODE_SNIPPET_END]-->

For a full list of endpoints and parameters, consult the [API reference](https://reference.conholdate.cloud/).

## Conclusion

Merging PDF documents using Java cloud API is straightforward with Conholdate.Total Cloud SDK for Java. The library abstracts authentication, file handling, and the merge operation, letting you focus on business logic. You can also achieve the same result via REST calls, which is useful for scripting or environments where the Java library cannot be installed. Remember to acquire a proper license for production use; pricing details are available on the [Conholdate.Total Cloud SDK for Java](https://products.conholdate.cloud/total/) page, and a temporary trial license can be requested during evaluation.

## FAQs

**How can I programmatically merge PDF documents in Java using a cloud API?**  
Use the Conholdate.Total Cloud SDK for Java to upload your source files, call the `mergePdf` method, and download the combined result. The same workflow is available through REST calls if you prefer cURL.

**Can I merge PDF files in Java without writing any code?**  
Yes, the REST API can be invoked from any HTTP client, including command‑line tools like cURL or Postman. This allows you to merge PDFs without embedding the Java library.

**What is the best way to combine multiple PDFs using Java for large documents?**  
Upload each PDF to cloud storage, then pass the list of file IDs to the merge endpoint. The service processes the files server‑side, which is efficient for large or many documents.

**Where can I find a java PDF merge library example?**  
The complete code example in this article shows a java PDF merge library example using Conholdate.Total Cloud SDK for Java. Additional samples are available in the official [documentation](https://reference.conholdate.cloud/).

## Read More
- [Manipulate PDF Documents using Conholdate.Cloud](https://blog.conholdate.cloud/total/manipulate-pdf-documents/)
- [Convert HTML Files using Conholdate.Cloud](https://blog.conholdate.cloud/total/convert-html-files/)
- [Manipulate Excel Spreadsheets using Conholdate.Cloud](https://blog.conholdate.cloud/total/manipulate-excel-spreadsheets/)