---
title: "Convert HTML to JPG in Node.JS"
seoTitle: "Convert HTML to JPG in Node.JS"
description: "Learn how to convert HTML to JPG in Node.JS using Aspose.CAD Cloud SDK. This step‑by‑step guide covers installation, code implementation, and cURL API usage."
date: Mon, 14 Sep 2026 11:35:34 +0000
lastmod: Mon, 14 Sep 2026 11:35:34 +0000
draft: false
url: /cad/convert-html-to-jpg-in-nodejs/
author: "Muhammad Mustafa"
summary: "Learn to convert HTML to JPG in Node.JS using Aspose.CAD Cloud SDK for Node.js. This guide walks through installing the library, setting up credentials, writing the conversion code, and using the REST API with cURL, delivering a ready‑to‑run solution."
tags: ['html to jpg', 'nodejs image conversion', 'server side screenshot']
categories: ["Aspose.CAD Cloud Product Family"]
showtoc: true
cover:
   image: images/convert-html-to-jpg-in-nodejs.jpg
   alt: "Convert HTML to JPG in Node.JS"
   caption: "Convert HTML to JPG in Node.JS"
steps:
  - "Step 1: Install the Aspose.CAD Cloud SDK for Node.JS"
  - "Step 2: Configure your Aspose.CAD Cloud credentials"
  - "Step 3: Prepare the HTML input and JPG output paths"
  - "Step 4: Build the conversion request"
  - "Step 5: Execute the conversion and save the JPG"
faqs:
  - q: "How can I convert HTML to JPG in Node.JS using Aspose.CAD?"
    a: "Use the Aspose.CAD Cloud SDK for Node.JS to create a ConvertRequest, set the format to 'jpg', and call the convert method. See the complete code example in this guide."
  - q: "Do I need an internet connection for the conversion?"
    a: "Yes, the SDK communicates with Aspose.CAD Cloud services, so a stable internet connection is required."
  - q: "Where can I find more information about supported formats?"
    a: "The official [API Reference](https://reference.aspose.cloud/cad/) lists all supported input and output formats."
  - q: "Is a license required for production use?"
    a: "A temporary license is available at the [temporary license page](https://purchase.aspose.com/temporary-license/). For production, purchase a full license from Aspose."
---

