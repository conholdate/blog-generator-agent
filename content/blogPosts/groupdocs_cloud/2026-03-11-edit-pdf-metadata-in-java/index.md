---
title: "Edit PDF Metadata in Java"
seoTitle: "Edit PDF Metadata in Java: Step-by-Step Guide for Developers"
description: "Learn how to edit PDF metadata in Java with GroupDocs.Metadata Cloud SDK. This guide shows how to update document properties, add fields, and save the PDF."
date: Wed, 11 Mar 2026 16:13:07 +0000
lastmod: Wed, 11 Mar 2026 16:13:07 +0000
draft: false
url: /metadata/edit-pdf-metadata-in-java/
author: "Muhammad Mustafa"
summary: "This guide shows how to edit PDF metadata in Java with GroupDocs.Metadata Cloud SDK. Learn to read existing metadata, modify Title, Author, and add custom key-value pairs, then save the file. Code example and a REST API cURL snippet are provided for integration."
tags: ["edit PDF Metadata in Java", "edit PDF metadata in Java", "update PDF document properties using Java"]
categories: ["GroupDocs.Metadata Cloud Product Family"]
showtoc: true
cover:
   image: images/edit-pdf-metadata-in-java.png
   alt: "Edit PDF Metadata in Java"
   caption: "Edit PDF Metadata in Java"
steps:
  - "Step 1: Install the GroupDocs.Metadata Cloud SDK for Java."
  - "Step 2: Configure authentication credentials."
  - "Step 3: Load the PDF file into the Metadata API."
  - "Step 4: Modify standard and custom metadata fields."
  - "Step 5: Save the updated PDF back to storage."
faqs:
  - q: "How can I edit PDF metadata in Java using GroupDocs.Metadata Cloud SDK?"
    a: "Use the SDK to load a PDF, modify its MetadataInfo properties, and save the file. See the [GroupDocs.Metadata Cloud SDK for Java](https://products.groupdocs.cloud/metadata/java/) documentation for details."
  - q: "Can I add custom key-value pairs to a PDF's metadata?"
    a: "Yes, the SDK allows adding custom entries via the setCustomProperties method. Refer to the [API reference](https://reference.groupdocs.cloud/metadata/) for examples."
  - q: "Is a temporary license sufficient for development?"
    a: "A temporary license from the [license page](https://purchase.groupdocs.cloud/temporary-license/) lets you test the SDK. For production, purchase a full license."
  - q: "Where can I find more examples for PDF metadata manipulation?"
    a: "The official [documentation](https://docs.groupdocs.cloud/metadata/) and the [forums](https://forum.groupdocs.cloud/c/metadata/30) contain additional samples and community support."
---


