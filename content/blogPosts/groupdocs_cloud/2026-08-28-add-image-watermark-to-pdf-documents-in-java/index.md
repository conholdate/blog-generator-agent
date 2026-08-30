---
title: "Add Image Watermark to PDF Documents in Java"
seoTitle: "Add Image Watermark to PDF Documents in Java"
description: "Learn how to add an image watermark to PDF documents in Java using GroupDocs.Watermark Cloud SDK. Step-by-step guide with code, cURL and configuration tips."
date: Fri, 28 Aug 2026 19:41:04 +0000
lastmod: Fri, 28 Aug 2026 19:41:04 +0000
draft: false
url: /watermark/add-image-watermark-to-pdf-documents-in-java/
author: "Muhammad Mustafa"
summary: "Learn how Java developers can add an image watermark to PDF documents with GroupDocs.Watermark Cloud SDK for Java. The guide includes a full code example, cURL REST calls, and tips for configuring opacity, scaling, alignment and margins."
tags: ['java pdf watermark', 'image watermark', 'pdf manipulation']
categories: ["GroupDocs.Watermark Cloud Product Family"]
showtoc: true
cover:
   image: images/add-image-watermark-to-pdf-documents-in-java.jpg
   alt: "Add Image Watermark to PDF Documents in Java"
   caption: "Add Image Watermark to PDF Documents in Java"
steps:
  - "Initialize the API client with your credentials"
  - "Specify the source PDF file information"
  - "Configure the image watermark properties"
  - "Set watermark options and output path"
  - "Execute the addWatermark request and handle the response"
faqs:
  - q: "What file formats are supported for the source document when adding an image watermark in Java?"
    a: "The API works with any format supported by GroupDocs.Watermark, including PDF, DOCX, PPTX and more. See the full list in the [official documentation](https://docs.groupdocs.cloud/watermark/)."
  - q: "How do I control the opacity of the image watermark?"
    a: "Set the opacity value (0.0 - 1.0) on the ImageWatermark object. For example, imageWatermark.setOpacity(0.5) creates a 50 % transparent watermark. Refer to the [API reference](https://reference.groupdocs.cloud/watermark/) for all properties."
  - q: "Can I use this library in a cloud‑only environment without installing anything locally?"
    a: "Yes. The GroupDocs.Watermark Cloud SDK for Java is a cloud‑based library that runs on your server or container. You only need to add the Maven dependency and provide your client credentials."
  - q: "What if the watermark image file is missing or the path is incorrect?"
    a: "The service returns a clear error message indicating the missing resource. Verify the image path and ensure the file is uploaded to the storage before calling the API."
---


