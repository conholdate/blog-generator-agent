---
title: "Add Text Overlay to GIF using REST in Java"
seoTitle: "Add Text Overlay to GIF using REST in Java"
description: "Learn how to add text overlay to GIFs using GroupDocs.Watermark Cloud SDK for Java via REST API. Includes code, cURL and setup steps now. Start quickly."
date: Wed, 23 Sep 2026 13:04:19 +0000
lastmod: Wed, 23 Sep 2026 13:04:19 +0000
draft: false
url: /watermark/add-text-overlay-to-gif-using-rest-in-java/
author: "Muhammad Mustafa"
summary: "Learn how to add text overlay to GIF files with GroupDocs.Watermark Cloud SDK for Java via REST API. The tutorial covers prerequisites, SDK installation, a Java code example, matching cURL commands, and tips for adding subtitles or promotional text to GIFs."
tags: ['java rest api', 'gif text overlay', 'image watermarking']
categories: ["GroupDocs.Watermark Cloud Product Family"]
showtoc: true
cover:
   image: images/add-text-overlay-to-gif-using-rest-in-java.jpg
   alt: "Add Text Overlay to GIF using REST in Java"
   caption: "Add Text Overlay to GIF using REST in Java"
steps:
  - "Step 1: Set up your GroupDocs.Watermark Cloud account and obtain client credentials."
  - "Step 2: Install the GroupDocs.Watermark Cloud SDK for Java."
  - "Step 3: Write Java code to configure text watermark options."
  - "Step 4: Execute the API call to add the overlay to your GIF."
  - "Step 5: Verify the output GIF and adjust options as needed."
faqs:
  - q: "How can I add text Overlay to GIF using REST in Java with dynamic content?"
    a: "Use the TextWatermarkOptions class to set the text value at runtime. The [GroupDocs.Watermark Cloud SDK for Java](https://products.groupdocs.cloud/watermark/java/) lets you pass any string, so you can build subtitles or promotional messages programmatically."
  - q: "Is it possible to add subtitles to an animated GIF via the REST API?"
    a: "Yes, the same API call supports multi‑line text. Define the subtitle text in TextWatermarkOptions and set the pageRange to cover all frames."
  - q: "Can I control the font style and opacity of the overlay text?"
    a: "Absolutely. Options such as fontFamily, fontSize, color, and opacity are available in TextWatermarkOptions. Refer to the [API reference](https://reference.groupdocs.cloud/watermark/) for the full list."
  - q: "Do I need a license to use the SDK in production?"
    a: "A valid license is required for production use. You can purchase a plan on the [pricing page](https://products.groupdocs.cloud/watermark/java/) or obtain a temporary license from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/)."
---

