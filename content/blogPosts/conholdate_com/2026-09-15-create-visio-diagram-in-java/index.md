---
title: "Create Visio Diagram in Java"
seoTitle: "Create Visio Diagram in Java"
description: "Learn how to create Visio diagrams in Java with Conholdate.Total for Java. This guide shows setup, shape creation, hyperlinks, styling, and saving VSDX files."
date: Tue, 15 Sep 2026 05:09:24 +0000
lastmod: Tue, 15 Sep 2026 05:09:24 +0000
draft: false
url: /total/create-visio-diagram-in-java/
author: "Farhan Raza"
summary: "This tutorial walks Java developers through generating Visio diagrams using Conholdate.Total for Java. You will learn to set up the SDK, create rectangles, ellipses and connectors, apply colors, embed hyperlinks, and export result as a VSDX file for Microsoft Visio."
tags: ['java visio generation', 'visio diagram hyperlinks', 'java diagram performance']
categories: ["Conholdate.Total Product Family"]
showtoc: true
cover:
   image: images/create-visio-diagram-in-java.jpg
   alt: "Create Visio Diagram in Java"
   caption: "Create Visio Diagram in Java"
steps:
  - "Step 1: Add Maven dependency and import required classes"
  - "Step 2: Initialize diagram and configure page size"
  - "Step 3: Create shapes and attach hyperlinks"
  - "Step 4: Connect shapes with a connector line"
  - "Step 5: Save the diagram as VSDX"
faqs:
  - q: "How can I create Visio Diagram in Java with hyperlink support?"
    a: "Use [Conholdate.Total for Java](https://products.conholdate.com/total/java/) to instantiate a Diagram, add Shape objects, set Hyperlink properties, and save as VSDX. The SDK handles all Visio specifics."
  - q: "What file format does the SDK generate for Visio diagrams?"
    a: "The SDK saves the output as VSDX, the modern Visio file format, which can be opened directly in Microsoft Visio."
  - q: "Do I need a license to run the generated Visio files in production?"
    a: "Yes. Obtain a production license from the [pricing page](https://purchase.conholdate.com/pricing/total/family/) and you can also use a [temporary license](https://purchase.conholdate.com/temporary-license/) during development."
  - q: "Can I integrate this diagram generation into a web service?"
    a: "Absolutely. The SDK is a pure Java library, so you can call it from any Java‑based backend, such as a Spring Boot REST endpoint."
---

