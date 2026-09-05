---
title: "Password Protect Excel via REST in Java"
seoTitle: "Password Protect Excel via REST in Java"
description: "Learn how to password protect an Excel workbook via REST in Java using GroupDocs.Merger Cloud SDK. Step-by-step guide, code sample, and cURL commands included."
date: Fri, 04 Sep 2026 12:18:34 +0000
lastmod: Fri, 04 Sep 2026 12:18:34 +0000
draft: false
url: /merger/password-protect-excel-via-rest-in-java/
author: "Muhammad Mustafa"
summary: "This tutorial shows Java developers how to password protect an Excel workbook using GroupDocs.Merger Cloud SDK via REST API. It includes prerequisites, Maven setup, a detailed code walkthrough, a complete example, and cURL commands for cloud integration."
tags: ['excel password protection', 'java rest api', 'workbook encryption']
categories: ["GroupDocs.Merger Cloud Product Family"]
showtoc: true
cover:
   image: images/password-protect-excel-via-rest-in-java.jpg
   alt: "Password Protect Excel via REST in Java"
   caption: "Password Protect Excel via REST in Java"
steps:
  - "Step 1: Set up Maven dependency and obtain credentials"
  - "Step 2: Initialize the Merger API client"
  - "Step 3: Define source and destination files"
  - "Step 4: Configure password protection options"
  - "Step 5: Execute the protect operation and handle the response"
faqs:
  - q: "How does password Protect Excel via REST in Java work with GroupDocs.Merger Cloud?"
    a: "The SDK sends a ProtectDocumentRequest containing the source XLSX file, desired output path, and password. The cloud service encrypts the workbook and stores the protected file in your storage. See the [GroupDocs.Merger Cloud SDK for Java](https://products.groupdocs.cloud/merger/java/) for details."
  - q: "Can I protect multiple Excel files in a single API call?"
    a: "The current protect endpoint works on one file per request. To handle many files, loop over them in your Java code and invoke the protect operation for each workbook."
  - q: "What authentication method is required for the REST calls?"
    a: "You must obtain an access token using your client ID and client secret. The token is then passed in the Authorization header for all subsequent API calls. Refer to the [official documentation](https://docs.groupdocs.cloud/merger/) for token acquisition."
  - q: "Do I need a license to run this in production?"
    a: "Yes. Production use requires a paid license. You can try the SDK with a temporary license from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/)."
---