Adding a visual identifier to [PDF](https://docs.fileformat.com/pdf) files is essential for protecting intellectual property and branding documents. [GroupDocs.Watermark Cloud SDK for Java](https://products.groupdocs.cloud/watermark/java/) offers a straightforward API to embed image watermarks directly into PDFs from your Java application. In this tutorial you will learn how to add image watermark to PDF documents in Java, see a complete working example, and explore the equivalent cURL REST calls for cloud integration.

## Add Image Watermark to PDF Documents in Java in 5 Steps

1. **Initialize the API client**: Create an `ApiClient` instance with your client ID and secret.  
   <!--[CODE_SNIPPET_START]-->
   ```java
   ApiClient apiClient = new ApiClient("YOUR_CLIENT_ID", "YOUR_CLIENT_SECRET");
   WatermarkApi watermarkApi = new WatermarkApi(apiClient);
   ```
   <!--[CODE_SNIPPET_END]-->  
   This step connects your Java code to the GroupDocs.Watermark Cloud service. See the [API reference](https://reference.groupdocs.cloud/watermark/) for more details.

2. **Specify the source PDF file**: Build a `FileInfo` object that points to the PDF you want to watermark.  
   <!--[CODE_SNIPPET_START]-->
   ```java
   FileInfo fileInfo = new FileInfo();
   fileInfo.setFilePath("input.pdf");
   ```
   <!--[CODE_SNIPPET_END]-->  
   The file must be uploaded to your GroupDocs storage before the request.

3. **Configure the image watermark**: Define the image path, opacity, scale factor, rotation and alignment.  
   <!--[CODE_SNIPPET_START]-->
   ```java
   ImageWatermark imageWatermark = new ImageWatermark();
   imageWatermark.setImagePath("watermark.png");
   imageWatermark.setOpacity(0.5);
   imageWatermark.setScaleFactor(0.3);
   imageWatermark.setHorizontalAlignment(HorizontalAlignment.CENTER);
   imageWatermark.setVerticalAlignment(VerticalAlignment.CENTER);
   imageWatermark.setMargin(new Margin(10, 10, 10, 10));
   ```
   <!--[CODE_SNIPPET_END]-->  
   Adjust these values to achieve the desired appearance opacity controls transparency, while scaleFactor determines the size relative to the page.

4. **Set watermark options and output path**: Combine the file info and watermark into a `WatermarkOptions` object.  
   <!--[CODE_SNIPPET_START]-->
   ```java
   WatermarkOptions options = new WatermarkOptions();
   options.setFileInfo(fileInfo);
   options.setImageWatermark(imageWatermark);
   options.setOutputPath("output.pdf");
   ```
   <!--[CODE_SNIPPET_END]-->  
   The `outputPath` tells the service where to store the resulting PDF.

5. **Execute the request**: Build an `AddWatermarkRequest` and call the API. Handle success or error responses.  
   <!--[CODE_SNIPPET_START]-->
   ```java
   AddWatermarkRequest request = new AddWatermarkRequest(options);
   try {
       AddWatermarkResponse response = watermarkApi.addWatermark(request);
       System.out.println("Watermark added successfully. Output file: " + response.getPath());
   } catch (Exception e) {
       System.err.println("Error adding watermark: " + e.getMessage());
   }
   ```
   <!--[CODE_SNIPPET_END]-->  
   After execution, the watermarked PDF is available at the location you specified.

## Complete Code Example: Add Image Watermark to PDF Documents in Java

The following example demonstrates the full implementation from client initialization to saving the watermarked PDF.

<!--[COMPLETE_CODE_SNIPPET_START]-->
```java
import com.groupdocs.cloud.watermark.api.WatermarkApi;
import com.groupdocs.cloud.watermark.client.ApiClient;
import com.groupdocs.cloud.watermark.model.AddWatermarkRequest;
import com.groupdocs.cloud.watermark.model.AddWatermarkResponse;
import com.groupdocs.cloud.watermark.model.FileInfo;
import com.groupdocs.cloud.watermark.model.ImageWatermark;
import com.groupdocs.cloud.watermark.model.Margin;
import com.groupdocs.cloud.watermark.model.WatermarkOptions;
import com.groupdocs.cloud.watermark.model.enums.HorizontalAlignment;
import com.groupdocs.cloud.watermark.model.enums.VerticalAlignment;

public class AddImageWatermarkExample {
    public static void main(String[] args) {
        // Initialize API client (replace with your actual credentials)
        ApiClient apiClient = new ApiClient("YOUR_CLIENT_ID", "YOUR_CLIENT_SECRET");
        WatermarkApi watermarkApi = new WatermarkApi(apiClient);

        // Input PDF file information
        FileInfo fileInfo = new FileInfo();
        fileInfo.setFilePath("input.pdf");

        // Image watermark configuration
        ImageWatermark imageWatermark = new ImageWatermark();
        imageWatermark.setImagePath("watermark.png");          // Path to watermark image
        imageWatermark.setOpacity(0.5);                        // 50% opacity
        imageWatermark.setScaleFactor(0.3);                    // 30% of page size
        imageWatermark.setRotationAngle(0);                    // No rotation
        imageWatermark.setHorizontalAlignment(HorizontalAlignment.CENTER);
        imageWatermark.setVerticalAlignment(VerticalAlignment.CENTER);
        imageWatermark.setMargin(new Margin(10, 10, 10, 10));  // 10 points margin on all sides

        // Watermark options
        WatermarkOptions options = new WatermarkOptions();
        options.setFileInfo(fileInfo);
        options.setImageWatermark(imageWatermark);
        options.setOutputPath("output.pdf"); // Resulting PDF with watermark

        // Create request and call API
        AddWatermarkRequest request = new AddWatermarkRequest(options);
        try {
            AddWatermarkResponse response = watermarkApi.addWatermark(request);
            System.out.println("Watermark added successfully. Output file: " + response.getPath());
        } catch (Exception e) {
            System.err.println("Error adding watermark: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
```
<!--[COMPLETE_CODE_SNIPPET_END]-->

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update the file paths (`input.pdf`, `watermark.png`, `output.pdf`) to match your actual file locations, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.groupdocs.cloud/watermark/) or reach out to the [support team](https://forum.groupdocs.cloud/c/watermark/29) for assistance.

## Apply Image Watermark to PDF Documents via cURL and REST API

Below are the REST calls you can use with cURL to achieve the same result without writing Java code.

1. **Obtain an access token**  
   <!--[CODE_SNIPPET_START]-->
   ```bash
   curl -X POST "https://api.groupdocs.cloud/v2.0/auth/token" \
        -H "Content-Type: application/json" \
        -d '{"client_id":"YOUR_CLIENT_ID","client_secret":"YOUR_CLIENT_SECRET"}'
   ```
   <!--[CODE_SNIPPET_END]-->  
   The response contains an `access_token` used in subsequent calls.

2. **Upload the source PDF**  
   <!--[CODE_SNIPPET_START]-->
   ```bash
   curl -X POST "https://api.groupdocs.cloud/v2.0/storage/upload?path=input.pdf" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -F "file=@/path/to/input.pdf"
   ```
   <!--[CODE_SNIPPET_END]-->

3. **Upload the watermark image**  
   <!--[CODE_SNIPPET_START]-->
   ```bash
   curl -X POST "https://api.groupdocs.cloud/v2.0/storage/upload?path=watermark.png" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -F "file=@/path/to/watermark.png"
   ```
   <!--[CODE_SNIPPET_END]-->

4. **Add the image watermark**  
   <!--[CODE_SNIPPET_START]-->
   ```bash
   curl -X POST "https://api.groupdocs.cloud/v2.0/watermark/add" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
              "fileInfo": { "filePath": "input.pdf" },
              "imageWatermark": {
                  "imagePath": "watermark.png",
                  "opacity": 0.5,
                  "scaleFactor": 0.3,
                  "horizontalAlignment": "Center",
                  "verticalAlignment": "Center",
                  "margin": { "top": 10, "right": 10, "bottom": 10, "left": 10 }
              },
              "outputPath": "output.pdf"
            }'
   ```
   <!--[CODE_SNIPPET_END]-->  
   This request mirrors the Java code logic, applying the same opacity, scaling and alignment settings.

5. **Download the watermarked PDF**  
   <!--[CODE_SNIPPET_START]-->
   ```bash
   curl -X GET "https://api.groupdocs.cloud/v2.0/storage/download?path=output.pdf" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -o output.pdf
   ```
   <!--[CODE_SNIPPET_END]-->  

For more details on request bodies and supported parameters, see the [official API documentation](https://reference.groupdocs.cloud/watermark/).

## Installing and Configuring GroupDocs.Watermark Cloud SDK for Java

Add the Maven dependency to your `pom.xml` (or the equivalent Gradle snippet). The library is hosted on Maven Central.

<!--[CODE_SNIPPET_START]-->
```xml
<dependency>
    <groupId>com.groupdocs</groupId>
    <artifactId>groupdocs-watermark-cloud</artifactId>
    <version>23.8</version>
</dependency>
```
<!--[CODE_SNIPPET_END]-->

You also need a valid GroupDocs Cloud account. Retrieve your **Client ID** and **Client Secret** from the [GroupDocs portal](https://products.groupdocs.cloud/watermark/java/). No additional runtime installation is required because the SDK communicates with the cloud service.

## Fine-Tuning Image Watermark Options for PDF Documents

The SDK exposes several properties that let you control the visual appearance of the watermark.

### Adjust Opacity

<!--[CODE_SNIPPET_START]-->
```java
imageWatermark.setOpacity(0.75); // 75% opacity for a more visible watermark
```
<!--[CODE_SNIPPET_END]-->  

Opacity values range from 0.0 (fully transparent) to 1.0 (fully opaque).

### Change Scale Factor

<!--[CODE_SNIPPET_START]-->
```java
imageWatermark.setScaleFactor(0.5); // Watermark occupies 50% of the page width
```
<!--[CODE_SNIPPET_END]-->  

The scale factor determines the watermark size relative to the page dimensions.

### Set Alignment and Margins

<!--[CODE_SNIPPET_START]-->
```java
imageWatermark.setHorizontalAlignment(HorizontalAlignment.RIGHT);
imageWatermark.setVerticalAlignment(VerticalAlignment.BOTTOM);
imageWatermark.setMargin(new Margin(20, 20, 20, 20));
```
<!--[CODE_SNIPPET_END]-->  

These settings place the watermark in the lower‑right corner with a 20‑point margin.

For a complete list of configurable properties, refer to the [API reference](https://reference.groupdocs.cloud/watermark/).

## Conclusion

Adding an image watermark to PDF documents in Java is a straightforward task when you use the [GroupDocs.Watermark Cloud SDK for Java](https://products.groupdocs.cloud/watermark/java/). The SDK handles all low‑level PDF manipulation, letting you focus on the visual aspects such as opacity, scaling and positioning. Whether you prefer a native Java implementation or a cloud‑based cURL workflow, the same high‑quality results are achievable without sacrificing performance. Remember to obtain a proper license for production use; pricing details are available on the product page and a [temporary license page](https://purchase.groupdocs.cloud/temporary-license/) can be used for evaluation.

## FAQs

- **How do I add image watermark to PDF in Java without losing quality?**  
  Use the `scaleFactor` property to size the watermark relative to the page and keep the original DPI of the source PDF. The SDK preserves the PDF's resolution, so the watermark appears crisp at any zoom level.

- **Can I add multiple watermarks to the same PDF?**  
  Yes. Create separate `ImageWatermark` objects with different configurations and add them sequentially by calling `addWatermark` multiple times or by adding them to a list in the request.

- **What are the supported image formats for the watermark?**  
  The API accepts common image types such as [PNG](https://docs.fileformat.com/image/png/), [JPG](https://docs.fileformat.com/image/jpg/), [BMP](https://docs.fileformat.com/image/bmp/), [GIF](https://docs.fileformat.com/image/gif/) and TIFF. PNG is recommended for lossless quality and transparency support.

- **Is there a way to preview the watermark before applying it?**  
  You can use the GroupDocs.Watermark Cloud SDK for Java to generate a temporary PDF with the watermark and download it for review. This uses the same `addWatermark` call with an output path pointing to a temporary location.

## Read More
- [Add Watermark to Images using Java](https://blog.groupdocs.cloud/watermark/add-watermark-to-images-using-java/)
- [Add Watermark to Word in Java - Watermark Creator](https://blog.groupdocs.cloud/watermark/add-watermark-to-word-in-java-watermark-creator/)
- [Add Image Watermark to PDF | How to Add Watermark to PDF Documents Using .NET](https://blog.groupdocs.cloud/watermark/insert-watermark-to-pdf-in-csharp/)