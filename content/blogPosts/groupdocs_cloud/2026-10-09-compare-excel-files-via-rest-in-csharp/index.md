---
title: "Compare Excel Files via REST in C#"
seoTitle: "Compare Excel Files via REST in C#"
description: "Learn how to compare Excel files via REST in C# using GroupDocs.Comparison Cloud SDK for .NET. Follow a concise guide with code, cURL, and setup steps."
date: Fri, 09 Oct 2026 14:45:06 +0000
lastmod: Fri, 09 Oct 2026 14:45:06 +0000
draft: false
url: /comparison/compare-excel-files-via-rest-in-csharp/
author: "Muhammad Mustafa"
summary: "This tutorial shows C# developers how to compare Excel files via REST in .NET using GroupDocs.Comparison Cloud SDK for .NET. Learn to upload XLSX files, set comparison options, run the comparison, download the result, and clean up, with code and cURL examples."
tags: ['excel comparison', 'rest api', 'csharp']
categories: ["GroupDocs.Comparison Cloud Product Family"]
showtoc: true
cover:
   image: images/compare-excel-files-via-rest-in-csharp.jpg
   alt: "Compare Excel Files via REST in C#"
   caption: "Compare Excel Files via REST in C#"
steps:
  - "Step 1: Upload the source XLSX file to GroupDocs storage"
  - "Step 2: Upload the target XLSX file to GroupDocs storage"
  - "Step 3: Configure CompareOptions with desired settings"
  - "Step 4: Execute the comparison request"
  - "Step 5: Download the result and clean up remote files"
faqs:
  - q: "How do I compare Excel files via REST in C# using GroupDocs.Comparison?"
    a: "Use the GroupDocs.Comparison Cloud SDK for .NET to upload two XLSX files, call the CompareDocument API, and download the result. The full workflow is demonstrated in this guide."
  - q: "What authentication method is required for the REST API?"
    a: "The API uses client‑id and client‑secret to obtain an OAuth token. Include the token in the Authorization header for all requests."
  - q: "Can I customize which changes are highlighted in the comparison result?"
    a: "Yes, the Settings object inside CompareOptions lets you enable GenerateSummaryPage, ShowDeletedContent, and ShowInsertedContent. Adjust these flags to suit your needs."
  - q: "Is a temporary license sufficient for testing?"
    a: "A temporary license from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/) works for development and testing. For production, purchase a full license."
---

