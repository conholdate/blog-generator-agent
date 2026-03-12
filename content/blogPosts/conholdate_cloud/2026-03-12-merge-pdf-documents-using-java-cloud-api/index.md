---
title: "Merge PDF Documents using Java Cloud API"
seoTitle: "Merge PDF Documents Using Java Cloud API: Step-by-Step Guide"
description: "Discover how to merge PDF documents using Java cloud API with Conholdate.Total Cloud SDK for Java. Follow step-by-step code and cURL examples for integration."
date: Thu, 12 Mar 2026 17:26:57 +0000
lastmod: Thu, 12 Mar 2026 17:26:57 +0000
draft: false
url: /total/merge-pdf-documents-using-java-cloud-api/
author: "Muhammad Mustafa"
summary: "Learn how to merge PDF documents using Java cloud API with Conholdate.Total Cloud SDK for Java. This guide walks through prerequisites, library setup, step-by-step merging, a complete code example, and equivalent cURL REST calls, plus production licensing tips."
tags: ["merge PDF documents using Java cloud api", "merge PDF documents using Java", "combine multiple PDFs in Java"]
categories: ["Conholdate.Total Cloud Product Family"]
showtoc: true
cover:
   image: images/merge-pdf-documents-using-java-cloud-api.png
   alt: "Merge PDF Documents using Java Cloud API"
   caption: "Merge PDF Documents using Java Cloud API"
steps:
  - "Step 1: Add the Conholdate.Total Cloud SDK for Java dependency to your project."
  - "Step 2: Configure authentication credentials for the cloud service."
  - "Step 3: Upload source PDF files to cloud storage."
  - "Step 4: Call the merge operation via the SDK."
  - "Step 5: Download the merged PDF and verify the result."
faqs:
  - q: "Can I merge PDF documents using Java cloud API without writing Java code?"
    a: "Yes, the same operation can be performed via REST calls. Use the cURL commands shown later to merge PDFs programmatically in Java environments without the SDK."
  - q: "What is the best java PDF merge library example for large documents?"
    a: "The complete code example in this article demonstrates an efficient java PDF merge library example using Conholdate.Total Cloud SDK for Java, handling streams and memory wisely."
  - q: "How do I handle errors when I merge PDF documents using Java cloud API?"
    a: "The SDK throws detailed exceptions. Catch them, log the error details, and refer to the [Conholdate.Total Cloud SDK for Java](https://products.conholdate.cloud/total/) documentation for troubleshooting."
  - q: "Is there a temporary license for testing the merge functionality?"
    a: "A temporary trial license can be obtained from the [pricing page](https://purchase.conholdate.cloud/pricing/total) to evaluate the API before purchasing a full license."
---


