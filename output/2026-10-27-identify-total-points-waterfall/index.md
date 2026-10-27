---
title: Identify Total Points in Waterfall Chart with Aspose.Words
seoTitle: Identify Total Points in Waterfall Chart with Aspose.Words
description: Learn how to detect total points in a Waterfall chart using Aspose.Words
  for .NET. The guide explains the IsTotal method on ChartSeries and the IsTotal property
  on ChartDataPoint with a complete C# example.
date: Tue, 27 Oct 2026 04:04:29 +0000
draft: true
url: /words/identify-total-points-waterfall/
author: Muzammil Khan
summary: This tutorial shows how to use Aspose.Words for .NET to recognize total (subtotal)
  data points in a Waterfall chart. You’ll see how to create a chart, add a series,
  and apply the new IsTotal method and property with a ready‑to‑run C# code sample.
tags: ['csharp', 'asposewords', 'waterfall chart', 'chartseries istotal', 'chart datapoint istotal', 'documentbuilder insertchart']
categories: ["Aspose.Words Product Family"]
showtoc: true
cover:
  image: images/identify-total-points-waterfall.jpg
  alt: Identify Total Points in Waterfall Chart with Aspose.Words
  caption: Identify Total Points in Waterfall Chart with Aspose.Words
  hidden: false
steps:
- Install Aspose.Words for .NET via NuGet.
- Create a Document and DocumentBuilder instance.
- Insert a Waterfall chart and add a series with data.
- Use ChartSeries.IsTotal (or ChartDataPoint.IsTotal) to identify total points.
- Save the document to a .docx file.
faqs:
- q: How does Aspose.Words determine a total point in a Waterfall chart?
  a: The ChartSeries.IsTotal(int index) method returns true for data points marked
    as totals, and the same information is exposed through the ChartDataPoint.IsTotal
    property.
- q: Can I set a point as a total when building the series?
  a: Yes. When adding a series you can pass a Boolean array indicating which data
    points are totals; the API then stores that flag for later retrieval.
- q: Is the IsTotal flag available for other chart types?
  a: The flag is specific to Waterfall charts, where totals and subtotals have special
    visual meaning.
- q: Do I need to enable any additional features to use IsTotal?
  a: No extra configuration is required; the feature is part of the standard Aspose.Words
    for .NET library.
- q: What namespace contains ChartSeries and ChartDataPoint?
  a: Both classes reside in the Aspose.Words.Drawing.Charts namespace.
- q: Can I retrieve the total flag after loading an existing document?
  a: Yes. After loading the document, you can access the chart’s series and query
    each data point with the IsTotal property.
---

In this post we’ll show how to **identify total (subtotal) points** in a Waterfall chart using Aspose.Words for .NET. Recognizing totals is essential for custom reporting, analytics, or when you need to apply special formatting to those columns.

## Key Takeaways
- Aspose.Words provides `ChartSeries.IsTotal(int)` and `ChartDataPoint.IsTotal` to flag total points in Waterfall charts.
- The API works directly with the chart’s series collection, no extra configuration needed.
- A short C# example demonstrates creating a chart, marking totals, and printing each point’s type.

## Why Identify Total Points in Waterfall Charts?
Total points represent subtotals or final sums in a Waterfall chart. Detecting them programmatically lets you highlight, style, or process those columns differently—crucial for precise financial or KPI reporting.

## Getting Started with Aspose.Words for .NET
First, add the Aspose.Words package to your project:

```powershell
Install-Package Aspose.Words
```

