---
title: "Step‑by‑Step Guide to Integrate GroupDocs.Rewriter with ASP.NET Core MVC"
seoTitle: "Step‑by‑Step Guide to Integrate GroupDocs.Rewriter with ASP.NET Core MVC"
description: "Step‑by‑step guide to add GroupDocs.Rewriter Cloud SDK for .NET to an ASP.NET Core MVC app, covering installation, DI setup, controller logic, and rendering."
date: Wed, 11 Nov 2026 19:21:49 +0000
lastmod: Wed, 11 Nov 2026 19:21:49 +0000
draft: false
url: /rewriter/stepbystep-guide-to-integrate-groupdocsrewriter-with-aspdotnet-core-mvc/
author: "Muhammad Mustafa"
summary: "This tutorial walks .NET developers through integrating GroupDocs.Rewriter Cloud SDK for .NET into an ASP.NET Core MVC application. You'll see how to install the package, configure credentials, register the API client with dependency injection, build a controller that rewrites text, and display results in a Razor view, all with complete code and cURL examples."
tags: ['aspnet core mvc', 'document rewriting', 'sdk integration']
categories: ["GroupDocs.Rewriter Cloud Product Family"]
showtoc: true
cover:
   image: images/stepbystep-guide-to-integrate-groupdocsrewriter-with-aspdotnet-core-mvc.jpg
   alt: "Step‑by‑Step Guide to Integrate GroupDocs.Rewriter with ASP.NET Core MVC"
   caption: "Step‑by‑Step Guide to Integrate GroupDocs.Rewriter with ASP.NET Core MVC"
steps:
  - "Step 1: Install the GroupDocs.Rewriter Cloud SDK for .NET package."
  - "Step 2: Add your GroupDocs Rewriter credentials to the configuration."
  - "Step 3: Register the Rewriter API client in the ASP.NET Core DI container."
  - "Step 4: Implement the MVC controller and view model for text rewriting."
  - "Step 5: Create the Razor view to accept input and display rewritten text."
faqs:
  - q: "What is the best way to store GroupDocs Rewriter credentials in an ASP.NET Core MVC project?"
    a: "Store the AppSid and AppKey in the appsettings.json file and bind them to a POCO class. The [GroupDocs.Rewriter Cloud SDK for .NET](https://products.groupdocs.cloud/rewriter/net/) reads the values via IOptions<T> at runtime."
  - q: "Can I use the same integration approach for other GroupDocs Cloud products?"
    a: "Yes. The pattern of adding credentials, registering the API client in DI, and calling the service from a controller works for all GroupDocs Cloud SDKs, such as [GroupDocs.Viewer Cloud SDK for .NET](https://products.groupdocs.cloud/viewer/net/)."
  - q: "How do I handle large texts or multiple rewrite requests efficiently?"
    a: "Process each request asynchronously as shown in the controller example. The SDK is designed for high‑throughput scenarios, and you can batch calls if needed."
  - q: "Is there a temporary license available for testing?"
    a: "A temporary license can be obtained from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/). It allows you to evaluate the SDK before purchasing a full license."
---

