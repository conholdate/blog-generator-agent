---
title: "PDF to DOCX Conversion in Node.JS"
seoTitle: "PDF to DOCX Conversion in Node.JS"
description: "Convert PDF to DOCX in Node.JS with GroupDocs.Conversion Cloud SDK. This guide shows async code, cURL REST calls, installation steps, and best-practice tips."
date: Mon, 03 Aug 2026 10:51:03 +0000
lastmod: Mon, 03 Aug 2026 10:51:03 +0000
draft: false
url: /conversion/pdf-to-docx-conversion-in-nodejs/
author: "Muhammad Mustafa"
summary: "Node.JS developers can convert PDF to DOCX with GroupDocs.Conversion Cloud SDK using an async code sample and equivalent cURL REST calls. This guide covers installation, configuration, and best‑practice tips for fast, reliable document conversion."
tags: ['pdf to docx', 'nodejs conversion', 'groupdocs conversion']
categories: ["GroupDocs.Conversion Cloud Product Family"]
showtoc: true
cover:
   image: images/pdf-to-docx-conversion-in-nodejs.jpg
   alt: "PDF to DOCX Conversion in Node.JS"
   caption: "PDF to DOCX Conversion in Node.JS"
steps:
  - "Step 1: Install the GroupDocs.Conversion Cloud SDK for Node.JS"
  - "Step 2: Configure your client credentials"
  - "Step 3: Upload the source PDF to GroupDocs Cloud storage"
  - "Step 4: Run the conversion code or cURL command"
  - "Step 5: Download the generated DOCX file"
faqs:
  - q: "How do I handle large PDF files during PDF to DOCX conversion in Node.JS?"
    a: "For large files, increase the timeout value in your code and consider using the asynchronous conversion endpoint. The [GroupDocs.Conversion Cloud SDK for Node.JS](https://products.groupdocs.cloud/conversion/nodejs/) supports streaming uploads to avoid memory bottlenecks."
  - q: "Can I convert password‑protected PDFs to DOCX?"
    a: "Yes. Set the password property on DocxConvertOptions before calling convertDocument. See the [official documentation](https://docs.groupdocs.cloud/conversion/) for details."
  - q: "What format options are available for the DOCX output?"
    a: "You can preserve original formatting, embed fonts, and control page layout via DocxConvertOptions. All options are listed in the [API reference](https://reference.groupdocs.cloud/conversion/)."
  - q: "Is there a way to test the conversion without a paid license?"
    a: "You can obtain a temporary license for evaluation from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/). This allows full functionality during development."
---