For more details about the product, visit the [Aspose.Words for .NET product page](https://products.aspose.com/words/net/).

## How to Detect Total Points in a Waterfall Chart
The following example creates a Waterfall chart, marks specific data points as totals, and prints whether each point is an increase, decrease, or total.

The example demonstrates:
1. Creating a `Document` and `DocumentBuilder`.
2. Inserting a Waterfall chart.
3. Clearing the default series and adding a custom series with a Boolean array that flags totals.
4. Using `ChartSeries.IsTotal` and `ChartDataPoint.IsTotal` to identify totals.
5. Saving the document.

```csharp
// For complete examples and data files, please go to https://github.com/aspose-words/Aspose.Words-for-.NET.git.
Document doc = new Document();
DocumentBuilder builder = new DocumentBuilder(doc);

// Insert a Waterfall chart.
Shape shape = builder.InsertChart(ChartType.Waterfall, 450, 450);
Chart chart = shape.Chart;
chart.Title.Text = "New Zealand GDP";

// Delete default generated series.
chart.Series.Clear();

// Add a series where the start value, the subtotal and the final value are totals.
ChartSeries series = chart.Series.Add(
    "New Zealand GDP",
    new string[] { "2018", "2019 growth", "2020 growth", "2020", "2021 growth", "2022 growth", "2022" },
    new double[] { 100, 0.57, -0.25, 100.32, 20.22, -2.92, 117.62 },
    new bool[] { true, false, false, true, false, false, true });

// Print the type of each data point.
for (int i = 0; i < series.YValues.Count; i++)
{
    if (series.IsTotal(i))
        Console.WriteLine($"Data point {i} is Subtotal");
    else if (series.YValues[i].DoubleValue > 0)
        Console.WriteLine($"Data point {i} is Increase");
    else
        Console.WriteLine($"Data point {i} is Decrease");
}

// The same flag is available on the data point itself.
Console.WriteLine($"Data point 3 is total: {series.DataPoints[3].IsTotal}");

doc.Save("Charts.ChartSeriesAndDataPointIsTotal.docx");
```

**Explanation**
- `Document` and `DocumentBuilder` create an empty Word document.
- `InsertChart` adds a Waterfall chart of the specified size.
- `chart.Series.Clear()` removes the placeholder series generated by the API.
- `chart.Series.Add` constructs a new series. The last Boolean array marks which X‑axis entries are totals (`true` for start, subtotal, and final values).
- `series.IsTotal(i)` checks the total flag for a given index. The loop prints a readable description for each point.
- `series.DataPoints[3].IsTotal` shows that the same information is accessible directly on the `ChartDataPoint` object.
- Finally, `doc.Save` writes the document to disk.

## Conclusion
Using Aspose.Words for .NET you can programmatically flag and detect total points in Waterfall charts via the `IsTotal` method on `ChartSeries` and the `IsTotal` property on `ChartDataPoint`. This enables custom logic such as special styling, analytics, or conditional processing of subtotal columns.

## FAQs
1. **How does Aspose.Words determine a total point in a Waterfall chart?**
   The `ChartSeries.IsTotal(int index)` method returns true for data points marked as totals, and the same flag is exposed through the `ChartDataPoint.IsTotal` property.

2. **Can I set a point as a total when building the series?**
   Yes. When calling `chart.Series.Add` you can supply a Boolean array that indicates which data points are totals; the API stores that flag for later retrieval.

3. **Is the IsTotal flag available for other chart types?**
   The flag is specific to Waterfall charts, where totals and subtotals have special visual meaning.

4. **Do I need to enable any additional features to use IsTotal?**
   No extra configuration is required; the feature is part of the standard Aspose.Words for .NET library.

5. **What namespace contains ChartSeries and ChartDataPoint?**
   Both classes reside in the `Aspose.Words.Drawing.Charts` namespace.

6. **Can I retrieve the total flag after loading an existing document?**
   Yes. After loading the document, you can access the chart’s series and query each data point with the `IsTotal` property.

## Get a Free License and Explore More
Start experimenting with Aspose.Words today by requesting a temporary free license:

[Get a Free Temporary License](https://purchase.aspose.com/temporary-license/)

Additional resources:
- [Documentation](https://docs.aspose.com/words/net/)
- [API Reference](https://reference.aspose.com/words/net/)
- [Free Apps](https://products.aspose.app/words/family)