Converting raw text into polished, SEO‑friendly content is a daily challenge for many .NET developers building content‑rich web applications. [GroupDocs.Rewriter Cloud SDK for .NET](https://products.groupdocs.cloud/rewriter/net/) provides a powerful API that rewrites sentences while preserving meaning. This step-by-Step guide to Integrate with ASP.NET Core MVC shows you how to set up the library, configure credentials, implement the rewriting logic in a controller, and render the results in a Razor view.

## The Use Case Requirements

Enterprises that generate user‑generated articles, product descriptions, or marketing copy often need to improve readability without manual editing. The requirements for such a scenario include:

* Real‑time text rewriting directly from a web form.  
* Secure handling of API credentials on the server side.  
* Seamless integration with the existing ASP.NET Core MVC pipeline.

Using generic string‑manipulation code quickly becomes error‑prone and does not scale, which is why a dedicated document rewriting library is essential.

## Choosing GroupDocs.Rewriter Cloud SDK for .NET for the Job

GroupDocs.Rewriter Cloud SDK for .NET offers a REST‑based API that supports multiple languages, customizable rewrite modes, and high‑performance processing. Its key capabilities that match the use case are:

* **RewriteModeEnum.Rewrite** - produces a natural‑language rewrite of the input text.  
* **DI‑friendly client** - can be registered as a singleton in the ASP.NET Core service container.  
* **Strong typing and async support** - fits naturally into modern .NET asynchronous patterns.

The step-by-Step guide to Integrate with ASP.NET Core MVC demonstrates how these capabilities map to the requirements. For detailed API information, see the [official documentation](https://docs.groupdocs.cloud/rewriter/) and the [API reference](https://reference.groupdocs.cloud/rewriter/).

## Implementing Step‑by‑Step Guide to Integrate with ASP.NET Core MVC

This step-by-Step guide to Integrate with ASP.NET Core MVC will walk you through each required configuration step.

### Install the SDK Package

Add the NuGet package to your project.

```bash
dotnet add package GroupDocs.Rewriter-Cloud
```

You can also download the binaries from the [download page](https://releases.groupdocs.cloud/rewriter/net/).

### Add Configuration for Rewriter Credentials

Place your AppSid and AppKey in the configuration. The snippet below adds them in‑memory for simplicity.

```csharp
builder.Configuration.AddInMemoryCollection(new[]
{
    new KeyValuePair<string,string>("GroupDocsRewriter:AppSid", "YOUR_APP_SID"),
    new KeyValuePair<string,string>("GroupDocsRewriter:AppKey", "YOUR_APP_KEY")
});
```

### Register the Rewriter API Client in DI

The SDK client is registered as a singleton so it can be injected into controllers.

```csharp
builder.Services.Configure<RewriterSettings>(builder.Configuration.GetSection("GroupDocsRewriter"));

builder.Services.AddSingleton<IRewriterApi>(sp =>
{
    var settings = sp.GetRequiredService<IOptions<RewriterSettings>>().Value;
    var config = new Configuration
    {
        AppSid = settings.AppSid,
        AppKey = settings.AppKey
    };
    return new RewriterApi(config);
});
```

### Create the MVC Controller and View Model

The controller receives the original text, calls the Rewriter API, and returns the rewritten result.

```csharp
public class RewriterController : Controller
{
    private readonly IRewriterApi _rewriterApi;

    public RewriterController(IRewriterApi rewriterApi)
    {
        _rewriterApi = rewriterApi;
    }

    [HttpGet]
    public IActionResult Index()
    {
        return View(new RewriterViewModel());
    }

    [HttpPost]
    public async Task<IActionResult> Index(RewriterViewModel model)
    {
        if (!ModelState.IsValid)
        {
            return View(model);
        }

        var rewriteRequest = new RewriteRequest
        {
            Text = model.InputText,
            Language = "en",
            TargetLanguage = "en",
            RewriteMode = RewriteModeEnum.Rewrite
        };

        RewriteResponse response = await _rewriterApi.RewriteAsync(rewriteRequest);
        model.OutputText = response?.Result?.Text ?? string.Empty;

        return View(model);
    }
}
```

The accompanying view model holds the input and output strings.

```csharp
public class RewriterViewModel
{
    [Required]
    [Display(Name = "Original Text")]
    public string InputText { get; set; } = string.Empty;

    [Display(Name = "Rewritten Text")]
    public string OutputText { get; set; } = string.Empty;
}
```

### Build the Razor View for Text Input and Output

The Razor page presents a simple form and displays the rewritten text when available.

```csharp
@model RewriterViewModel
@{
    ViewData["Title"] = "Text Rewriter";
}
<h2>@ViewData["Title"]</h2>

<form asp-action="Index" method="post" class="form-horizontal">
    <div class="form-group">
        <label asp-for="InputText" class="control-label"></label>
        <textarea asp-for="InputText" class="form-control" rows="6"></textarea>
        <span asp-validation-for="InputText" class="text-danger"></span>
    </div>
    <div class="form-group">
        <button type="submit" class="btn btn-primary">Rewrite</button>
    </div>
</form>

@if (!string.IsNullOrWhiteSpace(Model.OutputText))
{
    <hr />
    <h4>Rewritten Text</h4>
    <textarea class="form-control" rows="6" readonly>@Model.OutputText</textarea>
}

@section Scripts {
    @{await Html.RenderPartialAsync("_ValidationScriptsPartial");}
}
```

## Full Working Example for Document Rewriting in ASP.NET Core MVC

The example below contains the complete source files needed to run the solution.

```csharp
// ---------------------------------------------------
// Program.cs
// ---------------------------------------------------
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Options;
using GroupDocs.Rewriter.Cloud.Sdk.Api;
using GroupDocs.Rewriter.Cloud.Sdk.Client;
using GroupDocs.Rewriter.Cloud.Sdk.Model.Requests;
using GroupDocs.Rewriter.Cloud.Sdk.Model;
using System.Threading.Tasks;

var builder = WebApplication.CreateBuilder(args);

// Add configuration for GroupDocs Rewriter credentials
builder.Configuration.AddInMemoryCollection(new[]
{
    new KeyValuePair<string,string>("GroupDocsRewriter:AppSid", "YOUR_APP_SID"),
    new KeyValuePair<string,string>("GroupDocsRewriter:AppKey", "YOUR_APP_KEY")
});

builder.Services.Configure<RewriterSettings>(builder.Configuration.GetSection("GroupDocsRewriter"));

// Register GroupDocs Rewriter API client in DI
builder.Services.AddSingleton<IRewriterApi>(sp =>
{
    var settings = sp.GetRequiredService<IOptions<RewriterSettings>>().Value;
    var config = new Configuration
    {
        AppSid = settings.AppSid,
        AppKey = settings.AppKey
    };
    return new RewriterApi(config);
});

builder.Services.AddControllersWithViews();

var app = builder.Build();

if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Home/Error");
}
app.UseStaticFiles();
app.UseRouting();
app.UseAuthorization();

app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Rewriter}/{action=Index}/{id?}");

app.Run();

// ---------------------------------------------------
// RewriterSettings.cs
// ---------------------------------------------------
public class RewriterSettings
{
    public string AppSid { get; set; } = string.Empty;
    public string AppKey { get; set; } = string.Empty;
}

// ---------------------------------------------------
// Models/RewriterViewModel.cs
// ---------------------------------------------------
using System.ComponentModel.DataAnnotations;

public class RewriterViewModel
{
    [Required]
    [Display(Name = "Original Text")]
    public string InputText { get; set; } = string.Empty;

    [Display(Name = "Rewritten Text")]
    public string OutputText { get; set; } = string.Empty;
}

// ---------------------------------------------------
// Controllers/RewriterController.cs
// ---------------------------------------------------
using Microsoft.AspNetCore.Mvc;
using System.Threading.Tasks;

public class RewriterController : Controller
{
    private readonly IRewriterApi _rewriterApi;

    public RewriterController(IRewriterApi rewriterApi)
    {
        _rewriterApi = rewriterApi;
    }

    [HttpGet]
    public IActionResult Index()
    {
        return View(new RewriterViewModel());
    }

    [HttpPost]
    public async Task<IActionResult> Index(RewriterViewModel model)
    {
        if (!ModelState.IsValid)
        {
            return View(model);
        }

        // Build request for the Rewriter API
        var rewriteRequest = new RewriteRequest
        {
            Text = model.InputText,
            Language = "en",               // source language
            TargetLanguage = "en",         // target language (same for rewriting)
            RewriteMode = RewriteModeEnum.Rewrite // choose rewrite mode
        };

        // Call the API
        RewriteResponse response = await _rewriterApi.RewriteAsync(rewriteRequest);

        // Populate the view model with the rewritten text
        model.OutputText = response?.Result?.Text ?? string.Empty;

        return View(model);
    }
}

// ---------------------------------------------------
// Views/Rewriter/Index.cshtml
// ---------------------------------------------------
@model RewriterViewModel
@{
    ViewData["Title"] = "Text Rewriter";
}
<h2>@ViewData["Title"]</h2>

<form asp-action="Index" method="post" class="form-horizontal">
    <div class="form-group">
        <label asp-for="InputText" class="control-label"></label>
        <textarea asp-for="InputText" class="form-control" rows="6"></textarea>
        <span asp-validation-for="InputText" class="text-danger"></span>
    </div>
    <div class="form-group">
        <button type="submit" class="btn btn-primary">Rewrite</button>
    </div>
</form>

@if (!string.IsNullOrWhiteSpace(Model.OutputText))
{
    <hr />
    <h4>Rewritten Text</h4>
    <textarea class="form-control" rows="6" readonly>@Model.OutputText</textarea>
}

@section Scripts {
    @{await Html.RenderPartialAsync("_ValidationScriptsPartial");}
}
```

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update any file paths and configuration values to match your actual environment, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](https://docs.groupdocs.cloud/rewriter/) or reach out to the [support team](https://forum.groupdocs.cloud/c/rewriter/34) for assistance.

## Executing Document Rewriting Via REST API Using cURL

Below is a quick cURL workflow that performs the same rewrite operation via the GroupDocs Rewriter REST endpoints.

### Authenticate and Get Access Token

```bash
curl -X POST "https://api.groupdocs.cloud/v1/auth/token" \
     -H "Content-Type: application/json" \
     -d '{"client_id":"YOUR_CLIENT_ID","client_secret":"YOUR_CLIENT_SECRET"}'
```

The response returns an `access_token` that you will use in subsequent calls.

### Upload the Source Text (optional for large files)

```bash
curl -X POST "https://api.groupdocs.cloud/v1/storage/file/upload" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -F "file=@input.txt"
```

### Execute the Rewrite Operation

```bash
curl -X POST "https://api.groupdocs.cloud/v1/rewriter/rewrite" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "text": "Your original text goes here.",
           "language": "en",
           "targetLanguage": "en",
           "rewriteMode": "Rewrite"
         }'
```

The [JSON](https://docs.fileformat.com/web/json/) response contains the rewritten text in the `result.text` field.

### Download the Result (if you stored it as a file)

```bash
curl -X GET "https://api.groupdocs.cloud/v1/storage/file/download?path=output.txt" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -o rewritten.txt
```

For more details on request parameters and response formats, see the [official API documentation](https://docs.groupdocs.cloud/rewriter/).

## Final Thoughts

Integrating the [GroupDocs.Rewriter Cloud SDK for .NET](https://products.groupdocs.cloud/rewriter/net/) into an ASP.NET Core MVC project is straightforward once you follow this step-by-Step guide to Integrate with ASP.NET Core MVC. The library handles the heavy lifting of natural‑language rewriting, letting you focus on UI and business logic. Remember to secure your AppSid and AppKey, use the temporary license for evaluation, and upgrade to a full license for production workloads. With the code and cURL examples in hand, you can now add intelligent text rewriting to any .NET web application.

## FAQs

**How does the step-by-Step guide to Integrate with ASP.NET Core MVC handle error responses from the API?**  
The controller example checks `ModelState.IsValid` before calling the API and captures the `RewriteResponse`. If the API returns an error, the `response` object will be null, and the view will simply show an empty output. For detailed error handling, consult the [official documentation](https://docs.groupdocs.cloud/rewriter/).

**Can I rewrite documents other than plain text, such as [DOCX](https://docs.fileformat.com/word-processing/docx/) or [PDF](https://docs.fileformat.com/pdf), using the same approach?**  
Yes. The Rewriter API accepts raw text extracted from supported formats. You can first use GroupDocs.Parser or GroupDocs.Conversion to extract text, then pass it to the rewrite endpoint. Both SDKs are listed in the GroupDocs product family.

**Is it possible to run the rewrite operation asynchronously in a high‑traffic web site?**  
Absolutely. The controller uses `await _rewriterApi.RewriteAsync(...)`, which is fully asynchronous and scales with ASP.NET Core's async pipeline. This fits the pattern demonstrated in the step-by-Step guide to Integrate with ASP.NET Core MVC.

**Where can I obtain a temporary license for testing?**  
A temporary license is available from the [temporary license page](https://purchase.groupdocs.cloud/temporary-license/). It lets you evaluate the SDK without committing to a purchase.

## Further Reading
- [Rephrase and Rewrite Documents in .NET | Rewrite Paragraphs online in C#](https://blog.groupdocs.cloud/rewriter/paraphrase-documents-online/)
- [Summarize Document Content in C# .NET | Document Summarization API](https://blog.groupdocs.cloud/rewriter/summarize-document-content-csharp/)