Adding dynamic captions, subtitles, or promotional messages to animated GIFs is a common need for modern web and mobile applications. [GroupDocs.Watermark Cloud SDK for Java](https://products.groupdocs.cloud/watermark/java/) provides a powerful REST‑based library that makes this task straightforward. In this guide you will learn how to **add text Overlay to [GIF](https://docs.fileformat.com/image/gif/) using REST in Java**, see a full Java implementation, explore equivalent cURL commands, and understand the required setup steps.

## Add Text Overlay to GIF Using REST in Java - Sample Code

This example demonstrates how to configure a text watermark and apply it to every frame of a GIF file.

```java
import com.groupdocs.watermark.cloud.api.WatermarkApi;
import com.groupdocs.watermark.cloud.client.ApiException;
import com.groupdocs.watermark.cloud.client.Configuration;
import com.groupdocs.watermark.cloud.model.AddWatermarkRequest;
import com.groupdocs.watermark.cloud.model.AddWatermarkResponse;
import com.groupdocs.watermark.cloud.model.FileInfo;
import com.groupdocs.watermark.cloud.model.OutputFileInfo;
import com.groupdocs.watermark.cloud.model.TextWatermarkOptions;
import com.groupdocs.watermark.cloud.model.HorizontalAlignment;
import com.groupdocs.watermark.cloud.model.VerticalAlignment;

public class AddTextOverlayToGif {
    public static void main(String[] args) {
        // Initialize API configuration (replace with your actual clientId and clientSecret)
        Configuration config = new Configuration("YOUR_CLIENT_ID", "YOUR_CLIENT_SECRET");
        WatermarkApi watermarkApi = new WatermarkApi(config);

        // Prepare input file information
        FileInfo inputFile = new FileInfo();
        inputFile.setFilePath("input.gif");          // Path to the source GIF in the storage
        inputFile.setStorageName("MyStorage");       // Optional: name of the storage

        // Prepare output file information
        OutputFileInfo outputFile = new OutputFileInfo();
        outputFile.setFilePath("output.gif");        // Desired path for the watermarked GIF
        outputFile.setStorageName("MyStorage");      // Optional: name of the storage

        // Configure text watermark options
        TextWatermarkOptions textOptions = new TextWatermarkOptions();
        textOptions.setText("Sample Watermark");
        textOptions.setFontFamily("Arial");
        textOptions.setFontSize(24.0);
        textOptions.setColor("#FF0000");             // Red color in HEX
        textOptions.setOpacity(0.5);                 // 50% opacity
        textOptions.setRotationAngle(0.0);
        textOptions.setHorizontalAlignment(HorizontalAlignment.CENTER);
        textOptions.setVerticalAlignment(VerticalAlignment.MIDDLE);
        textOptions.setPageRange("1-");               // Apply to all frames/pages

        // Build the request
        AddWatermarkRequest request = new AddWatermarkRequest();
        request.setFileInfo(inputFile);
        request.setOutputFileInfo(outputFile);
        request.setOptions(textOptions);

        try {
            // Execute the request
            AddWatermarkResponse response = watermarkApi.addWatermark(request);
            System.out.println("Watermark added successfully. Output file: " + response.getPath());
        } catch (ApiException e) {
            System.err.println("Error while adding watermark: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.groupdocs.cloud/watermark/) or reach out to the [support team](https://forum.groupdocs.cloud/c/watermark/29) for assistance.

## Overlay Text on GIF with REST API Using cURL

Below are the cURL commands that perform the same operation from a terminal. They illustrate the full REST workflow: authentication, upload, watermarking, and download.

```bash
# 1. Obtain an access token
curl -X POST "https://api.groupdocs.cloud/v2.0/auth/token" \
     -H "Content-Type: application/json" \
     -d '{"client_id":"YOUR_CLIENT_ID","client_secret":"YOUR_CLIENT_SECRET"}'
```

Replace `YOUR_ACCESS_TOKEN` in the following calls with the token returned above.

```bash
# 2. Upload the source GIF to storage
curl -X PUT "https://api.groupdocs.cloud/v2.0/storage/file/input.gif" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/octet-stream" \
     --data-binary @path/to/local/input.gif
```

```bash
# 3. Add text overlay to the GIF
curl -X POST "https://api.groupdocs.cloud/v2.0/watermark/add" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "fileInfo": { "filePath": "input.gif", "storageName": "MyStorage" },
           "outputFileInfo": { "filePath": "output.gif", "storageName": "MyStorage" },
           "options": {
               "text": "Sample Watermark",
               "fontFamily": "Arial",
               "fontSize": 24,
               "color": "#FF0000",
               "opacity": 0.5,
               "horizontalAlignment": "Center",
               "verticalAlignment": "Middle",
               "pageRange": "1-"
           }
         }'