[GroupDocs.Metadata Cloud SDK for Java](https://products.groupdocs.cloud/metadata/java/) enables Java developers to programmatically read and modify [PDF](https://docs.fileformat.com/pdf) document properties. In this guide you will learn how to edit PDF metadata in Java, update standard fields like Title and Author, and add custom key‑value pairs. The SDK provides a simple API to load a PDF, change its metadata, and save the file back to storage. Follow the step‑by‑step instructions to integrate metadata editing into your Java applications.

## Prerequisites and Setup

To work with PDF metadata you need Java 8 or higher and Maven installed on your development machine. Download the latest version from [this page](https://releases.groupdocs.cloud/metadata/java/).

Add the SDK to your Maven project:

<!--[CODE_SNIPPET_START]-->
```xml
<dependency>
    <groupId>com.groupdocs</groupId>
    <artifactId>groupdocs-metadata-cloud</artifactId>
    <version>23.9</version>
</dependency>
```
<!--[CODE_SNIPPET_END]-->

Or install it via the command line:

<!--[CODE_SNIPPET_START]-->
```bash
mvn install com.groupdocs:groupdocs-metadata-cloud
```
<!--[CODE_SNIPPET_END]-->

Create a configuration file (or set environment variables) with your client ID and client secret obtained from the GroupDocs Cloud dashboard. No license code is required for this example; a temporary license can be requested from the [license page](https://purchase.groupdocs.cloud/temporary-license/).

## Understanding PDF Metadata

PDF files contain a set of standard properties (Title, Author, Subject, Keywords) and allow custom key‑value pairs. These properties are stored in the document's metadata dictionary and can be read or modified without altering the visual content of the file.

## Key Features of GroupDocs.Metadata Cloud SDK for Java

- Read existing metadata from PDF, [DOCX](https://docs.fileformat.com/word-processing/docx/), [XLSX](https://docs.fileformat.com/spreadsheet/xlsx/), and many other formats.  
- Update standard properties such as Title, Author, Creator, and Producer.  
- Add, edit, or remove custom properties using a simple map interface.  
- Save changes back to the original file or to a new output location.

## Modifying Standard PDF Document Properties

The SDK exposes the `MetadataInfo` class which provides getters and setters for all standard fields. You can also access the `CustomProperties` collection to work with user‑defined entries.

## Adding Custom Metadata Fields

Custom metadata is stored as a dictionary of string keys and values. The SDK automatically serializes these entries when the document is saved, making them available to any PDF reader that supports custom metadata.

## Steps to Edit PDF Metadata in Java

1. **Initialize the API client**: Create a `Configuration` object with your credentials and instantiate the `MetadataApi`.  
2. **Upload the source PDF**: Use the `StorageApi` to place the file in your GroupDocs Cloud storage.  
3. **Load the PDF metadata**: Call `metadataApi.getMetadataInfo` to retrieve a `MetadataInfo` object.  
4. **Update fields**: Set standard properties (e.g., `setTitle`, `setAuthor`) and add custom entries via `getCustomProperties().put("MyKey", "MyValue")`.  
5. **Save the changes**: Invoke `metadataApi.updateMetadataInfo` to write the modified metadata back to the file.

For more details on the classes used, refer to the [API reference](https://reference.groupdocs.cloud/metadata/).

## Edit PDF Metadata in Java - Complete Code Example

The following example demonstrates a full workflow: authentication, file upload, metadata modification, and saving the updated PDF.

{{< gist "groupdocs-cloud-gists" "75c1fea24775617738805b31e5d1ca45" "edit_pdf_metadata_in_java_complete_code_example.java" >}}

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update the file paths (`sample.pdf`, `C:/files/sample.pdf`) to match your actual file locations, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.groupdocs.cloud/metadata/) or reach out to the [support team](https://forum.groupdocs.cloud/c/metadata/30) for assistance.

## Edit PDF Metadata via REST API using cURL

If you prefer not to use the Java library, the same operation can be performed through the GroupDocs Metadata Cloud REST API.

1. **Obtain an access token**  

   ```bash
   curl -X POST "https://api.groupdocs.cloud/v2.0/oauth/token" \
        -H "Content-Type: application/json" \
        -d '{"client_id":"YOUR_CLIENT_ID","client_secret":"YOUR_CLIENT_SECRET"}'
   ```

2. **Upload the PDF file**  

   ```bash
   curl -X PUT "https://api.groupdocs.cloud/v2.0/storage/file/sample.pdf" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -H "Content-Type: application/octet-stream" \
        --data-binary "@C:/files/sample.pdf"
   ```

3. **Update metadata**  

   ```bash
   curl -X POST "https://api.groupdocs.cloud/v2.0/metadata/pdf/sample.pdf/metadata" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
              "title":"New Document Title",
              "author":"John Doe",
              "subject":"Updated Subject",
              "customProperties":{"Project":"Alpha","ReviewedBy":"Jane Smith"}
            }'
   ```

4. **Download the updated PDF**  

   ```bash
   curl -X GET "https://api.groupdocs.cloud/v2.0/storage/file/sample.pdf" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -o "C:/files/updated_sample.pdf"
   ```

These commands let you integrate PDF metadata editing into scripts, CI/CD pipelines, or any environment where installing the Java library is not practical. For a full list of endpoints, see the [API documentation](https://reference.groupdocs.cloud/metadata/).

## Conclusion

You now have a complete understanding of how to edit PDF metadata in Java using GroupDocs.Metadata Cloud SDK for Java. The guide covered reading existing metadata, modifying standard fields such as Title and Author, adding custom key‑value pairs, and persisting the changes. The SDK runs on your local machine or server and requires a valid license; you can start with a temporary license from the [license page](https://purchase.groupdocs.cloud/temporary-license/) and upgrade to a full commercial license for production use. Incorporate these techniques to keep your PDF documents well‑organized and searchable.

## FAQs

**How can I edit PDF metadata in Java using GroupDocs.Metadata Cloud SDK?**  
Use the SDK to load a PDF, modify its `MetadataInfo` properties, and save the file. See the [GroupDocs.Metadata Cloud SDK for Java](https://products.groupdocs.cloud/metadata/java/) documentation for details.

**Can I add custom key-value pairs to a PDF's metadata?**  
Yes, the SDK allows adding custom entries via the `setCustomProperties` method. Refer to the [API reference](https://reference.groupdocs.cloud/metadata/) for examples.

**Is a temporary license sufficient for development?**  
A temporary license from the [license page](https://purchase.groupdocs.cloud/temporary-license/) lets you test the SDK. For production, purchase a full license.

**Where can I find more examples for PDF metadata manipulation?**  
The official [documentation](https://docs.groupdocs.cloud/metadata/) and the [forums](https://forum.groupdocs.cloud/c/metadata/30) contain additional samples and community support.

## Read More
- [EPUB Metadata Editor: Change E-Book Metadata in Java using REST API](https://blog.groupdocs.cloud/metadata/edit-epub-metadata-in-java-using-rest-api/)
- [Edit PDF Metadata in C# - PDF Metadata Editor](https://blog.groupdocs.cloud/metadata/edit-metadata-of-pdf-files-using-rest-api-in-csharp/)
- [Extract Metadata of MP3 Files using REST API in Java](https://blog.groupdocs.cloud/metadata/extract-metadata-of-mp3-files-using-rest-api-in-java/)