Converting [PDF](https://docs.fileformat.com/pdf) files to [DOCX](https://docs.fileformat.com/word-processing/docx/) format is a frequent requirement when building document‑centric applications, especially when you need editable Word output. [GroupDocs.Conversion Cloud SDK for Node.js](https://products.groupdocs.cloud/conversion/nodejs/) provides a robust API that makes this task simple and scalable. In this guide you will see a complete asynchronous code sample, learn how to achieve the same result with cURL REST calls, set up the SDK, and apply best‑practice recommendations for reliable conversions.

## Complete Code Example: Async PDF to DOCX Conversion in Node.JS

This example demonstrates how to perform an asynchronous PDF to DOCX conversion using GroupDocs.Conversion Cloud SDK for Node.js.

<!--[COMPLETE_CODE_SNIPPET_START]-->
```javascript
// PDF to DOCX conversion using GroupDocs.Conversion Cloud SDK for Node.js

const GroupDocsConversionCloud = require('groupdocs-conversion-cloud');
const path = require('path');

// -------------------- Configuration --------------------
const CLIENT_ID = process.env.GROUPDOCS_CLIENT_ID || 'YOUR_CLIENT_ID';
const CLIENT_SECRET = process.env.GROUPDOCS_CLIENT_SECRET || 'YOUR_CLIENT_SECRET';

// Initialize API client
const apiInstance = new GroupDocsConversionCloud.ConversionApi();
apiInstance.apiClient = new GroupDocsConversionCloud.ApiClient();
apiInstance.apiClient.basePath = 'https://api.groupdocs.cloud';
apiInstance.apiClient.authentications['JWT'].clientId = CLIENT_ID;
apiInstance.apiClient.authentications['JWT'].clientSecret = CLIENT_SECRET;

// -------------------- Conversion Logic --------------------
async function convertPdfToDocx() {
    try {
        // Input file information (must already be uploaded to GroupDocs Cloud storage)
        const inputFileInfo = new GroupDocsConversionCloud.FileInfo();
        inputFileInfo.filePath = path.normalize('input.pdf'); // generic path in cloud storage

        // DOCX specific conversion options (optional, shown for demonstration)
        const docxOptions = new GroupDocsConversionCloud.DocxConvertOptions();
        docxOptions.preserveOriginalFormatting = true; // keep original PDF layout as much as possible
        docxOptions.password = null; // if PDF is password protected, set it here

        // Build conversion request
        const convertRequest = new GroupDocsConversionCloud.ConvertDocumentRequest();
        convertRequest.format = 'docx';
        convertRequest.fileInfo = inputFileInfo;
        convertRequest.outputPath = path.normalize('output.docx'); // result will be stored in cloud storage
        convertRequest.options = docxOptions; // attach format‑specific options

        // Perform conversion (async)
        const conversionResult = await apiInstance.convertDocument(convertRequest);

        // conversionResult contains the path of the generated file and other metadata
        console.log('Conversion succeeded.');
        console.log('Output file path:', conversionResult.path);
        console.log('File size (bytes):', conversionResult.size);
    } catch (error) {
        // Detailed error handling
        if (error.response && error.response.body) {
            console.error('API error:', error.response.body);
        } else {
            console.error('Unexpected error:', error.message);
        }
    }
}

// -------------------- Execution --------------------
(async () => {
    // Optional: set a timeout to avoid hanging indefinitely
    const timeoutMs = 300000; // 5 minutes
    const timeout = setTimeout(() => {
        console.error('Conversion timed out after', timeoutMs / 1000, 'seconds');
        process.exit(1);
    }, timeoutMs);

    await convertPdfToDocx();

    clearTimeout(timeout);
    // Graceful shutdown
    process.exit(0);
})();
```
<!--[COMPLETE_CODE_SNIPPET_END]-->

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update the file paths (`input.pdf`, `output.docx`, etc.) to match your actual locations, verify that all required dependencies are installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.groupdocs.cloud/conversion/) or reach out to the [support team](https://forum.groupdocs.cloud/c/conversion/11) for assistance.

## Convert Documents Using cURL and the REST API

You can achieve the same PDF to DOCX conversion without writing code by calling the GroupDocs.Conversion Cloud REST endpoints directly. The steps below show how to obtain an access token, upload a PDF, start the conversion, and download the resulting DOCX file.

1. **Authenticate and get an access token**  
   Replace `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET` with your credentials.

<!--[CODE_SNIPPET_START]-->
```bash
curl -X POST "https://api.groupdocs.cloud/v1.0/oauth2/token" \
     -H "Content-Type: application/json" \
     -d '{
           "grant_type":"client_credentials",
           "client_id":"YOUR_CLIENT_ID",
           "client_secret":"YOUR_CLIENT_SECRET"
         }'
```
<!--[CODE_SNIPPET_END]-->

   The response contains `access_token` that you will use in subsequent calls.

2. **Upload the source PDF**  

<!--[CODE_SNIPPET_START]-->
```bash
curl -X PUT "https://api.groupdocs.cloud/v1.0/storage/file/input.pdf" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/pdf" \
     --data-binary @./local/input.pdf
```
<!--[CODE_SNIPPET_END]-->

3. **Execute the conversion**  

<!--[CODE_SNIPPET_START]-->
```bash
curl -X POST "https://api.groupdocs.cloud/v1.0/conversion/convert" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "format":"docx",
           "fileInfo":{"filePath":"input.pdf"},
           "outputPath":"output.docx",
           "options":{"preserveOriginalFormatting":true}
         }'
```
<!--[CODE_SNIPPET_END]-->

   The response returns the path of the generated DOCX file.

4. **Download the converted DOCX**  

<!--[CODE_SNIPPET_START]-->
```bash
curl -X GET "https://api.groupdocs.cloud/v1.0/storage/file/output.docx" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -o ./local/output.docx
```
<!--[CODE_SNIPPET_END]-->

For more details on request payloads and additional options, see the [official API documentation](https://docs.groupdocs.cloud/conversion/).

## Breaking Down PDF to DOCX Conversion in Node.JS

Below is a concise walkthrough of the key parts of the asynchronous code sample.

1. **Import and configure the client**  
   ```javascript
   const GroupDocsConversionCloud = require('groupdocs-conversion-cloud');
   const apiInstance = new GroupDocsConversionCloud.ConversionApi();
   ```  
   The `ConversionApi` class ([API reference](https://reference.groupdocs.cloud/conversion/)) is the entry point for all conversion operations.

2. **Set authentication credentials**  
   ```javascript
   apiInstance.apiClient.authentications['JWT'].clientId = CLIENT_ID;
   apiInstance.apiClient.authentications['JWT'].clientSecret = CLIENT_SECRET;
   ```  
   JWT authentication secures each request to the cloud service.

3. **Prepare the input file information**  
   ```javascript
   const inputFileInfo = new GroupDocsConversionCloud.FileInfo();
   inputFileInfo.filePath = path.normalize('input.pdf');
   ```  
   `FileInfo` tells the API where the source PDF resides in GroupDocs Cloud storage.

4. **Configure DOCX‑specific options**  
   ```javascript
   const docxOptions = new GroupDocsConversionCloud.DocxConvertOptions();
   docxOptions.preserveOriginalFormatting = true;
   ```  
   `DocxConvertOptions` lets you keep the original layout and handle passwords if needed.

5. **Create and send the conversion request**  
   ```javascript
   const convertRequest = new GroupDocsConversionCloud.ConvertDocumentRequest();
   convertRequest.format = 'docx';
   convertRequest.fileInfo = inputFileInfo;
   convertRequest.outputPath = path.normalize('output.docx');
   convertRequest.options = docxOptions;
   const conversionResult = await apiInstance.convertDocument(convertRequest);
   ```  
   The `convertDocument` method performs the actual conversion and returns metadata such as the output path and file size.

## Installing and Configuring GroupDocs.Conversion Cloud SDK for Node.JS

1. **Install the package**  

<!--[CODE_SNIPPET_START]-->
```bash
npm install groupdocs-conversion-cloud
```
<!--[CODE_SNIPPET_END]-->

   The package is available from the public npm registry. See the [download page](https://releases.groupdocs.cloud/conversion/nodejs/) for version details.

2. **Prerequisites**  
   - Node.js 12 or higher.  
   - A GroupDocs Cloud account with client ID and client secret.  

3. **Initialize the SDK in your project** (excerpt from the full example)

<!--[CODE_SNIPPET_START]-->
```javascript
const GroupDocsConversionCloud = require('groupdocs-conversion-cloud');
const apiInstance = new GroupDocsConversionCloud.ConversionApi();
apiInstance.apiClient.basePath = 'https://api.groupdocs.cloud';
```
<!--[CODE_SNIPPET_END]-->

   Adjust the `basePath` if you use a regional endpoint.

## Best Practices for High‑Performance Document Conversion

- **Reuse the API client** instead of creating a new instance for each conversion; this reduces authentication overhead.  
- **Enable streaming uploads** for large PDFs to avoid loading the entire file into memory.  
- **Set a reasonable timeout** (e.g., 5 minutes) to prevent hanging jobs while still allowing complex documents to finish.  
- **Preserve original formatting only when needed**; disabling it can speed up conversion for simple text‑only PDFs.  
- **Monitor API usage limits** in your GroupDocs account dashboard to avoid throttling during batch operations.

## Conclusion

[GroupDocs.Conversion Cloud SDK for Node.js](https://products.groupdocs.cloud/conversion/nodejs/) makes PDF to DOCX conversion straightforward, whether you prefer a full‑featured library or direct REST calls with cURL. By following the async code sample, configuring the client correctly, and applying the performance tips above, you can integrate reliable document conversion into any Node.JS service. Remember to acquire a proper license for production use; pricing details are available on the product page, and a temporary license can be obtained from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/) for evaluation.

## FAQs

- **How does PDF to DOCX conversion in Node.JS handle complex layouts?**  
  The SDK attempts to preserve original formatting by default. You can toggle `preserveOriginalFormatting` in `DocxConvertOptions` to trade fidelity for speed. See the [API reference](https://reference.groupdocs.cloud/conversion/) for all options.

- **What are the limits on file size for PDF to DOCX conversion?**  
  The cloud service accepts files up to 200 MB for free accounts; larger files require an upgraded plan. Uploads are streamed, so memory usage on your server stays low.

- **Can I convert multiple PDFs to DOCX in a single request?**  
  The API processes one document per request, but you can loop over a list of files in Node.JS and run conversions in parallel, respecting your account's concurrency limits.

- **Is there a way to test the conversion locally without a paid license?**  
  Yes, you can request a temporary evaluation license from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/). This provides full functionality for development and testing.

## Read More
- [Step-by-Step CSV to PDF Conversion Example in Node.JS](https://blog.groupdocs.cloud/conversion/step-by-step-csv-to-pdf-conversion-example-in-nodejs/)
- [Convert PDF to Word in Node.js | PDF to DOCX Online with REST API](https://blog.groupdocs.cloud/conversion/convert-pdf-to-doc-with-nodejs/)
- [Convert Word to PDF in Node.js | DOC/DOCX to PDF Online with REST API](https://blog.groupdocs.cloud/conversion/convert-doc-to-pdf-with-nodejs/)