Concealing sensitive data in Excel workbooks is a common requirement for enterprises that share reports internally or with partners. [GroupDocs.Merger Cloud SDK for Java](https://products.groupdocs.cloud/merger/java/) enables developers to add password protection to [XLSX](https://docs.fileformat.com/spreadsheet/xlsx/) files through a simple REST API. In this guide you will learn how to implement **password Protect Excel via REST in Java**, see a complete Java example, and run equivalent cURL commands for cloud integration.

## Prerequisites and Setup

Before you begin, make sure you have the following:

- Java 8 or higher installed.
- Maven or Gradle for dependency management.
- A GroupDocs Cloud account with **client ID** and **client secret**.
- Access to the cloud storage where the Excel files will reside.

Add the Maven dependency to your `pom.xml` (or the equivalent Gradle snippet):

<!--[CODE_SNIPPET_START]-->
```xml
<dependency>
    <groupId>com.groupdocs</groupId>
    <artifactId>groupdocs-merger-cloud</artifactId>
    <version>25.11</version>
</dependency>
```
<!--[CODE_SNIPPET_END]-->

You can download the latest JARs from the [download page](https://releases.groupdocs.cloud/merger/java/). After adding the dependency, create a configuration object with your credentials:

<!--[CODE_SNIPPET_START]-->
```java
String clientId = "YOUR_CLIENT_ID";
String clientSecret = "YOUR_CLIENT_SECRET";

Configuration config = new Configuration(clientId, clientSecret);
MergerApi mergerApi = new MergerApi(config);
```
<!--[CODE_SNIPPET_END]-->

With the client ready, you can move on to the actual password‑protect workflow.

## Password Protect Excel via REST in Java: Step-by-Step Walkthrough

### Step 1: Load the Source Document

Define the location of the source XLSX file inside your cloud storage.

<!--[CODE_SNIPPET_START]-->
```java
FileInfo inputFile = new FileInfo();
inputFile.setFilePath("input.xlsx");   // source Excel file
```
<!--[CODE_SNIPPET_END]-->

### Step 2: Set the Destination Path

Specify where the protected workbook will be saved.

<!--[CODE_SNIPPET_START]-->
```java
String outputPath = "output_protected.xlsx"; // destination file
```
<!--[CODE_SNIPPET_END]-->

### Step 3: Configure Password Protection Options

Create a `ProtectOptions` object, attach the file info, output path, and the desired password.

<!--[CODE_SNIPPET_START]-->
```java
ProtectOptions protectOptions = new ProtectOptions();
protectOptions.setFileInfo(inputFile);
protectOptions.setOutputPath(outputPath);
protectOptions.setPassword("MySecretPassword"); // desired password
```
<!--[CODE_SNIPPET_END]-->

### Step 4: Build the Protect Document Request

Wrap the options in a `ProtectDocumentRequest`.

<!--[CODE_SNIPPET_START]-->
```java
ProtectDocumentRequest request = new ProtectDocumentRequest(protectOptions);
```
<!--[CODE_SNIPPET_END]-->

### Step 5: Execute the Request and Handle the Response

Call the API method and process any errors.

<!--[CODE_SNIPPET_START]-->
```java
try {
    mergerApi.protectDocument(request);
    System.out.println("Excel file has been password protected successfully.");
    System.out.println("Protected file stored at: " + outputPath);
} catch (ApiException e) {
    System.err.println("Error while protecting the Excel file:");
    System.err.println("Status Code: " + e.getCode());
    System.err.println("Message: " + e.getMessage());
}
```
<!--[CODE_SNIPPET_END]-->

For more details on each class, refer to the [API reference](https://reference.groupdocs.cloud/merger/).

## Full Working Example for Password Protect Excel via REST in Java

The following code demonstrates the complete process from start to finish.

<!--[COMPLETE_CODE_SNIPPET_START]-->
```java
import com.groupdocs.merger.cloud.ApiException;
import com.groupdocs.merger.cloud.Configuration;
import com.groupdocs.merger.cloud.api.MergerApi;
import com.groupdocs.merger.cloud.model.FileInfo;
import com.groupdocs.merger.cloud.model.ProtectOptions;
import com.groupdocs.merger.cloud.model.requests.ProtectDocumentRequest;

public class ProtectExcelExample {
    public static void main(String[] args) {
        // Replace with your actual client credentials
        String clientId = "YOUR_CLIENT_ID";
        String clientSecret = "YOUR_CLIENT_SECRET";

        // Initialize the API configuration
        Configuration config = new Configuration(clientId, clientSecret);
        MergerApi mergerApi = new MergerApi(config);

        // Define input and output file locations (relative to the storage root)
        FileInfo inputFile = new FileInfo();
        inputFile.setFilePath("input.xlsx");          // source Excel file
        String outputPath = "output_protected.xlsx";  // destination file

        // Set password protection options
        ProtectOptions protectOptions = new ProtectOptions();
        protectOptions.setFileInfo(inputFile);
        protectOptions.setOutputPath(outputPath);
        protectOptions.setPassword("MySecretPassword"); // desired password

        // Build the request
        ProtectDocumentRequest request = new ProtectDocumentRequest(protectOptions);

        try {
            // Execute the password protection operation
            mergerApi.protectDocument(request);
            System.out.println("Excel file has been password protected successfully.");
            System.out.println("Protected file stored at: " + outputPath);
        } catch (ApiException e) {
            System.err.println("Error while protecting the Excel file:");
            System.err.println("Status Code: " + e.getCode());
            System.err.println("Message: " + e.getMessage());
        }
    }
}
```
<!--[COMPLETE_CODE_SNIPPET_END]-->

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update the file paths (`input.xlsx`, `output_protected.xlsx`) to match your actual file locations, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.groupdocs.cloud/merger/) or reach out to the [support team](https://forum.groupdocs.cloud/c/merger/18) for assistance.

## Protect Excel Workbook via REST API Using cURL

Below is a set of cURL commands that perform the same password‑protect operation directly against the REST endpoints.

**1. Authenticate and obtain an access token**

<!--[CODE_SNIPPET_START]-->
```bash
curl -X POST "https://api.groupdocs.cloud/v2.0/auth/token" \
     -H "Content-Type: application/json" \
     -d '{
           "client_id": "YOUR_CLIENT_ID",
           "client_secret": "YOUR_CLIENT_SECRET"
         }'
```
<!--[CODE_SNIPPET_END]-->

The response contains an `access_token` that you will use in subsequent calls.

**2. Upload the source XLSX file**

<!--[CODE_SNIPPET_START]-->
```bash
curl -X PUT "https://api.groupdocs.cloud/v2.0/storage/file/input.xlsx" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/octet-stream" \
     --data-binary @input.xlsx
```
<!--[CODE_SNIPPET_END]-->

**3. Request password protection**

<!--[CODE_SNIPPET_START]-->
```bash
curl -X POST "https://api.groupdocs.cloud/v2.0/merger/protect" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "fileInfo": { "filePath": "input.xlsx" },
           "outputPath": "output_protected.xlsx",
           "password": "MySecretPassword"
         }'
```
<!--[CODE_SNIPPET_END]-->

**4. Download the protected workbook**

<!--[CODE_SNIPPET_START]-->
```bash
curl -X GET "https://api.groupdocs.cloud/v2.0/storage/file/output_protected.xlsx" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -o output_protected.xlsx
```
<!--[CODE_SNIPPET_END]-->

These commands let you integrate the protection workflow into scripts or CI pipelines. For more details, see the [official API documentation](https://docs.groupdocs.cloud/merger/).

## Conclusion

Implementing **password Protect Excel via REST in Java** is straightforward with the GroupDocs.Merger Cloud SDK for Java. By following the steps above you can secure Excel workbooks, automate the process in server‑side applications, and keep sensitive data safe. Remember to acquire a proper license for production use; pricing information is available on the product page and you can start with a [temporary license](https://purchase.groupdocs.cloud/temporary-license/) to evaluate the library. Happy coding!

## FAQs

- **How does password Protect Excel via REST in Java differ from local encryption?**  
  The cloud API performs encryption on the server, so you don't need to manage cryptographic libraries locally. The SDK handles request construction and response parsing, simplifying integration.

- **Is it possible to set additional protection options, such as read‑only mode?**  
  The current `ProtectOptions` class focuses on password protection. For more advanced security features, consult the [API reference](https://reference.groupdocs.cloud/merger/) for any newer parameters.

- **What file formats are supported for password protection?**  
  The Merger API currently supports XLSX, [DOCX](https://docs.fileformat.com/word-processing/docx/), [PPTX](https://docs.fileformat.com/presentation/pptx/), and [PDF](https://docs.fileformat.com/pdf) for encryption. Refer to the [official documentation](https://docs.groupdocs.cloud/merger/) for the full list.

- **Do I need a license to run the example in a development environment?**  
  Development and testing can be done with a temporary license. Production deployments require a paid license, which you can purchase through the product page.

## Read More
- [Password-Protect PowerPoint Files in Node.js](https://blog.groupdocs.cloud/merger/password-protect-powerpoint-files-in-nodejs/)
- [Password Protect Excel Files using REST API in Python](https://blog.groupdocs.cloud/merger/password-protect-excel-files-using-rest-api-in-python/)
- [Combine Excel Sheets in Java - Excel Files Merger](https://blog.groupdocs.cloud/merger/combine-excel-sheets-in-java-excel-files-merger/)