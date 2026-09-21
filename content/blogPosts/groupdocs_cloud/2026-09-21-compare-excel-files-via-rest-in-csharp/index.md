---
title: "Compare Excel Files via REST in C#"
seoTitle: "Compare Excel Files via REST in C#"
description: "Learn how to compare Excel files in .NET using GroupDocs.Comparison Cloud SDK. This guide shows REST integration, C# code, cURL commands, and tips."
date: Mon, 21 Sep 2026 11:32:39 +0000
lastmod: Mon, 21 Sep 2026 11:32:39 +0000
draft: false
url: /comparison/compare-excel-files-via-rest-in-csharp/
author: "Muhammad Mustafa"
summary: "This tutorial demonstrates how to compare Excel files in .NET with GroupDocs.Comparison Cloud SDK. You will learn to set up the library, upload workbooks, call the REST API from C#, view change logs, and customize comparison settings for spreadsheet diff results."
tags: ['excel comparison', 'csharp rest api', 'spreadsheet diff']
categories: ["GroupDocs.Comparison Cloud Product Family"]
showtoc: true
cover:
   image: images/compare-excel-files-via-rest-in-csharp.jpg
   alt: "Compare Excel Files via REST in C#"
   caption: "Compare Excel Files via REST in C#"
steps:
  - "Step 1: Install the SDK and configure credentials"
  - "Step 2: Prepare source and target Excel files"
  - "Step 3: Define comparison options and settings"
  - "Step 4: Execute the comparison and process results"
  - "Step 5: Retrieve detailed change log"
faqs:
  - q: "How can I compare Excel files in .NET using GroupDocs.Comparison Cloud?"
    a: "Use the Compare API of [GroupDocs.Comparison Cloud SDK for .NET](https://products.groupdocs.cloud/comparison/net/) to submit two XLSX workbooks and receive a diff file with highlighted changes."
  - q: "What REST endpoint is used to perform the comparison?"
    a: "The SDK calls the /comparison/compare endpoint; you can invoke the same operation with cURL as shown in this guide."
  - q: "Can I customize which changes are shown in the diff result?"
    a: "Yes, the Settings object lets you toggle ShowDeletedContent, ShowInsertedContent, ShowStyleChanges, and GenerateSummaryPage. See the API reference for more options."
  - q: "Is a license required for production use?"
    a: "A valid license is needed. You can obtain a temporary license from the [license page](https://purchase.groupdocs.cloud/temporary-license/) and purchase a full license on the product site."
---