Comparing Excel worksheets programmatically is a frequent requirement when you need to detect data changes, audit revisions, or generate reports. [GroupDocs.Comparison Cloud SDK for .NET](https://products.groupdocs.cloud/comparison/net/) provides a powerful REST‑based library that makes it easy to compare Excel files via REST in C#. This guide walks you through uploading files, configuring comparison options, executing the comparison, and retrieving the result, with both C# code and cURL examples.

## Compare Excel Files via REST in C# in 5 Steps
1. **Upload the source [XLSX](https://docs.fileformat.com/spreadsheet/xlsx/) file**: Use the `StorageApi.UploadFile` method to place `sample1.xlsx` in cloud storage.  
```csharp
using (var stream1 = new FileStream(localFilePath1, FileMode.Open, FileAccess.Read))
{
    var uploadRequest1 = new UploadFileRequest(remoteFilePath1, stream1);
    storageApi.UploadFile(uploadRequest1);
}
```
   
2. **Upload the target XLSX file**: Repeat the upload for `sample2.xlsx`.  
```csharp
using (var stream2 = new FileStream(localFilePath2, FileMode.Open, FileAccess.Read))
{
    var uploadRequest2 = new UploadFileRequest(remoteFilePath2, stream2);
    storageApi.UploadFile(uploadRequest2);
}
```
   
3. **Configure comparison options**: Create a `CompareOptions` object, set the source and target file paths, define the output path, and adjust settings such as `GenerateSummaryPage`.  
```csharp
var compareOptions = new CompareOptions
{
    SourceFile = new FileInfo { FilePath = remoteFilePath1 },
    TargetFiles = new List<FileInfo>
    {
        new FileInfo { FilePath = remoteFilePath2 }
    },
    OutputPath = remoteResultPath,
    Settings = new Settings
    {
        GenerateSummaryPage = true,
        ShowDeletedContent = true,
        ShowInsertedContent = true
    }
};
```
   
   See the full API reference for `CompareOptions` and `Settings` at the [API Reference](https://reference.groupdocs.cloud/comparison/).  
4. **Execute the comparison**: Call `CompareApi.CompareDocument` with a `CompareDocumentRequest`.  
```csharp
var compareRequest = new CompareDocumentRequest(compareOptions);
var compareResult = compareApi.CompareDocument(compareRequest);
```
   
5. **Download the result and clean up**: Retrieve the generated `result.xlsx`, save it locally, and optionally delete the remote files.  
```csharp
var downloadRequest = new DownloadFileRequest(compareResult.Path);
using (var resultStream = storageApi.DownloadFile(downloadRequest))
using (var fileStream = new FileStream(localResultPath, FileMode.Create, FileAccess.Write))
{
    resultStream.CopyTo(fileStream);
}

// Clean up
storageApi.DeleteFile(new DeleteFileRequest(remoteFilePath1));
storageApi.DeleteFile(new DeleteFileRequest(remoteFilePath2));
storageApi.DeleteFile(new DeleteFileRequest(remoteResultPath));
```
   

## Complete Code Example: Compare Excel Files via REST in C# Using GroupDocs.Comparison
This example demonstrates how to upload two XLSX files, compare them, and download the highlighted result.

```csharp
using System;
using System.Collections.Generic;
using System.IO;
using GroupDocs.Comparison.Cloud.Sdk.Api;
using GroupDocs.Comparison.Cloud.Sdk.Client;
using GroupDocs.Comparison.Cloud.Sdk.Model;
using GroupDocs.Comparison.Cloud.Sdk.Model.Requests;

namespace CompareExcelFilesExample
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
            var compareApi = new CompareApi(config);
            var storageApi = new StorageApi(config);

            // Local and remote file names
            string localFilePath1 = "sample1.xlsx";
            string localFilePath2 = "sample2.xlsx";
            string remoteFilePath1 = "sample1.xlsx";
            string remoteFilePath2 = "sample2.xlsx";
            string remoteResultPath = "result.xlsx";
            string localResultPath = "result.xlsx";

            // Upload first Excel file
            using (var stream1 = new FileStream(localFilePath1, FileMode.Open, FileAccess.Read))
            {
                var uploadRequest1 = new UploadFileRequest(remoteFilePath1, stream1);
                storageApi.UploadFile(uploadRequest1);
            }

            // Upload second Excel file
            using (var stream2 = new FileStream(localFilePath2, FileMode.Open, FileAccess.Read))
            {
                var uploadRequest2 = new UploadFileRequest(remoteFilePath2, stream2);
                storageApi.UploadFile(uploadRequest2);
            }

            // Prepare comparison options
            var compareOptions = new CompareOptions
            {
                SourceFile = new FileInfo { FilePath = remoteFilePath1 },
                TargetFiles = new List<FileInfo>
                {
                    new FileInfo { FilePath = remoteFilePath2 }
                },
                OutputPath = remoteResultPath,
                Settings = new Settings
                {
                    // Example: show changes in a new sheet
                    GenerateSummaryPage = true,
                    ShowDeletedContent = true,
                    ShowInsertedContent = true
                }
            };

            // Execute comparison
            var compareRequest = new CompareDocumentRequest(compareOptions);
            var compareResult = compareApi.CompareDocument(compareRequest);

            // Download the result file
            var downloadRequest = new DownloadFileRequest(compareResult.Path);
            using (var resultStream = storageApi.DownloadFile(downloadRequest))
            using (var fileStream = new FileStream(localResultPath, FileMode.Create, FileAccess.Write))
            {
                resultStream.CopyTo(fileStream);
            }

            // Optional: clean up remote files
            storageApi.DeleteFile(new DeleteFileRequest(remoteFilePath1));
            storageApi.DeleteFile(new DeleteFileRequest(remoteFilePath2));
            storageApi.DeleteFile(new DeleteFileRequest(remoteResultPath));

            Console.WriteLine("Comparison completed. Result saved to " + localResultPath);
        }
    }
}
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.groupdocs.cloud/comparison/) or reach out to the [support team](https://forum.groupdocs.cloud/c/comparison/12) for assistance.

## Calling the Comparison REST API with cURL
Below is a cURL workflow that performs the same operation without writing C# code. Replace placeholder values with your actual credentials and file names.

1. **Obtain an access token**  
   ```bash
   curl -X POST "https://api.groupdocs.cloud/v2.0/oauth2/token" \
        -H "Content-Type: application/json" \
        -d '{"client_id":"YOUR_CLIENT_ID","client_secret":"YOUR_CLIENT_SECRET"}'
   ```
2. **Upload the source XLSX file**  
   ```bash
   curl -X PUT "https://api.groupdocs.cloud/v2.0/storage/file/sample1.xlsx" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -H "Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" \
        --data-binary "@sample1.xlsx"
   ```
3. **Upload the target XLSX file**  
   ```bash
   curl -X PUT "https://api.groupdocs.cloud/v2.0/storage/file/sample2.xlsx" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -H "Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" \
        --data-binary "@sample2.xlsx"
   ```
4. **Run the comparison**  
   ```bash
   curl -X POST "https://api.groupdocs.cloud/v2.0/comparison/compare" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
              "source_file": {"file_path": "sample1.xlsx"},
              "target_files": [{"file_path": "sample2.xlsx"}],
              "output_path": "result.xlsx",
              "settings": {
                  "generate_summary_page": true,
                  "show_deleted_content": true,
                  "show_inserted_content": true
              }
            }'
   ```
5. **Download the result**  
   ```bash
   curl -X GET "https://api.groupdocs.cloud/v2.0/storage/file/result.xlsx" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -o result.xlsx
   ```

For a complete list of endpoints and parameters, see the [official API documentation](https://docs.groupdocs.cloud/comparison/).

## Prerequisites and Setup
1. Install the .NET package via NuGet:  
```bash
dotnet add package GroupDocs.Comparison-Cloud
```
   
2. Ensure you have a valid GroupDocs Cloud account and obtain your **Client Id** and **Client Secret** from the dashboard.  
3. .NET 6.0 or later is required.  

You can download the latest library from the [download page](https://releases.groupdocs.cloud/comparison/net/).

## Fine-Tuning Comparison Settings
The `Settings` object inside `CompareOptions` lets you control the output. Common adjustments include:

- **GenerateSummaryPage** - adds a summary sheet with change statistics.  
- **ShowDeletedContent** - highlights cells that were removed.  
- **ShowInsertedContent** - highlights newly added cells.  

These properties are already used in the code example above. For additional options such as `Password` protection or `StyleChangeDetection`, refer to the [API Reference](https://reference.groupdocs.cloud/comparison/).

## Conclusion
Comparing Excel files via REST in C# becomes straightforward with the [GroupDocs.Comparison Cloud SDK for .NET](https://products.groupdocs.cloud/comparison/net/). By following the steps, you can upload XLSX files, configure detailed comparison settings, execute the comparison, and retrieve a result workbook that clearly marks differences. Remember to secure your API credentials, respect file size limits, and use a temporary license for development. When you're ready for production, purchase a full license from the [pricing page](https://purchase.groupdocs.cloud/temporary-license/) to unlock unlimited usage.

## FAQs
- **How do I compare Excel files via REST in C# using GroupDocs.Comparison?**  
  Use the SDK to upload two XLSX files, set `CompareOptions`, call `CompareDocument`, and download the resulting file. The full workflow is illustrated in the code and cURL sections above.

- **What authentication method does the REST API require?**  
  The API uses OAuth 2.0 with your client‑id and client‑secret to obtain an access token, which must be sent in the `Authorization: Bearer` header for every request.

- **Can I customize which changes are highlighted in the comparison result?**  
  Yes. Adjust the `Settings` object (e.g., `GenerateSummaryPage`, `ShowDeletedContent`, `ShowInsertedContent`) to control the appearance of differences.

- **Is a temporary license enough for testing?**  
  A temporary license from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/) works for development and testing. For production deployments, acquire a full license.

## Read More
- [Compare Excel Files using REST API in Python](https://blog.groupdocs.cloud/comparison/compare-excel-files-using-rest-api-in-python/)
- [Compare Excel Files and Highlight Differences in Java using REST API](https://blog.groupdocs.cloud/comparison/compare-two-excel-sheets-and-highlight-differences-using-java/)
- [Compare PDF Files using REST API in Python](https://blog.groupdocs.cloud/comparison/compare-pdf-files-using-rest-api-in-python/)