---
title: "Convert Word Page Orientation in Node.JS"
seoTitle: "Convert Word Page Orientation in Node.JS"
description: "Learn to programmatically change Word page orientation in Node.js with GroupDocs.Merger Cloud SDK. Includes step-by-step guide, code sample, cURL and setup."
date: Wed, 26 Aug 2026 08:28:34 +0000
lastmod: Wed, 26 Aug 2026 08:28:34 +0000
draft: false
url: /merger/convert-word-page-orientation-in-nodejs/
author: "Muhammad Mustafa"
summary: "Learn how Node.js developers can change Word document orientation with GroupDocs.Merger Cloud SDK for Node.js. The guide provides step-by-step instructions, a full code example, cURL REST calls, and setup tips to integrate orientation changes into your apps."
tags: ['nodejs word processing', 'page orientation conversion', 'document manipulation']
categories: ["GroupDocs.Merger Cloud Product Family"]
showtoc: true
cover:
   image: images/convert-word-page-orientation-in-nodejs.jpg
   alt: "Convert Word Page Orientation in Node.JS"
   caption: "Convert Word Page Orientation in Node.JS"
steps:
  - "Step 1: Install the SDK and configure credentials"
  - "Step 2: Build the request object with file info and orientation"
  - "Step 3: Call the ChangePageOrientation API method"
  - "Step 4: Handle the response and verify the output"
  - "Step 5: (Optional) Adjust additional options such as page range"
faqs:
  - q: "How do I change page orientation in Word documents using Node.js?"
    a: "Use the [GroupDocs.Merger Cloud SDK for Node.js](https://products.groupdocs.cloud/merger/nodejs/) and call the ChangePageOrientation API. Set the desired orientation (Portrait or Landscape) in the request options and execute the operation."
  - q: "Can I export Word page orientation in Node.js without writing code?"
    a: "Yes, the same functionality is available via the REST API. You can send a cURL request that specifies the orientation change, which is useful for quick scripts or automation pipelines."
  - q: "What file formats are supported for orientation changes?"
    a: "The SDK works with DOCX, DOC, and other Word-compatible formats. Refer to the [official documentation](https://docs.groupdocs.cloud/merger/) for the full list of supported formats."
  - q: "Do I need a license to use the SDK in production?"
    a: "A valid license is required for production use. You can obtain a temporary license from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/) and purchase a full license as needed."
---