Analyzing changes between spreadsheet versions is a routine task for finance, reporting, and data‑validation workflows. [GroupDocs.Comparison Cloud SDK for .NET](https://products.groupdocs.cloud/comparison/net/) provides a powerful API that makes it easy to compare Excel files in .NET without manual inspection. In this guide you will see how to set up the library, upload workbooks, call the REST endpoint from C#, retrieve detailed change information, and fine‑tune comparison options for precise results.

## Before You Start: Prerequisites and Installation

Before you begin, ensure you have the following:

- .NET 6.0 or later installed.
- An IDE such as Visual Studio 2022.
- A GroupDocs Cloud account with **ClientId** and **ClientSecret**.
- Access to the GroupDocs Cloud storage where the Excel files will be uploaded.

Install the SDK via NuGet:

```bash
dotnet add package GroupDocs.Comparison-Cloud
```

Download the latest package from the [release page](https://releases.groupdocs.cloud/comparison/net/). After installation, add your credentials in code as shown later. You are now ready to start the comparison workflow.

## Step-by-Step Guide to Compare Excel Files in .NET

The following steps illustrate how to compare Excel files in .NET using the SDK.

### Step 1: Load the Source and Target Documents

Create a configuration object with your credentials and instantiate the `CompareApi`.

```csharp
var config = new Configuration
{
    ClientId = "YOUR_CLIENT_ID",
    ClientSecret = "YOUR_CLIENT_SECRET"
};

var compareApi = new CompareApi(config);
```

### Step 2: Prepare the Excel Workbooks

Define `FileInfo` objects that point to the source and target [XLSX](https://docs.fileformat.com/spreadsheet/xlsx/) files stored in GroupDocs Cloud storage.

```csharp
var sourceFile = new FileInfo { FilePath = "input/source.xlsx" };
var targetFile = new FileInfo { FilePath = "input/target.xlsx" };
```

### Step 3: Set Comparison Options and Settings

Configure the `CompareOptions` object, including detailed change settings.

```csharp
var compareOptions = new CompareOptions
{
    SourceFile = sourceFile,
    TargetFiles = new List<FileInfo> { targetFile },
    OutputPath = "output/diff_result.xlsx",
    Settings = new Settings
    {
        ShowDeletedContent = true,
        ShowInsertedContent = true,
        ShowStyleChanges = true,
        GenerateSummaryPage = true
    }
};
```

For a full list of settings, refer to the [API reference](https://reference.groupdocs.cloud/comparison/).

### Step 4: Execute the Comparison and Process Results

Call the `Compare` method and read the basic result information.

```csharp
var compareResult = compareApi.Compare(compareOptions);
Console.WriteLine($"Comparison completed. Result file: {compareResult.Path}");
Console.WriteLine($"Number of changes detected: {compareResult.Changes?.Count ?? 0}");
```

### Step 5: Retrieve Detailed Change Information

If you need a granular report, use the `GetChanges` request.

```csharp
var changesRequest = new GetChangesRequest
{
    SourceFile = sourceFile,
    TargetFile = targetFile,
    OutputPath = "output/detailed_changes.json"
};
var detailedChanges = compareApi.GetChanges(changesRequest);
Console.WriteLine($"Detailed changes saved to: {detailedChanges.Path}");
```

With these steps you have fully automated the process of comparing Excel files in .NET.

## Comparing Excel Files Programmatically - Complete Code Example

The following code demonstrates the complete workflow from configuration to result handling.

```csharp
using System;
using System.Collections.Generic;
using GroupDocs.Comparison.Cloud.Sdk.Api;
using GroupDocs.Comparison.Cloud.Sdk.Client;
using GroupDocs.Comparison.Cloud.Sdk.Model;

namespace CompareExcelDemo
{
    class Program
    {
        static void Main(string[] args)
        {
            // Set up API credentials (replace with your actual credentials)
            var config = new Configuration
            {
                ClientId = "YOUR_CLIENT_ID",
                ClientSecret = "YOUR_CLIENT_SECRET"
            };

            // Initialize Compare API
            var compareApi = new CompareApi(config);

            // Prepare source and target Excel files (must be uploaded to GroupDocs Cloud storage beforehand)
            var sourceFile = new FileInfo { FilePath = "input/source.xlsx" };
            var targetFile = new FileInfo { FilePath = "input/target.xlsx" };

            // Define comparison options
            var compareOptions = new CompareOptions
            {
                SourceFile = sourceFile,
                TargetFiles = new List<FileInfo> { targetFile },
                OutputPath = "output/diff_result.xlsx",
                // Optional: specify that we want detailed changes for worksheets
                Settings = new Settings
                {
                    ShowDeletedContent = true,
                    ShowInsertedContent = true,
                    ShowStyleChanges = true,
                    GenerateSummaryPage = true
                }
            };

            try
            {
                // Call the Compare API
                var compareResult = compareApi.Compare(compareOptions);

                // Output basic result information
                Console.WriteLine($"Comparison completed. Result file: {compareResult.Path}");
                Console.WriteLine($"Number of changes detected: {compareResult.Changes?.Count ?? 0}");

                // Iterate through change details
                if (compareResult.Changes != null)
                {
                    foreach (var change in compareResult.Changes)
                    {
                        Console.WriteLine("--------------------------------------------------");
                        Console.WriteLine($"Change Type   : {change.ChangeType}");
                        Console.WriteLine($"Worksheet     : {change.Worksheet}");
                        Console.WriteLine($"Cell Address  : {change.CellAddress}");
                        Console.WriteLine($"Old Value     : {change.OldValue}");
                        Console.WriteLine($"New Value     : {change.NewValue}");
                        Console.WriteLine($"Is New Row    : {change.IsNewRow}");
                        Console.WriteLine($"Is New Column : {change.IsNewColumn}");
                    }
                }

                // Retrieve detailed changes via GetChanges (optional)
                var changesRequest = new GetChangesRequest
                {
                    SourceFile = sourceFile,
                    TargetFile = targetFile,
                    OutputPath = "output/detailed_changes.json"
                };
                var detailedChanges = compareApi.GetChanges(changesRequest);
                Console.WriteLine($"Detailed changes saved to: {detailedChanges.Path}");
            }
            catch (ApiException apiEx)
            {
                Console.WriteLine($"API error: {apiEx.ErrorCode} - {apiEx.Message}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Unexpected error: {ex.Message}");
            }
        }
    }
}
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.groupdocs.cloud/comparison/) or reach out to the [support team](https://forum.groupdocs.cloud/c/comparison/12) for assistance.

## Perform Excel Comparison via REST with cURL

You can achieve the same result without writing C# code by calling the REST API directly.

**1. Authenticate and Get Access Token**

```bash
curl -X POST "https://api.groupdocs.cloud/v1.0/oauth2/token" \
     -H "Content-Type: application/json" \
     -d '{"client_id":"YOUR_CLIENT_ID","client_secret":"YOUR_CLIENT_SECRET"}'
```

**2. Upload the Source Workbook**

```bash
curl -X PUT "https://api.groupdocs.cloud/v1.0/storage/file?path=input/source.xlsx" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -T "./source.xlsx"
```

**3. Upload the Target Workbook**

```bash
curl -X PUT "https://api.groupdocs.cloud/v1.0/storage/file?path=input/target.xlsx" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -T "./target.xlsx"
```

**4. Execute the Comparison**

```bash
curl -X POST "https://api.groupdocs.cloud/v1.0/comparison/compare" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "source_file": {"file_path":"input/source.xlsx"},
           "target_files": [{"file_path":"input/target.xlsx"}],
           "output_path":"output/diff_result.xlsx",
           "settings": {
               "show_deleted_content": true,
               "show_inserted_content": true,
               "show_style_changes": true,
               "generate_summary_page": true
           }
         }'
```

**5. Download the Resulting Diff Workbook**

```bash
curl -X GET "https://api.groupdocs.cloud/v1.0/storage/file?path=output/diff_result.xlsx" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -o diff_result.xlsx
```

For a complete list of parameters, see the [official API documentation](https://docs.groupdocs.cloud/comparison/).

## Fine-Tuning Comparison Settings

The `Settings` object gives you control over what changes are highlighted:

- **ShowDeletedContent** - Marks cells that were removed.
- **ShowInsertedContent** - Highlights newly added cells.
- **ShowStyleChanges** - Indicates formatting differences such as font or fill color.
- **GenerateSummaryPage** - Adds a summary worksheet that lists all changes.

You can adjust these options directly in the `CompareOptions` object, as shown in the code snippet above. Additional options like `Password` for protected workbooks or `CompareOptions` for ignoring case can be explored in the [API reference](https://reference.groupdocs.cloud/comparison/).

## Conclusion

Using the **GroupDocs.Comparison Cloud SDK for .NET** you can easily compare Excel files in .NET and obtain a detailed diff workbook that highlights every modification. The SDK's REST‑based architecture lets you integrate spreadsheet comparison into any C# service, web API, or background job with minimal effort. Remember to acquire a proper license for production use; a temporary license is available from the [license page](https://purchase.groupdocs.cloud/temporary-license/) and full licensing details are listed on the product site. Start automating your Excel diff workflows today and eliminate manual inspection errors.

## FAQs

- **How can I compare Excel files in .NET without writing a lot of code?**  
  The SDK abstracts the heavy lifting. You only need to configure credentials, point to the two XLSX files, and call `compareApi.Compare`. The library returns a diff file and a list of change objects.

- **What format does the diff result use?**  
  By default the result is saved as an XLSX workbook, preserving the original layout while applying visual markers for deletions, insertions, and style changes.

- **Is it possible to compare protected Excel workbooks?**  
  Yes. Provide the password in the `FileInfo` object's `Password` property. The API will unlock the workbook before performing the comparison.

- **Do I need a license for development and testing?**  
  A temporary license can be obtained from the [license page](https://purchase.groupdocs.cloud/temporary-license/). For production deployments you must purchase a full license as described on the product page.

## Read More
- [Compare Excel Files using REST API in Python](https://blog.groupdocs.cloud/comparison/compare-excel-files-using-rest-api-in-python/)
- [Compare Excel Files and Highlight Differences in Java using REST API](https://blog.groupdocs.cloud/comparison/compare-two-excel-sheets-and-highlight-differences-using-java/)
- [Compare PDF Files using REST API in Python](https://blog.groupdocs.cloud/comparison/compare-pdf-files-using-rest-api-in-python/)