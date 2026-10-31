---
title: Preserve Literal Special Symbols in PDF with Aspose.PDF
seoTitle: Preserve Literal Special Symbols in PDF with Aspose.PDF
description: Learn how to preserve literal special symbols like $p and $P in PDFs
  generated with Aspose.PDF for .NET by turning off the ProcessSpecialSymbols option
  now.
date: Thu, 29 Oct 2026 04:05:48 +0000
draft: true
url: /pdf/preserve-literal-special-symbols-pdf/
author: Muzammil Khan
summary: This tutorial shows how to keep placeholders such as $p and $P from being
  interpreted as page‑number tokens when creating PDFs with Aspose.PDF for .NET. You
  will see the required property, a complete code example, and best‑practice tips
  for real‑world projects.
tags: ['csharp', 'aspose pdf', 'pdf generation', 'special symbols', 'processspecialsymbols', 'aspdotnet', 'pdf conversion']
categories: ["Aspose.PDF Product Family"]
showtoc: true
cover:
  image: images/preserve-literal-special-symbols-pdf.jpg
  alt: Preserve Literal Special Symbols in PDF with Aspose.PDF
  caption: Preserve Literal Special Symbols in PDF with Aspose.PDF
  hidden: false
steps:
- Install Aspose.PDF for .NET using the NuGet command.
- Create a new Document and add a Page.
- Set Page.ProcessSpecialSymbols to false to stop placeholder processing.
- Add TextFragment objects that contain $p and $P literals.
- Save the Document to a PDF file.
faqs:
- q: What does the Page.ProcessSpecialSymbols property control?
  a: When true (the default), the engine replaces $p and $P with the current page
    number; setting it to false leaves the symbols unchanged in the output.
- q: Will disabling ProcessSpecialSymbols affect other placeholders?
  a: Only $p (lower‑case) and $P (upper‑case) are affected; all other text is rendered
    exactly as supplied.
- q: Can I enable ProcessSpecialSymbols for some pages and disable it for others?
  a: Yes. ProcessSpecialSymbols is a per‑page property, so you can set it to true
    on pages that need automatic page numbering and false on pages that require literal
    symbols.
- q: Is the property available in languages other than C#?
  a: The same property exists in all language bindings of Aspose.PDF, including Java,
    Python, and PHP; the usage pattern is identical.
- q: Do I need to call any additional methods after changing ProcessSpecialSymbols?
  a: No additional calls are required; the setting takes effect immediately for any
    text added after the change.
- q: Will disabling ProcessSpecialSymbols impact PDF rendering performance?
  a: The impact is negligible; the property only toggles a simple string‑replacement
    check during text rendering.
---

When generating PDF documents programmatically, Aspose.PDF treats the tokens `$p` and `$P` as placeholders for the current page number. In many scenarios—such as legal notices, code samples, or templates—you need those symbols to appear exactly as typed. The `Page.ProcessSpecialSymbols` property gives you fine‑grained control over this behavior. This guide shows how to turn the feature off so that `$p` and `$P` are preserved as literal text.

## Key Takeaways
- `Page.ProcessSpecialSymbols` defaults to **true**, which replaces `$p`/`$P` with page numbers.
- Setting the property to **false** disables the replacement, keeping the symbols literal.
- The property is applied per page, allowing mixed behavior in a single document.
- The API works the same across all Aspose.PDF language bindings.
- Disabling the feature has no measurable performance penalty.

## Why This Feature Matters
Developers often embed placeholders in template text to be replaced later—page numbers, dates, or user‑provided values. When the placeholder syntax collides with Aspose.PDF's built‑in `$p`/`$P` tokens, the generated PDF can contain unexpected numbers instead of the intended symbols. This is especially problematic for documents that display code snippets, licensing terms, or any content where a literal dollar‑sign followed by a letter must stay untouched. By controlling `ProcessSpecialSymbols`, you ensure that your PDF output matches the exact visual layout required by your business logic.

## Getting Started with Aspose.PDF
First, add the Aspose.PDF library to your .NET project. The easiest way is via NuGet:

```powershell
Install-Package Aspose.PDF
```