```

```bash
# 4. Download the watermarked GIF
curl -X GET "https://api.groupdocs.cloud/v2.0/storage/file/output.gif" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -o path/to/local/output.gif
```

For more details on request bodies and response formats, see the [official API documentation](https://docs.groupdocs.cloud/watermark/).

## Breaking Down Add Text Overlay to GIF Using REST in Java - How It Works

1. **Initialize the API client** - `new Configuration("YOUR_CLIENT_ID", "YOUR_CLIENT_SECRET")` creates a configuration object that holds your credentials. The `WatermarkApi` instance uses this configuration to sign every request.  
   ```java
   Configuration config = new Configuration("YOUR_CLIENT_ID", "YOUR_CLIENT_SECRET");
   WatermarkApi watermarkApi = new WatermarkApi(config);
   ```
   

2. **Specify source and destination files** - `FileInfo` and `OutputFileInfo` tell the service where to read the original GIF and where to write the result. Both can reference a custom storage name.  
   ```java
   FileInfo inputFile = new FileInfo();
   inputFile.setFilePath("input.gif");
   inputFile.setStorageName("MyStorage");
   ```
   

3. **Configure the text watermark** - `TextWatermarkOptions` holds all visual properties: text, font, size, color, opacity, rotation, and alignment. Setting `pageRange` to `"1-"` ensures every frame of the animated GIF receives the overlay.  
   ```java
   TextWatermarkOptions textOptions = new TextWatermarkOptions();
   textOptions.setText("Sample Watermark");
   textOptions.setFontFamily("Arial");
   textOptions.setFontSize(24.0);
   textOptions.setColor("#FF0000");
   textOptions.setOpacity(0.5);
   textOptions.setHorizontalAlignment(HorizontalAlignment.CENTER);
   textOptions.setVerticalAlignment(VerticalAlignment.MIDDLE);
   textOptions.setPageRange("1-");
   ```
   

4. **Build and send the request** - `AddWatermarkRequest` bundles the file info and options. Calling `watermarkApi.addWatermark(request)` performs the operation on the server and returns the path of the processed file.  
   ```java
   AddWatermarkRequest request = new AddWatermarkRequest();
   request.setFileInfo(inputFile);
   request.setOutputFileInfo(outputFile);
   request.setOptions(textOptions);
   AddWatermarkResponse response = watermarkApi.addWatermark(request);
   ```
   

5. **Handle the response** - The response contains the output file path. In a real application you would typically download the file or pass the path to another service.  

For a full list of classes and properties, refer to the [API reference](https://reference.groupdocs.cloud/watermark/).

## Installing and Configuring GroupDocs.Watermark Cloud SDK for Java

Add the Maven dependency to your `pom.xml` (or the equivalent Gradle entry). This pulls in version 23.8 of the SDK.

```xml
<dependency>
    <groupId>com.groupdocs</groupId>
    <artifactId>groupdocs-watermark-cloud</artifactId>
    <version>23.8</version>
</dependency>
```

**Prerequisites**

* Java 8 or higher
* An active GroupDocs Cloud account
* Client ID and Client Secret (available in the GroupDocs Cloud dashboard)

**Configuration Example**

```java
Configuration config = new Configuration("YOUR_CLIENT_ID", "YOUR_CLIENT_SECRET");
```

Download the latest JARs from the [download page](https://releases.groupdocs.cloud/watermark/java/). For production use, apply a valid license obtained from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/).

## Conclusion

Adding text Overlay to GIF using REST in Java becomes a repeatable, server‑side operation with the help of the [GroupDocs.Watermark Cloud SDK for Java](https://products.groupdocs.cloud/watermark/java/). The SDK abstracts the complexities of handling animated frames, letting you focus on the content of your subtitles or promotional messages. After integrating the sample code or the cURL workflow, you can fine‑tune font styles, colors, and opacity to match your brand. Remember to secure a production license pricing details are available on the product page, and a temporary license can be obtained for testing via the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/). Happy coding!

## FAQs

- **How do I add text Overlay to GIF using REST in Java when the text changes per user?**  
  Build the `TextWatermarkOptions` object at runtime with the user‑specific string, then invoke the same `addWatermark` call. The API processes each request independently, so dynamic content is fully supported.

- **Can I add subtitles to an animated GIF without affecting its animation speed?**  
  Yes. The watermark is applied to each frame while preserving the original frame delay. Just set `pageRange` to `"1-"` so every frame receives the same overlay.

- **What formats are supported for the overlay text color?**  
  The SDK accepts HEX color codes (e.g., `#FF0000`) and standard [HTML](https://docs.fileformat.com/web/html/) color names. See the [API reference](https://reference.groupdocs.cloud/watermark/) for the complete list.

- **Do I need a license for development and testing?**  
  A temporary license is sufficient for evaluation and testing. For production deployments, purchase a full license from the product page and apply it using the SDK's licensing API.

## Read More
- [Add Overlay Text on a GIF using REST API in C#](https://blog.groupdocs.cloud/watermark/add-overlay-text-on-a-gif-using-rest-api-in-csharp/)
- [Add Watermark to Images using Java](https://blog.groupdocs.cloud/watermark/add-watermark-to-images-using-java/)
- [Add Watermark to Word in Java - Watermark Creator](https://blog.groupdocs.cloud/watermark/add-watermark-to-word-in-java-watermark-creator/)