Converting the layout of a Word document is a frequent need when generating reports, contracts, or printable brochures. [GroupDocs.Merger Cloud SDK for Node.js](https://products.groupdocs.cloud/merger/nodejs/) enables developers to programmatically **convert Word page Orientation in Node.JS** with just a few lines of code. This guide walks you through the required steps, shows a complete working example, demonstrates equivalent cURL calls, and explains installation and configuration so you can integrate page orientation changes into your Node.js applications.

## Steps to Convert Word Page Orientation in Node.JS
1. **Install the SDK and configure credentials**: Use npm to add the library and set up your client ID and secret.  
   <!--[CODE_SNIPPET_START]-->
   ```bash
   npm install groupdocs-merger-cloud
   ```
   <!--[CODE_SNIPPET_END]-->

2. **Create the API instance**: Initialize `ChangePageOrientationApi` with the configuration object.  
   <!--[CODE_SNIPPET_START]-->
   ```javascript
   const GroupDocsMergerCloud = require('groupdocs-merger-cloud');
   const clientId = 'YOUR_CLIENT_ID';
   const clientSecret = 'YOUR_CLIENT_SECRET';
   const config = new GroupDocsMergerCloud.Configuration(clientId, clientSecret);
   const orientationApi = new GroupDocsMergerCloud.ChangePageOrientationApi(config);
   ```
   <!--[CODE_SNIPPET_END]-->

3. **Build the request options**: Define the source file, page range, desired orientation, and output path.  
   <!--[CODE_SNIPPET_START]-->
   ```javascript
   const options = new GroupDocsMergerCloud.ChangePageOrientationOptions();
   options.fileInfo = new GroupDocsMergerCloud.FileInfo();
   options.fileInfo.filePath = 'input.docx';
   options.pages = ['1-']; // all pages
   options.orientation = GroupDocsMergerCloud.Orientation.Landscape; // or Portrait
   options.outputPath = 'output.docx';
   ```
   <!--[CODE_SNIPPET_END]-->

4. **Execute the orientation change**: Send the request and handle the response.  
   <!--[CODE_SNIPPET_START]-->
   ```javascript
   const request = new GroupDocsMergerCloud.ChangePageOrientationRequest(options);
   orientationApi.changePageOrientation(request)
       .then(response => {
           console.log('Page orientation conversion completed.');
           console.log('Output stored at:', response.path);
       })
       .catch(error => {
           console.error('Error during orientation conversion:', error);
       });
   ```
   <!--[CODE_SNIPPET_END]-->

5. **(Optional) Adjust additional settings**: You can modify the `pages` array to target specific pages or switch the `orientation` enum to `Portrait` for a different layout.

## Word Page Orientation Change - Complete Code Example
The following example demonstrates the full workflow for changing the orientation of a [DOCX](https://docs.fileformat.com/word-processing/docx/) file using the GroupDocs.Merger Cloud SDK for Node.js.

<!--[COMPLETE_CODE_SNIPPET_START]-->
```javascript
const GroupDocsMergerCloud = require('groupdocs-merger-cloud');

// ==== Configuration ====
// Replace with your actual credentials
const clientId = 'YOUR_CLIENT_ID';
const clientSecret = 'YOUR_CLIENT_SECRET';
const config = new GroupDocsMergerCloud.Configuration(clientId, clientSecret);

// ==== API Instance ====
const orientationApi = new GroupDocsMergerCloud.ChangePageOrientationApi(config);

// ==== Request Construction ====
const options = new GroupDocsMergerCloud.ChangePageOrientationOptions();
options.fileInfo = new GroupDocsMergerCloud.FileInfo();
options.fileInfo.filePath = 'input.docx';               // source Word document
options.pages = ['1-'];                                 // apply to all pages (1 to end)
options.orientation = GroupDocsMergerCloud.Orientation.Landscape; // Portrait or Landscape
options.outputPath = 'output.docx';                     // destination file

const request = new GroupDocsMergerCloud.ChangePageOrientationRequest(options);

// ==== Execution ====
orientationApi.changePageOrientation(request)
    .then(response => {
        console.log('Page orientation conversion completed.');
        console.log('Output stored at:', response.path);
    })
    .catch(error => {
        console.error('Error during orientation conversion:', error);
    });
```
<!--[COMPLETE_CODE_SNIPPET_END]-->

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update the file paths (`input.docx`, `output.docx`) to match your actual file locations, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.groupdocs.cloud/merger/) or reach out to the [support team](https://forum.groupdocs.cloud/c/merger/18) for assistance.

## Changing Page Orientation via REST API with cURL
If you prefer a pure HTTP approach, the same operation can be performed with cURL commands against the GroupDocs.Merger Cloud REST endpoints.

1. **Obtain an access token**  
   ```bash
   curl -X POST "https://api.groupdocs.cloud/v1.0/oauth2/token" \
        -H "Content-Type: application/json" \
        -d '{"client_id":"YOUR_CLIENT_ID","client_secret":"YOUR_CLIENT_SECRET"}'
   ```
   The response contains `access_token`.

2. **Upload the source DOCX file**  
   ```bash
   curl -X POST "https://api.groupdocs.cloud/v1.0/merger/storage/upload" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -F "file=@input.docx" \
        -F "path=/input.docx"
   ```

3. **Request orientation change**  
   ```bash
   curl -X POST "https://api.groupdocs.cloud/v1.0/merger/words/changePageOrientation" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
              "fileInfo": { "filePath": "/input.docx" },
              "pages": ["1-"],
              "orientation": "Landscape",
              "outputPath": "/output.docx"
            }'
   ```

4. **Download the resulting file**  
   ```bash
   curl -X GET "https://api.groupdocs.cloud/v1.0/merger/storage/download?path=/output.docx" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -o output.docx
   ```

For more details on request payloads and supported parameters, see the [official API documentation](https://docs.groupdocs.cloud/merger/).

## Installing and Configuring GroupDocs.Merger Cloud SDK for Node.js
To get started, install the package from npm and configure your credentials.

```bash
npm install groupdocs-merger-cloud
```

```javascript
const GroupDocsMergerCloud = require('groupdocs-merger-cloud');
const clientId = 'YOUR_CLIENT_ID';
const clientSecret = 'YOUR_CLIENT_SECRET';
const config = new GroupDocsMergerCloud.Configuration(clientId, clientSecret);
```

Download the latest library from the [release page](https://releases.groupdocs.cloud/merger/nodejs/) if you need a specific version. Ensure your environment runs Node.js 12 or higher and that you have a valid GroupDocs Cloud account.

## Configuring Page Orientation Options
The SDK exposes several properties you can tweak:

- **pages** - Define which pages to affect (e.g., `['1-5']` for the first five pages).  
  ```javascript
  options.pages = ['1-5'];
  ```
- **orientation** - Choose `GroupDocsMergerCloud.Orientation.Portrait` or `Landscape`.  
  ```javascript
  options.orientation = GroupDocsMergerCloud.Orientation.Portrait;
  ```
- **outputPath** - Specify the destination path in your cloud storage.  
  ```javascript
  options.outputPath = 'converted/output.docx';
  ```

These options are part of the `ChangePageOrientationOptions` class documented in the [API reference](https://reference.groupdocs.cloud/merger/).

## Conclusion
Changing the layout of Word files programmatically is straightforward with the [GroupDocs.Merger Cloud SDK for Node.js](https://products.groupdocs.cloud/merger/nodejs/). By following the steps above, you can **convert Word page Orientation in Node.JS**, automate bulk processing, and integrate orientation changes into any document workflow. Remember to secure a proper license for production use; pricing details are available on the product page, and you can obtain a temporary license from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/). With the SDK installed and configured, you're ready to enhance your applications with flexible document manipulation capabilities.

## FAQs
- **How do I change page orientation in Word documents using Node.js?**  
  Use the `ChangePageOrientationApi` from the [GroupDocs.Merger Cloud SDK for Node.js](https://products.groupdocs.cloud/merger/nodejs/), set the desired `orientation` in the request options, and execute the API call.

- **Is there a way to export Word page Orientation in Node.JS without writing code?**  
  Yes, the same operation can be performed via the REST API using cURL commands, which is useful for quick scripts or integration with other systems.

- **What orientations are supported for Word documents?**  
  The SDK supports both `Portrait` and `Landscape` modes through the `Orientation` enum. You can also specify page ranges to apply the change selectively.

- **Do I need a license to run this in production?**  
  A valid license is required for production deployments. You can start with a temporary license from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/) and upgrade to a full license as your usage grows.

## Read More
- [Password-Protect ZIP File using Password Protection Software](https://blog.groupdocs.cloud/merger/password-protect-zip-file-using-password-protection-software/)
- [Password-Protect Excel using Password Protection Service](https://blog.groupdocs.cloud/merger/password-protect-excel-using-password-protection-service/)
- [How to Combine Multiple Word Documents in Node.JS](https://blog.groupdocs.cloud/merger/how-to-combine-multiple-word-documents-in-nodejs/)