Converting web pages into high‑resolution images is a frequent need for reporting, thumbnail generation, and email rendering. [Aspose.CAD Cloud SDK for Node.js](https://products.aspose.cloud/cad/nodejs/) provides a powerful library that makes it easy to convert [HTML](https://docs.fileformat.com/web/html/) to [JPG](https://docs.fileformat.com/image/jpg/) in Node.JS on your server. This guide walks you through installing the SDK, configuring credentials, writing the conversion code, and using the REST API with cURL, so you can integrate HTML to JPG conversion into any Node.JS application.

## Steps to Convert HTML to JPG in Node.JS

1. **Configure Aspose.CAD Cloud credentials**: Create a configuration object and set your client ID and secret.  
```javascript
const config = new CadApi.Configuration();
config.clientId = 'YOUR_CLIENT_ID';
config.clientSecret = 'YOUR_CLIENT_SECRET';
```

2. **Create the CAD API instance**: Use the configuration to instantiate the API client.  
```javascript
const cadApi = new CadApi.CadApi(config);
```

3. **Define input HTML and output JPG paths**: Resolve absolute paths for the source HTML file and the target JPG file.  
```javascript
const inputPath = path.resolve(__dirname, 'sample.html');
const outputPath = path.resolve(__dirname, 'sample.jpg');
```

4. **Prepare the conversion request**: Attach a readable stream of the HTML file and specify the output format as `jpg`.  
```javascript
const request = new CadApi.ConvertRequest();
request.inputFile = fs.createReadStream(inputPath);
request.format = 'jpg';
```

5. **Execute the conversion and save the JPG**: Call `convert`, receive a Buffer, and write it to disk. This completes the process to convert HTML to JPG in Node.JS.  
```javascript
try {
    const resultBuffer = await cadApi.convert(request);
    fs.writeFileSync(outputPath, resultBuffer);
    console.log('Conversion completed. JPG saved to:', outputPath);
} catch (err) {
    console.error('Error during conversion:', err);
}
```

For detailed class information, refer to the [API Reference](https://reference.aspose.cloud/cad/).

## Full Working Example for HTML to JPG Conversion

The following example demonstrates the complete workflow from start to finish.

```javascript
const fs = require('fs');
const path = require('path');
const CadApi = require('asposecadcloud');

async function convertHtmlToJpg() {
    // Configure Aspose.CAD Cloud credentials
    const config = new CadApi.Configuration();
    config.clientId = 'YOUR_CLIENT_ID';
    config.clientSecret = 'YOUR_CLIENT_SECRET';

    // Create API instance
    const cadApi = new CadApi.CadApi(config);

    // Define input HTML and output JPG paths
    const inputPath = path.resolve(__dirname, 'sample.html');
    const outputPath = path.resolve(__dirname, 'sample.jpg');

    // Prepare request with a readable stream and target format
    const request = new CadApi.ConvertRequest();
    request.inputFile = fs.createReadStream(inputPath);
    request.format = 'jpg';

    try {
        // Perform conversion; result is a Buffer containing JPG data
        const resultBuffer = await cadApi.convert(request);
        // Write the JPG buffer to the output file
        fs.writeFileSync(outputPath, resultBuffer);
        console.log('Conversion completed. JPG saved to:', outputPath);
    } catch (err) {
        console.error('Error during conversion:', err);
    }
}

// Execute the conversion
convertHtmlToJpg();
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.aspose.cloud/cad/) or reach out to the [support team](https://forum.aspose.cloud/c/cad/28) for assistance.

## Generate JPG from HTML Using cURL

You can achieve the same conversion via the REST API. Below are the required cURL commands.

1. **Obtain an access token**  
   Replace `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET` with your credentials.  
```bash
curl -X POST "https://api.aspose.cloud/connect/token" \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET"
```

2. **Upload the source HTML file**  
   Use the access token from the previous step.  
```bash
curl -X PUT "https://api.aspose.cloud/v3.0/cad/storage/file/sample.html" \
-H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
-H "Content-Type: text/html" \
--data-binary "@sample.html"
```

3. **Request conversion to JPG**  
   The `format` query parameter specifies the target format.  
```bash
curl -X POST "https://api.aspose.cloud/v3.0/cad/convert?format=jpg" \
-H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
-H "Content-Type: application/octet-stream" \
--data-binary "@sample.html" \
-o sample.jpg
```

4. **Download the resulting JPG** (if you used a different endpoint for conversion).  
```bash
curl -X GET "https://api.aspose.cloud/v3.0/cad/storage/file/sample.jpg" \
-H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
-o sample.jpg
```

For more details, see the [official API documentation](https://docs.aspose.cloud/cad/).

## Installing and Configuring Aspose.CAD Cloud SDK for Node.JS

Install the SDK via npm:

```bash
npm install @asposecloud/aspose-cad-cloud
```

The package is available for download at the [Release page](https://releases.aspose.cloud/cad/nodejs/).  
Make sure you have Node.js 12 or higher installed and that you have created an Aspose Cloud account to obtain your `clientId` and `clientSecret`.

## Aspose.CAD Cloud SDK Capabilities for Image Generation

- **HTML to JPG conversion** - Directly render HTML pages as high‑quality JPG images without intermediate steps.  
- **Stream‑based processing** - Accepts input as a readable stream, which is ideal for large files or when reading from memory.  
- **Multiple output formats** - Besides JPG, the SDK supports [PNG](https://docs.fileformat.com/image/png/), [BMP](https://docs.fileformat.com/image/bmp/), [GIF](https://docs.fileformat.com/image/gif/), and [TIFF](https://docs.fileformat.com/image/tiff/), allowing flexible image generation.  
- **Cloud‑hosted rendering engine** - Leverages Aspose's cloud infrastructure for fast and reliable conversions.  
- **Comprehensive API reference** - Detailed method signatures and usage examples are provided in the [API Reference](https://reference.aspose.cloud/cad/).

## Conclusion

You now know how to convert HTML to JPG in Node.JS using the powerful Aspose.CAD Cloud SDK for Node.js. The SDK handles credential management, stream processing, and format selection, giving you a ready‑to‑run solution for server‑side image generation. Remember to obtain a temporary license from the [temporary license page](https://purchase.aspose.com/temporary-license/) for testing, and purchase a full license for production deployments. Happy coding!

## FAQs

**How can I convert HTML to JPG in Node.JS using Aspose.CAD?**  
Use the Aspose.CAD Cloud SDK for Node.js to create a `ConvertRequest`, set `format` to `'jpg'`, and call the `convert` method. The full code example in this article shows the exact steps.

**Is the conversion performed locally or in the cloud?**  
The SDK sends the request to Aspose.CAD Cloud services, so the processing happens in the cloud while your Node.JS code orchestrates the workflow.

**What file formats are supported for input and output?**  
The SDK supports a wide range of CAD and image formats. For HTML to image conversion, you can output JPG, PNG, BMP, GIF, or TIFF. See the [API Reference](https://reference.aspose.cloud/cad/) for the complete list.

**Do I need to purchase a license for production use?**  
A temporary license is available for evaluation at the [temporary license page](https://purchase.aspose.com/temporary-license/). For production, you must acquire a commercial license from Aspose.

## Read More
- [Convert STL to JPG in .NET](https://blog.aspose.cloud/cad/convert-stl-to-jpg-in-dotnet/)
- [Convert DWG to PDF | Save DWG to JPG | Convert DWG to PNG using C#](https://blog.aspose.cloud/cad/convert-dwg-to-pdf-jpeg-png-using-rest-api/)
- [STL to BMP - Convert STL to BMP in C#](https://blog.aspose.cloud/cad/convert-stl-to-bmp-in-csharp/)