After the package is installed, you can start using the API. Detailed documentation is available on the [Aspose.PDF product page](https://products.aspose.com/pdf/net/), the [official docs site](https://docs.aspose.com/pdf/net/), and the [API reference](https://reference.aspose.com/pdf/net/).

## How to Preserve Literal Special Symbols When Generating PDFs
Below is a step‑by‑step walkthrough that creates a PDF, disables special‑symbol processing for a page, adds two text fragments containing `$p` and `$P`, and saves the file.

1. **Create a new `Document` instance** – this represents the PDF you are building.
2. **Add a `Page` to the document** – each page can be configured independently.
3. **Set `Page.ProcessSpecialSymbols` to `false`** – this tells the engine not to replace `$p`/`$P`.
4. **Insert `TextFragment` objects** – these hold the literal strings you want to appear.
5. **Save the document to disk** – the output file will contain the exact symbols you added.

The following example shows how to preserve literal `$p` and `$P` placeholders using C# and Aspose.PDF.

```csharp
private static void PreserveLiteralSpecialSymbols()
{
    // The path to the documents directory
    var dataDir = RunExamples.GetDataDir_AsposePdf();

    // Create PDF document
    using (var document = new Aspose.Pdf.Document())
    {
        // Add a page and preserve literal $p and $P text
        var page = document.Pages.Add();
        page.ProcessSpecialSymbols = false;
        page.Paragraphs.Add(new Aspose.Pdf.Text.TextFragment("Lowercase: $p"));
        page.Paragraphs.Add(new Aspose.Pdf.Text.TextFragment("Uppercase: $P"));

        // Save PDF document
        document.Save(dataDir + "literal-special-symbols.pdf");
    }
}
```

**Explanation of the code**

- `RunExamples.GetDataDir_AsposePdf()` resolves a folder path where the generated PDF will be written. Replace it with any writable directory in your own project.
- `new Aspose.Pdf.Document()` creates an empty PDF container.
- `document.Pages.Add()` appends a fresh page to the document’s page collection.
- `page.ProcessSpecialSymbols = false;` disables the automatic replacement of `$p` and `$P` for this particular page.
- `new Aspose.Pdf.Text.TextFragment("Lowercase: $p")` builds a text object that contains the literal `$p`. Because the processing flag is off, the fragment is rendered exactly as typed.
- `document.Save(...)` writes the constructed PDF to the file system. The resulting `literal-special-symbols.pdf` will show the strings **Lowercase: $p** and **Uppercase: $P**.

### Extending the Example
You may need to preserve symbols on only a subset of pages while allowing auto‑numbering on others. Because `ProcessSpecialSymbols` is a property of `Page`, you can enable it selectively:

```csharp
// Page 1 – keep literals
var page1 = document.Pages.Add();
page1.ProcessSpecialSymbols = false;
page1.Paragraphs.Add(new Aspose.Pdf.Text.TextFragment("Literal: $p"));

// Page 2 – automatic page number
var page2 = document.Pages.Add();
page2.ProcessSpecialSymbols = true; // default, but shown explicitly
page2.Paragraphs.Add(new Aspose.Pdf.Text.TextFragment("Auto‑number: $p"));
```

When you open the resulting PDF, Page 1 will display `$p` unchanged, while Page 2 will show the actual page number (e.g., "Auto‑number: 2"). This mixed approach is useful for multi‑section reports where a header needs a literal placeholder but the body uses automatic numbering.

### Common Pitfalls and How to Avoid Them
- **Forgetting to set the property before adding text** – The flag affects only text added after the assignment. If you add a `TextFragment` first and then set `ProcessSpecialSymbols = false`, the earlier fragment will already have been processed.
- **Assuming the property works for other placeholder formats** – It is limited to `$p` (lowercase) and `$P` (uppercase). Symbols such as `${date}` or `@@PAGE@@` are not touched by this setting.
- **Confusing per‑page and document‑wide settings** – There is no global switch; you must set the property on each page that requires special handling.
- **Running on a read‑only stream** – The `Save` method needs write access to the target folder. Ensure the application has appropriate permissions.

### Performance Considerations
The engine checks the flag during text rendering, which is a lightweight Boolean check. In large‑scale batch processing (hundreds of thousands of pages), the overhead is negligible compared with other PDF generation costs such as image embedding or complex graphics.

## Conclusion
Preserving literal `$p` and `$P` symbols in PDFs generated with Aspose.PDF is straightforward: set `Page.ProcessSpecialSymbols` to `false` on the pages where you need the symbols unchanged. This per‑page control lets you combine literal placeholders with automatic page numbering in the same document, giving you the flexibility required for templates, legal documents, and code samples. The example above demonstrates the complete workflow and highlights best practices for avoiding common mistakes.

## FAQs
1. **What does the Page.ProcessSpecialSymbols property control?**
   When true (the default), the engine replaces `$p` and `$P` with the current page number; setting it to false leaves the symbols unchanged in the output.

2. **Will disabling ProcessSpecialSymbols affect other placeholders?**
   Only `$p` (lower‑case) and `$P` (upper‑case) are affected; all other text is rendered exactly as supplied.

3. **Can I enable ProcessSpecialSymbols for some pages and disable it for others?**
   Yes. ProcessSpecialSymbols is a per‑page property, so you can set it to true on pages that need automatic page numbering and false on pages that require literal symbols.

4. **Is the property available in languages other than C#?**
   The same property exists in all language bindings of Aspose.PDF, including Java, Python, and PHP; the usage pattern is identical.

5. **Do I need to call any additional methods after changing ProcessSpecialSymbols?**
   No additional calls are required; the setting takes effect immediately for any text added after the change.

6. **Will disabling ProcessSpecialSymbols impact PDF rendering performance?**
   The impact is negligible; the property only toggles a simple string‑replacement check during text rendering.

## Get a Free License and Explore More
Start experimenting with Aspose.PDF for .NET today by requesting a temporary free license. A free license removes evaluation limitations and lets you integrate the library into your development workflow without cost.

- [Free License Request](${platform.license_url})
- [Documentation](${platform.docs_url})
- [API Reference](${platform.api_reference_url})
- [Free Online PDF Apps](${platform.free_apps_url})