Creating a Visio diagram directly from Java code can streamline documentation workflows and eliminate manual drawing effort. [Conholdate.Total for Java](https://products.conholdate.com/total/java/) provides a robust SDK that enables you to generate Visio files programmatically. In this guide we will create Visio Diagram in Java, add shapes, style them, and embed hyperlinks. By the end you will have a ready‑to‑open [VSDX](https://docs.fileformat.com/visio/vsdx/) file that can be edited further in Microsoft Visio.

## The Visio Diagram Creation Requirements

Enterprises often need to produce technical schematics, flowcharts, or network diagrams automatically from data sources. Java developers building reporting dashboards, configuration tools, or CI pipelines frequently face the requirement to generate Visio files without manual intervention. The solution must support precise positioning, custom styling, and clickable hyperlinks that point to external documentation or web resources. Manual drawing in Visio is time‑consuming and error‑prone, especially when diagrams must be regenerated on each build.

## The Approach: Visio Diagram Generation With Conholdate.Total

[Conholdate.Total for Java](https://products.conholdate.com/total/java/) offers a dedicated diagram API that works with the VSDX format. It lets you create pages, add shapes, define fills, lines, and attach Hyperlink objects all through simple Java calls. The SDK also provides methods to set page dimensions in points, which aligns with Visio's native measurement system. Documentation for the diagram classes is available at the [official documentation](https://docs.conholdate.com/java/), and the full API reference can be explored at the [API reference](https://reference.conholdate.com/java/). Using this library you can automate the entire Visio creation pipeline on a server or desktop environment.

## Building the Solution: Create Visio Diagram in Java

The following steps walk you through the complete process, from Maven setup to saving the final VSDX file.

### Add Maven Dependency and Import Classes

First, configure the Conholdate Maven repository and add the SDK dependency to your `pom.xml`. Then import the required diagram classes.

```xml
<repositories>
  <repository>
    <id>conholdate-repo</id>
    <name>Conholdate Maven Repository</name>
    <url>https://repository.conholdate.com/repo/</url>
  </repository>
</repositories>

<dependency>
  <groupId>com.conholdate</groupId>
  <artifactId>conholdate-total</artifactId>
  <version>24.9</version>
  <type>pom</type>
</dependency>
```

```java
import com.groupdocs.diagram.Diagram;
import com.groupdocs.diagram.SaveFileFormat;
import com.groupdocs.diagram.diagramobjects.Shape;
import com.groupdocs.diagram.diagramobjects.ShapeType;
import com.groupdocs.diagram.diagramobjects.Hyperlink;
import com.groupdocs.diagram.diagramobjects.Fill;
import com.groupdocs.diagram.diagramobjects.Line;
import com.groupdocs.diagram.diagramobjects.Text;
```

### Initialize Diagram and Set Page Size

Create a new `Diagram` instance and define the page dimensions in points (1 inch = 72 points).

```java
Diagram diagram = new Diagram();
diagram.getPage().setWidth(8.5 * 72);   // 8.5 inches
diagram.getPage().setHeight(11 * 72);   // 11 inches
```

### Create Shapes and Add Hyperlinks

Add a rectangle and an ellipse, set their visual properties, and attach a hyperlink to the rectangle.

```java
// Rectangle
Shape rectangle = new Shape();
rectangle.setShapeType(ShapeType.RECTANGLE);
rectangle.setX(2 * 72);
rectangle.setY(2 * 72);
rectangle.setWidth(2 * 72);
rectangle.setHeight(1 * 72);
rectangle.getText().setValue("Hello Visio");
Hyperlink rectLink = rectangle.getHyperlink();
rectLink.setUrl("https://www.example.com");
rectLink.setDescription("Example site");
rectangle.getFill().setColor("#FFCC00");
rectangle.getLine().setColor("#000000");
rectangle.getLine().setWeight(0.5);
diagram.addShape(rectangle);

// Ellipse
Shape ellipse = new Shape();
ellipse.setShapeType(ShapeType.ELLIPSE);
ellipse.setX(5 * 72);
ellipse.setY(2 * 72);
ellipse.setWidth(2 * 72);
ellipse.setHeight(1 * 72);
ellipse.getText().setValue("Ellipse");
ellipse.getFill().setColor("#00CCFF");
ellipse.getLine().setColor("#000000");
ellipse.getLine().setWeight(0.5);
diagram.addShape(ellipse);
```

### Connect Shapes with a Connector

Create a line shape that links the center of the rectangle to the center of the ellipse.

```java
Shape connector = new Shape();
connector.setShapeType(ShapeType.LINE);
connector.setBeginX(rectangle.getX() + rectangle.getWidth() / 2);
connector.setBeginY(rectangle.getY() + rectangle.getHeight() / 2);
connector.setEndX(ellipse.getX() + ellipse.getWidth() / 2);
connector.setEndY(ellipse.getY() + ellipse.getHeight() / 2);
connector.getLine().setColor("#FF0000");
connector.getLine().setWeight(1.0);
diagram.addShape(connector);
```

### Save Diagram to VSDX

Finally, write the diagram to a VSDX file that can be opened in Microsoft Visio.

```java
diagram.save("output.vsdx", SaveFileFormat.VSDX);
```

## Create Visio Diagram in Java - Full Working Sample - Complete Code Example

The following code demonstrates the entire workflow from start to finish.

```java
import com.groupdocs.diagram.Diagram;
import com.groupdocs.diagram.SaveFileFormat;
import com.groupdocs.diagram.diagramobjects.Shape;
import com.groupdocs.diagram.diagramobjects.ShapeType;
import com.groupdocs.diagram.diagramobjects.Hyperlink;
import com.groupdocs.diagram.diagramobjects.Fill;
import com.groupdocs.diagram.diagramobjects.Line;
import com.groupdocs.diagram.diagramobjects.Text;

public class CreateVisioDiagram {
    public static void main(String[] args) {
        Diagram diagram = null;
        try {
            // Initialize a new Visio diagram
            diagram = new Diagram();

            // Configure page size (in inches, 1 inch = 72 points)
            diagram.getPage().setWidth(8.5 * 72);
            diagram.getPage().setHeight(11 * 72);

            // -------------------- Rectangle Shape --------------------
            Shape rectangle = new Shape();
            rectangle.setShapeType(ShapeType.RECTANGLE);
            rectangle.setX(2 * 72);          // X position in points
            rectangle.setY(2 * 72);          // Y position in points
            rectangle.setWidth(2 * 72);      // Width in points
            rectangle.setHeight(1 * 72);     // Height in points

            // Text inside rectangle
            Text rectText = rectangle.getText();
            rectText.setValue("Hello Visio");

            // Hyperlink for rectangle
            Hyperlink rectLink = rectangle.getHyperlink();
            rectLink.setUrl("https://www.example.com");
            rectLink.setDescription("Example site");

            // Styling rectangle
            Fill rectFill = rectangle.getFill();
            rectFill.setColor("#FFCC00");    // Fill color
            Line rectLine = rectangle.getLine();
            rectLine.setColor("#000000");    // Border color
            rectLine.setWeight(0.5);         // Border thickness

            // Add rectangle to diagram
            diagram.addShape(rectangle);

            // -------------------- Ellipse Shape --------------------
            Shape ellipse = new Shape();
            ellipse.setShapeType(ShapeType.ELLIPSE);
            ellipse.setX(5 * 72);
            ellipse.setY(2 * 72);
            ellipse.setWidth(2 * 72);
            ellipse.setHeight(1 * 72);

            // Text inside ellipse
            ellipse.getText().setValue("Ellipse");

            // Styling ellipse
            ellipse.getFill().setColor("#00CCFF");
            ellipse.getLine().setColor("#000000");
            ellipse.getLine().setWeight(0.5);

            // Add ellipse to diagram
            diagram.addShape(ellipse);

            // -------------------- Connector (Line) --------------------
            Shape connector = new Shape();
            connector.setShapeType(ShapeType.LINE);
            // Start point: center of rectangle
            connector.setBeginX(rectangle.getX() + rectangle.getWidth() / 2);
            connector.setBeginY(rectangle.getY() + rectangle.getHeight() / 2);
            // End point: center of ellipse
            connector.setEndX(ellipse.getX() + ellipse.getWidth() / 2);
            connector.setEndY(ellipse.getY() + ellipse.getHeight() / 2);
            // Styling connector
            connector.getLine().setColor("#FF0000");
            connector.getLine().setWeight(1.0);

            // Add connector to diagram
            diagram.addShape(connector);

            // -------------------- Save Diagram --------------------
            diagram.save("output.vsdx", SaveFileFormat.VSDX);
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            // Ensure resources are released
            if (diagram != null) {
                try {
                    diagram.close();
                } catch (Exception ex) {
                    ex.printStackTrace();
                }
            }
        }
    }
}
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.conholdate.com/java/) or reach out to the [support team](https://forum.conholdate.com/c/total/5) for assistance.

## Deployment Considerations for Visio Diagram Projects

The SDK runs on any Java 8+ runtime, making it suitable for backend services, batch jobs, or desktop utilities. When generating large diagrams, monitor heap usage and consider reusing a single `Diagram` instance for multiple pages to reduce memory overhead. A valid license is required for production; you can obtain a temporary license for testing from the [temporary license page](https://purchase.conholdate.com/temporary-license/) and purchase a full license via the [pricing page](https://purchase.conholdate.com/pricing/total/family/). Ensure the output directory is writable by the process that executes the code.

## Conclusion

Programmatically creating Visio diagrams in Java becomes straightforward with [Conholdate.Total for Java](https://products.conholdate.com/total/java/). By following the steps above you can generate VSDX files, apply custom styling, and embed hyperlinks that enhance interactivity. Remember to acquire a proper production license and test the generated diagrams in Microsoft Visio to verify layout fidelity. With the SDK in place, you can automate diagram creation across a wide range of enterprise scenarios.

## FAQs

- **How can I create Visio Diagram in Java with hyperlink support?**  
  Use the diagram classes provided by [Conholdate.Total for Java](https://products.conholdate.com/total/java/), set `Hyperlink` properties on shapes, and save the file as VSDX.

- **What file format does the SDK generate for Visio diagrams?**  
  The SDK outputs the modern VSDX format, which is fully compatible with Microsoft Visio.

- **Do I need a license to run the generated Visio files in production?**  
  Yes. Obtain a production license from the [pricing page](https://purchase.conholdate.com/pricing/total/family/) and you may use a [temporary license](https://purchase.conholdate.com/temporary-license/) during development.

- **Can I integrate this diagram generation into a web service?**  
  Absolutely. The SDK is a pure Java library, so you can call it from any Java‑based backend such as Spring Boot or Jakarta EE.

## Read More
- [Create Charts in Word Documents using Java](https://blog.conholdate.com/total/create-charts-in-word-documents-using-java/)
- [Add Watermark to PDF in Java](https://blog.conholdate.com/total/add-watermark-to-pdf-in-java/)
- [Convert Onenote to Image in Java](https://blog.conholdate.com/total/convert-onenote-to-image-in-java/)