[Conholdate.Total Cloud SDK for Java](https://products.conholdate.cloud/total/) enables Java applications to work with [PDF](https://docs.fileformat.com/pdf) files in the cloud. With this library you can merge PDF documents using Java cloud API quickly and reliably. In this guide we walk through installing the SDK, configuring authentication, writing code to combine multiple PDFs in Java, and executing the same operation via REST calls. By the end you will have a reusable solution for how to merge PDFs programmatically in Java.

## Prerequisites and Setup

To use the Conholdate.Total Cloud SDK for Java you need Java 8 or higher and Maven installed on your development machine. Download the latest version from [this page](https://releases.aspose.cloud/total/).

Add the SDK to your Maven project:

<!--[CODE_SNIPPET_START]-->
```xml
<dependency>
    <groupId>com.conholdate.total</groupId>
    <artifactId>total-sdk</artifactId>
    <version>23.10</version>
</dependency>
```
<!--[CODE_SNIPPET_END]-->

Configure your client credentials (Client Id and Client Secret) which you obtain from the Conholdate portal. These credentials are required for every API call.

## Key Features of Conholdate.Total Cloud SDK for Java

The SDK offers a rich set of PDF manipulation features, including the ability to **combine multiple PDFs in Java** with a single method call. It also provides high‑performance streaming, password protection handling, and support for large documents. Developers looking for a java PDF merge library example will find the API intuitive and well documented.

## Modify PDF Document Properties in Java using Conholdate.Total Cloud SDK

Beyond merging, you can edit metadata, set page orientation, and add watermarks. The same client object used for merging can be reused to modify document properties, making it a versatile tool for any PDF workflow.

## Steps to Merge PDF Documents Using Java Cloud API

1. **Initialize the PdfApi client**: Create an instance of `PdfApi` with your client credentials.  
   <!--[CODE_SNIPPET_START]-->
   ```java
   PdfApi pdfApi = new PdfApi(clientId, clientSecret);
   ```
   <!--[CODE_SNIPPET_END]-->

2. **Upload source files**: Use the `uploadFile` method to send each PDF to cloud storage.  
   <!--[CODE_SNIPPET_START]-->
   ```java
   pdfApi.uploadFile("source1.pdf", Files.readAllBytes(Paths.get("source1.pdf")));
   pdfApi.uploadFile("source2.pdf", Files.readAllBytes(Paths.get("source2.pdf")));
   ```
   <!--[CODE_SNIPPET_END]-->

3. **Create a merge request**: Build a `MergePdfRequest` that lists the uploaded files in the desired order.  
   <!--[CODE_SNIPPET_START]-->
   ```java
   MergePdfRequest request = new MergePdfRequest()
       .addInputFile("source1.pdf")
       .addInputFile("source2.pdf")
       .setOutputFile("merged.pdf");
   ```
   <!--[CODE_SNIPPET_END]-->

4. **Execute the merge operation**: Call `mergePdf` on the `PdfApi` client.  
   <!--[CODE_SNIPPET_START]-->
   ```java
   pdfApi.mergePdf(request);
   ```
   <!--[CODE_SNIPPET_END]-->

5. **Download the merged PDF**: Retrieve the result and save it locally.  
   <!--[CODE_SNIPPET_START]-->
   ```java
   byte[] mergedBytes = pdfApi.downloadFile("merged.pdf");
   Files.write(Paths.get("merged_output.pdf"), mergedBytes);
   ```
   <!--[CODE_SNIPPET_END]-->

For more details on the `PdfApi` class, see the [API reference](https://reference.conholdate.cloud/).

## Merge PDF Documents Using Java Cloud API - Complete Code Example

The following example demonstrates how to merge two PDF files using the Conholdate.Total Cloud SDK for Java. It includes all required imports, authentication setup, error handling, and resource cleanup.

{{< gist "conholdate-cloud-gists" "f3955b6a13d13a84488607cf23fd77a3" "merge_pdf_documents_using_java_cloud_api_complete_.java" >}}

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update the file paths (`doc1.pdf`, `doc2.pdf`, etc.) to match your actual file locations, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://reference.conholdate.cloud/) or reach out to the [support team](https://forum.conholdate.cloud/) for assistance.

## Merge PDF Documents via REST API using cURL

The same merge operation can be performed directly through the REST API. This is useful for environments where installing the Java library is not practical.

**1. Authenticate and obtain an access token**

<!--[CODE_SNIPPET_START]-->
```bash
curl -X POST "https://api.conholdate.cloud/v1/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET"
```
<!--[CODE_SNIPPET_END]-->

**2. Upload the source PDF files**

Replace `YOUR_ACCESS_TOKEN` with the token from the previous step.

<!--[CODE_SNIPPET_START]-->
```bash
curl -X PUT "https://api.conholdate.cloud/v1/storage/file/doc1.pdf" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/pdf" \
  --data-binary "@doc1.pdf"
```

```bash
curl -X PUT "https://api.conholdate.cloud/v1/storage/file/doc2.pdf" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/pdf" \
  --data-binary "@doc2.pdf"
```
<!--[CODE_SNIPPET_END]-->

**3. Execute the merge operation**

<!--[CODE_SNIPPET_START]-->
```bash
curl -X POST "https://api.conholdate.cloud/v1/pdf/merge" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
        "inputFiles": ["doc1.pdf", "doc2.pdf"],
        "outputFile": "merged_result.pdf"
      }'
```
<!--[CODE_SNIPPET_END]-->

**4. Download the merged PDF**

<!--[CODE_SNIPPET_START]-->
```bash
curl -X GET "https://api.conholdate.cloud/v1/storage/file/merged_result.pdf" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -o merged_result.pdf
```
<!--[CODE_SNIPPET_END]-->

For a full list of endpoints and parameters, consult the [API reference](https://reference.conholdate.cloud/).

## Conclusion

You now have a complete solution for how to merge PDF documents using Java cloud API with the Conholdate.Total Cloud SDK for Java. The guide covered prerequisites, library configuration, step‑by‑step merging, a full working code example, and equivalent cURL commands for REST integration. Remember to obtain a proper license from the [pricing page](https://purchase.conholdate.cloud/pricing/total) for production use; a temporary trial license is available for evaluation. Integrate this functionality into your applications to streamline document workflows and improve user experience.

## FAQs

**How can I merge PDF documents using Java cloud API without the SDK?**  
You can call the REST endpoints directly with cURL or any HTTP client. The same merge operation is exposed via the API, allowing you to merge PDFs programmatically in Java or any other language.

**Where can I find a java PDF merge library example that handles large files?**  
The complete code example in this article shows an efficient java PDF merge library example that streams file data, reducing memory consumption for large documents.

**What is the best way to combine multiple PDFs in Java when I need to preserve annotations?**  
Use the `PdfApi` merge method with the `preserveAnnotations` flag set to true. This ensures that all annotations from the source files are retained in the final merged PDF.

**Is there a limit on the number of PDFs I can merge using the cloud API?**  
The cloud service imposes a size limit per request rather than a file count limit. For very large batches, consider merging in stages or contacting support for higher limits.

## Read More
- [Manipulate PDF Documents using Conholdate.Cloud](https://blog.conholdate.cloud/total/manipulate-pdf-documents/)
- [Convert HTML Files using Conholdate.Cloud](https://blog.conholdate.cloud/total/convert-html-files/)
- [Manipulate Excel Spreadsheets using Conholdate.Cloud](https://blog.conholdate.cloud/total/manipulate-excel-spreadsheets/)