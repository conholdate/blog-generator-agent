---
title: "Extract Text from PDF in Node.JS"
seoTitle: "Extract Text from PDF in Node.JS"
description: "Learn how to extract text from PDF in Node.JS with GroupDocs.Parser Cloud SDK. Step‑by‑step code, cURL calls, and installation guide, including encrypted PDFs."
date: Mon, 21 Sep 2026 14:36:45 +0000
lastmod: Mon, 21 Sep 2026 14:36:45 +0000
draft: false
url: /parser/extract-text-from-pdf-in-nodejs/
author: "Muhammad Mustafa"
summary: "This guide shows Node.JS developers how to extract text from PDF documents using GroupDocs.Parser Cloud SDK. You'll see a working example, a cURL REST alternative, installation steps, and tips for processing scanned or encrypted PDFs, integrate it into workflow."
tags: ['nodejs pdf parsing', 'pdf text extraction', 'javascript file processing']
categories: ["GroupDocs.Parser Cloud Product Family"]
showtoc: true
cover:
   image: images/extract-text-from-pdf-in-nodejs.jpg
   alt: "Extract Text from PDF in Node.JS"
   caption: "Extract Text from PDF in Node.JS"
steps:
  - "Step 1: Install the GroupDocs.Parser Cloud SDK for Node.JS"
  - "Step 2: Configure your client credentials"
  - "Step 3: Build the ExtractText request"
  - "Step 4: Execute the request and handle the result"
  - "Step 5: Save the extracted text to a local file"
faqs:
  - q: "How do I extract text from PDF in Node.JS using GroupDocs.Parser?"
    a: "Use the [GroupDocs.Parser Cloud SDK for Node.JS](https://products.groupdocs.cloud/parser/nodejs/) to call the extractText method. The SDK handles plain PDFs, scanned PDFs, and encrypted PDFs."
  - q: "Can I extract text from scanned PDF in Node.JS?"
    a: "Yes. The SDK includes OCR capabilities that automatically process scanned PDF pages when you call extractText."
  - q: "What if my PDF is password protected?"
    a: "Provide the password in the FileInfo object. The SDK will decrypt the file before extracting text."
  - q: "Is there a REST alternative to the Node.JS library?"
    a: "Absolutely. You can use cURL commands against the GroupDocs.Parser Cloud REST API to achieve the same result."
---

Extracting text from [PDF](https://docs.fileformat.com/pdf) files is a frequent requirement when building document‑processing pipelines, especially for search indexing or data analysis. [GroupDocs.Parser Cloud SDK for Node.JS](https://products.groupdocs.cloud/parser/nodejs/) provides a robust library that lets you programmatically extract text from PDF in Node.JS without dealing with low‑level parsing logic. In this guide you will learn how to extract text from PDF in Node.JS using a complete code example, a cURL REST alternative, and the necessary setup steps, covering both plain and encrypted PDFs.

## Extract Text from PDF in Node.JS - Complete Code Example

The following example demonstrates how to extract text from PDF in Node.JS with GroupDocs.Parser Cloud SDK. It includes initialization, request building, execution, and saving the result to a local file.

```javascript
const GroupDocsParserCloud = require("@groupdocs/parser-cloud");
const fs = require("fs");

(async () => {
    // Initialize configuration with your credentials
    const config = new GroupDocsParserCloud.Configuration({
        clientId: "YOUR_CLIENT_ID",
        clientSecret: "YOUR_CLIENT_SECRET"
    });

    // Create Parser API instance
    const parserApi = new GroupDocsParserCloud.ParserApi(config);

    // Build request to extract text from a PDF file stored in cloud storage
    const request = new GroupDocsParserCloud.ExtractTextRequest({
        fileInfo: new GroupDocsParserCloud.FileInfo({
            filePath: "input.pdf" // path to the PDF in GroupDocs cloud storage
        })
    });

    try {
        // Execute the request
        const result = await parserApi.extractText(request);

        // result.text contains the extracted plain text
        console.log("Extracted Text:\n", result.text);

        // Save extracted text to a local file
        fs.writeFileSync("extracted.txt", result.text, "utf8");
        console.log("Text saved to extracted.txt");
    } catch (error) {
        console.error("Error extracting text:", error);
    }
})();
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.groupdocs.cloud/parser/) or reach out to the [support team](https://forum.groupdocs.cloud/c/parser/19) for assistance.

## Retrieve PDF Text Using cURL and the REST API

If you prefer a language‑agnostic approach, you can achieve the same result with cURL commands that call the GroupDocs.Parser Cloud REST API. The steps below show how to authenticate, upload a PDF, extract its text, and download the result.

```bash
# 1. Get an access token
curl -X POST "https://api.groupdocs.cloud/v2.0/auth/token" \
     -H "Content-Type: application/json" \
     -d '{"client_id":"YOUR_CLIENT_ID","client_secret":"YOUR_CLIENT_SECRET"}'
# Response contains "access_token"

# 2. Upload the PDF to cloud storage
curl -X PUT "https://api.groupdocs.cloud/v2.0/storage/file/input.pdf" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/pdf" \
     --data-binary @input.pdf

# 3. Extract text from the uploaded PDF
curl -X POST "https://api.groupdocs.cloud/v2.0/parser/extractText" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"fileInfo":{"filePath":"input.pdf"}}' \
     -o result.json

# 4. Save the extracted text locally
jq -r '.text' result.json > extracted.txt
```

These commands perform the same **extract text from PDF in Node.JS** operation, but through the cloud API, making it easy to integrate with any platform. For more details, see the [official API reference](https://reference.groupdocs.cloud/parser/).

## Breaking Down Extract Text from PDF in Node.JS

Understanding each part of the code helps you adapt it to more complex scenarios, such as processing scanned or encrypted PDFs.

1. **Configuration Initialization** -  
   ```javascript
   const config = new GroupDocsParserCloud.Configuration({
       clientId: "YOUR_CLIENT_ID",
       clientSecret: "YOUR_CLIENT_SECRET"
   });
   ```  
   This creates a configuration object that holds your authentication credentials. The class is documented in the [API reference](https://reference.groupdocs.cloud/parser/Configuration).

2. **Parser API Instance** -  
   ```javascript
   const parserApi = new GroupDocsParserCloud.ParserApi(config);
   ```  
   The `ParserApi` class provides methods for all parsing operations, including `extractText`.

3. **Building the ExtractTextRequest** -  
   ```javascript
   const request = new GroupDocsParserCloud.ExtractTextRequest({
       fileInfo: new GroupDocsParserCloud.FileInfo({
           filePath: "input.pdf"
       })
   });
   ```  
   `ExtractTextRequest` tells the service which file to process. You can also set OCR options here for scanned PDFs.

4. **Executing the Request** -  
   ```javascript
   const result = await parserApi.extractText(request);
   ```  
   The `extractText` method sends the request to the cloud and returns a response object containing the plain text.

5. **Handling the Result** -  
   ```javascript
   console.log("Extracted Text:\n", result.text);
   fs.writeFileSync("extracted.txt", result.text, "utf8");
   ```  
   The `result.text` property holds the extracted content, which you can log, store, or further process.

## Installing and Configuring GroupDocs.Parser Cloud SDK for Node.JS

Before you can run the code, install the SDK and set up your environment.

```bash
npm install groupdocs-parser-cloud
```

*Prerequisites*: Node.js 14 or later, an active GroupDocs Cloud account, and client credentials (client ID and client secret). Download the latest package from the [official download page](https://releases.groupdocs.cloud/parser/nodejs/). After installation, create a `config.json` (or use environment variables) to store your credentials securely.

## Conclusion

Extracting text from PDF in Node.JS becomes straightforward with the [GroupDocs.Parser Cloud SDK for Node.JS](https://products.groupdocs.cloud/parser/nodejs/). The SDK abstracts the complexity of PDF parsing, supports OCR for scanned PDFs, and handles encrypted documents out of the box. Remember to obtain a valid license for production use; you can purchase a subscription or request a [temporary license](https://purchase.groupdocs.cloud/temporary-license/) to evaluate the library. With the code example, cURL alternative, and installation steps covered, you're ready to integrate PDF text extraction into your document workflow and unlock powerful search and analytics capabilities.

## FAQs

- **How do I extract text from PDF in Node.JS using GroupDocs.Parser?**  
  Use the `extractText` method of `ParserApi` as shown in the complete code example. The SDK automatically returns plain text, and you can enable OCR for scanned PDFs.

- **Can I extract text from scanned PDF in Node.JS?**  
  Yes. Set OCR options in the `ExtractTextRequest` to let the service recognize text on image‑based pages.

- **What if my PDF is password protected?**  
  Include the password in the `FileInfo` object (`password: "yourPassword"`). The SDK will decrypt the file before extracting text.

- **Is there a way to call the service without writing Node.JS code?**  
  Absolutely. The cURL commands in the "Retrieve PDF Text Using cURL and the REST API" section demonstrate a language‑agnostic approach via the REST API.

## Read More
- [Extract Text from PDF in Node.js | Text Extraction API with REST](https://blog.groupdocs.cloud/parser/extract-text-from-pdf-in-nodejs/)
- [Extract Images from PDF in Node.js | PDF Image Extractor with REST API](https://blog.groupdocs.cloud/parser/extract-images-from-pdf-in-nodejs-image-extractor/)
- [Extract Text from PDF with C# .NET](https://blog.groupdocs.cloud/parser/extract-text-from-pdf-using-csharp/)