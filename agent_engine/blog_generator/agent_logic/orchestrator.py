"""
Orchestrator with OpenAI Agents SDK + Runner + Metrics Tracking
NOW USING CENTRALIZED LLM SERVICE
"""
from agents import set_tracing_disabled
from config import settings
from tools.mcp_tools import generate_markdown_file, fetch_category_related_articles, gist_injector, generate_blog_image, fetch_keywords_auto
from utils import prompts
from utils.seo_validator import validate_seo_content, validate_and_fix_meta_description, validate_and_fix_seo_title
from utils.file_format_mappings import FILE_FORMAT_MAPPINGS, BASE_URL
from utils.helpers import mark_topic_as_generated, prepare_context, get_productInfo, get_topic_by_index, inject_file_format_links, slugify, normalize_case_preserve_formats_in_keywords, clean_ai_generated_markdown, validate_markdown_links, capitalize_file_formats_for_title, setup_logger, generate_tags_with_llm, save_blog_metadata_to_sheet, extract_blog_metadata, get_topic_from_sheet, get_next_tab, extract_product_names, get_recent_layouts, convert_sheet_row_to_file_format, update_last_processed_product
from utils.layouts import select_layout
from utils.code_snippet import generate_code_snippet
from utils.metricsRecorder import MetricsRecorder
from services.LLMservice import llm_service
import json
import os

class BlogOrchestrator: 
    def __init__(self, brand="aspose.com", agent_owner="Muhammad Mustafa", run_env=None):
        """
        Initialize Blog Orchestrator
        
        Args:
            brand: Brand name (aspose.com, groupdocs.com, conholdate.com)
            agent_owner: Name of the agent owner
            run_env: Environment - "DEV" or "PROD" (auto-detected if None)
        """
        self.brand = brand.lower().strip()
        self.products = self.load_products()
        self.log = setup_logger()
        
        # Initialize metrics recorder with updated parameters
        self.metrics = MetricsRecorder(
            agent_name="Blog Post Generator",
            agent_owner=agent_owner,
            job_type="Blog Post Generation",
            run_env=run_env
        )
        
        print(f" Orchestrator initialized")
        print(f"   Run ID: {self.metrics.run_id}")
        print(f"   Environment: {self.metrics.run_env}")
        print(f"   Owner: {self.metrics.agent_owner}")

    def load_products(self):
        """Load products from correct JSON based on brand name"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "../../", "content/productsData")
        
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"Data directory not found: {data_dir}")
        
        filename = f"{self.brand}.json"
        products_path = os.path.join(data_dir, filename)
        
        if not os.path.exists(products_path):
            available_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
            available_brands = [f.replace('.json', '') for f in available_files]
            raise FileNotFoundError(
                f"Products file not found for brand '{self.brand}'. "
                f"Available brands: {', '.join(available_brands)}"
            )
        
        with open(products_path, "r") as f:
            return json.load(f)

    async def create_blog_autonomously(
        self, 
        author: str = "",
    ):
        """Let the agent autonomously create a blog with metrics tracking"""
        set_tracing_disabled(disabled=True)

        # ── GSC-first topic selection ────────────────────────────────────
        # Fail-safe by design: any error here (API, quota, sheets, parsing)
        # logs a warning and falls through to the existing round-robin flow,
        # so current behavior is never affected.
        gsc_selection = None
        try:
            from services.gsc_selector import select_topic_via_gsc
            gsc_selection = select_topic_via_gsc(self.brand)
        except Exception as gsc_err:
            print(f"⚠️ GSC selection unavailable ({gsc_err}); using round-robin", flush=True)

        if gsc_selection:
            sheet_name = gsc_selection["tab"]
            topics_raw_data = convert_sheet_row_to_file_format(gsc_selection["row"])
            row_number = gsc_selection["row_number"]
            print(
                f"🎯 Topic selected via GSC opportunity '{gsc_selection['keyword']}' "
                f"(tab: {sheet_name}, row: {row_number})",
                flush=True,
            )
        else:
            # ── Fallback: existing round-robin selection (unchanged) ─────
            sheet_name = get_next_tab()

            if not sheet_name:
                print("No approved topics found in any tab. Exiting gracefully.")
                return {
                    "status": "skipped",
                    "message": "No approved topics found in any tab"
                }
            print("going down further")
            # Get first approved topic from that tab
            result = get_topic_from_sheet(sheet_name)
            if not result:
                print(f"No approved topics in {sheet_name}, skipping.")
                return
            topics_raw_data, row_number = result
        print(f"sheet data {topics_raw_data}")
        allowed_products = extract_product_names(self.products)
        post_topic = topics_raw_data.pop("topic")
        product_name = topics_raw_data.pop("product")
        platform = topics_raw_data.pop("platform")
 
        # Get product info
        try:
            product_info = get_productInfo(product_name, platform, self.products, self.brand)
        except ValueError as e:
            print(f"❌ Product info error: {e}. Skipping.")
            return {
                "status": "skipped",
                "message": str(e)
            }
        
        print(f"product info -- {product_info}")
       
        isCloud = "cloud" in product_info["ProductName"].lower()
        post_topic = capitalize_file_formats_for_title(post_topic, FILE_FORMAT_MAPPINGS)

        print(f"[METRICS DEBUG] After seo_title => api_call_count: {self.metrics.api_call_count}, token_usage: {self.metrics.token_usage['total_tokens']}", flush=True)

        if isCloud:
            product_name = product_name.split(' Cloud')[0]

        # Start metrics tracking
        self.metrics.start_job(
            product=product_name,
            platform=platform,
            website=self.brand
        )
        product_name = product_info.get("ProductName")
        
        try:
            context = prepare_context(product_info)
            
            print("📚 Connecting to fetch_category_related_articles MCP server")
            related_links = await fetch_category_related_articles(
                post_topic, 
                product_name, 
                product_info.get('BlogsURL'), 
                3
            )
            # ── Record HTTP calls made by the MCP scraper ────────────────────
            scan_stats = related_links.get("scan_stats", {}) if isinstance(related_links, dict) else {}
            http_calls = scan_stats.get("tier1_scanned", 0) + scan_stats.get("tier2_scanned", 0)
            if http_calls:
                self.metrics.record_http_call(
                    count=http_calls,
                    caller="fetch_category_related_articles"
                )
            # ─────────────────────────────────────────────────────────────────
        
            primary = topics_raw_data.get("keywords", {}).get("primary", [])
            secondary = topics_raw_data.get("keywords", {}).get("secondary", [])
            target_persona = topics_raw_data.get("target_persona", "")
            blog_post_angle = topics_raw_data.get("angle", "")
            long_tail_keywords = topics_raw_data.get("keywords", {}).get("long_tail", [])
            semantic_keywords = topics_raw_data.get("keywords", {}).get("semantic", [])
            other_important_and_relevant_things = topics_raw_data.get("other_notes", "")
            blog_outline = topics_raw_data.get("outline")

            print(f"primary -- {primary}", flush=True)
            print(f"secondary -- {secondary}", flush=True)
            print(f"target persona -- {target_persona}", flush=True)
            print(f"Blog post angle -- {blog_post_angle}", flush=True)
            print(f"long_tail_keywords -- {long_tail_keywords}", flush=True)
            print(f"semantic_keywords -- {semantic_keywords}", flush=True)
            print(f"blog_outline -- {blog_outline}", flush=True)
            print(f"other_important_and_relevant_things -- {other_important_and_relevant_things}", flush=True)
            
            f_keywords = normalize_case_preserve_formats_in_keywords(primary + secondary, FILE_FORMAT_MAPPINGS)
            print(f"normalized f_keywords -- {f_keywords}")

         
            
            print(f" Generating content now. ")
            tags = await generate_tags_with_llm(post_topic,f_keywords, blog_outline, self.metrics )
            print(f"tags are -- {tags}")

            # ── Layout selection: sheet override -> signals -> anti-repeat ──
            try:
                recent_layouts = get_recent_layouts(product=sheet_name, limit=2)
            except Exception as layout_err:
                print(f"⚠️ Could not read recent layouts ({layout_err}), continuing without history")
                recent_layouts = []

            layout_choice = select_layout(
                topic=post_topic,
                angle=blog_post_angle,
                persona=target_persona,
                is_cloud=isCloud,
                recent_layouts=recent_layouts,
                override=topics_raw_data.get("layout", ""),
            )
            print(f"📐 Layout: {layout_choice.name} (reason: {layout_choice.reason})", flush=True)
            print(f"📐 Skeleton: {' -> '.join(layout_choice.skeleton())}", flush=True)
            # ─────────────────────────────────────────────────────────────────

            # ── Code snippet generation: single source-of-truth code, up to  ──
            # ── 3 retries. The whole post is built around this snippet, so  ──
            # ── a total failure here aborts the run rather than falling     ──
            # ── back to the writer inventing code inline.                   ──
            print("💻 Generating source-of-truth code snippet...", flush=True)
            generated_code = await generate_code_snippet(
                topic=post_topic,
                primary_keyword=f_keywords[0],
                platform=platform,
                context=context,
                outline=blog_outline,
                is_cloud=isCloud,
                max_retries=3,
                metrics=self.metrics,
            )
            if not generated_code:
                message = "Code snippet generation failed after 3 attempts. Aborting blog generation."
                print(f"❌ {message}", flush=True)
                self.metrics.record_failure(message)
                self.metrics.end_job()
                return {
                    "status": "error",
                    "message": message,
                    "run_id": self.metrics.run_id,
                    "token_usage": self.metrics.token_usage["total_tokens"],
                    "api_call_count": self.metrics.api_call_count,
                }
            # ─────────────────────────────────────────────────────────────────

            # ════════════════════════════════════════════════════════════════════
            # UPDATED: Using centralized LLM service instead of direct Agent creation
            # ════════════════════════════════════════════════════════════════════
            instructions = prompts.get_blog_writer_prompt(
                post_topic,
                f_keywords,
                blog_outline,
                related_links,
                context,
                author,
                target_persona,
                blog_post_angle,
                long_tail_keywords,
                semantic_keywords,
                other_important_and_relevant_things,
                tags,
                isCloud,
                allowed_products,
                layout_choice=layout_choice,
                generated_code=generated_code
            )
        
            result = await llm_service.run_agent(
                instructions=instructions,
                context=context,
                agent_name="blog-writer-agent",
                temperature=0.4,
                max_turns=10,
                max_tokens=16000
            )
            if not result or not result.final_output:
                print("⚠️ LLM returned empty output. Ending execution gracefully.")
                return {
                    "status": "skipped",
                    "message": "LLM returned empty output"
                }
            
             
            # ── Record token usage from the main blog-writing agent call ────
            self.metrics.record_llm_usage(
                input_tokens=result.token_usage["input_tokens"],
                output_tokens=result.token_usage["output_tokens"],
                caller="blog-writer-agent"
            )
            # ─────────────────────────────────────────────────────────────────
            # ════════════════════════════════════════════════════════════════════

            # Validate and fix if needed
            fixed_content, was_fixed = await validate_and_fix_meta_description(result.final_output, metrics=self.metrics)
            print(f"[METRICS DEBUG] After meta_description => api_call_count: {self.metrics.api_call_count}, token_usage: {self.metrics.token_usage['total_tokens']}", flush=True)
            
            if was_fixed:
                print(f"✅ Meta description was corrected and is now valid (140-160 chars)", flush=True)
                result.final_output = fixed_content
            else:
                print(f"✅ Meta description is already valid", flush=True)
            
            print(f"Meta description check done")
            result.final_output = clean_ai_generated_markdown(result.final_output)
            print(f"clean_ai_generated_markdown done ")
            
            result.final_output = validate_markdown_links(result.final_output)
            print(f"validate_markdown_links done ")
            print(f" Content Generated, Performing SEO Audit Now --", flush=True)

            targets = {
                "primary_keyword": f_keywords[0],
                "target_keyword_count": 5,
                "min_words": settings.NUMBER_OF_BLOG_WORDS
            }
            report = validate_seo_content(result.final_output, targets)
            print(f" Audit completed -- {report}", flush=True)
             
            blog_post_metadata = extract_blog_metadata(result.final_output)
          
            jistified = await gist_injector(result.final_output, post_topic, blog_post_metadata["summary"], f'https://blog.{self.brand}{blog_post_metadata["url"]}')
            text_output = jistified.content[0].text
            data = json.loads(text_output)
            # final_content = data["jistified_content"]
            gist_url = data.get("gist_url", "")
           
           
            final_content = inject_file_format_links(result.final_output, FILE_FORMAT_MAPPINGS, BASE_URL)
            
            print(f" Generating markdown file")
            file_res = await generate_markdown_file(
                title=post_topic,
                content=final_content,
                brand=self.brand
            )
         
            filepath = file_res.get("output", {}).get("filepath")
            folder_name = file_res.get("output", {}).get("folder_name")
            banner_location = f"../../content/blogPosts/{file_res['output']['brand_folder']}/{file_res['output']['folder_name']}/images/{slugify(post_topic)}.jpg"
            banner = await generate_blog_image(product_name, post_topic, "Left", banner_location)
            print(f"banner generated -- {banner}", flush=True)

            # Record success
            self.metrics.record_success(f"Blog post created: {filepath}")
            
            # End job and send metrics
            self.metrics.end_job()
            
            print(f"\n✅ Blog post generation completed!")
            print(f"📄 File: {filepath}")
            print(f"⏱️  Duration: {self.metrics.run_duration_ms}ms\n")
            
            # Print and send metrics
            self.metrics.print_summary()
            print("📊 Sending metrics to Google Script... ")
          
            metrics_sent_for_team = await self.metrics.send_metrics_to_team()
            metrics_sent_for_pro = await self.metrics.send_metrics_to_prod()
            
            if metrics_sent_for_team and metrics_sent_for_pro:
                print(f"Metrics sent successfully\n {metrics_sent_for_pro}",flush=True)
            else:
                print("Failed to send metrics (check logs)\n")
            

            self.log("---Execution started---")
            self.log(f"Topic-> {post_topic}")
            self.log(f"Layout-> {layout_choice.name} ({layout_choice.reason})")
            self.log(f"Brand-> {self.brand}")
            self.log(f"Keywords -> {topics_raw_data}")
            self.log(f"product info {product_info}")
            self.log(f" File path: {filepath}")
            self.log("---Execution ended---")
            mark_topic_as_generated(sheet_name, row_number)

            # Advance the rotation pointer only for round-robin picks so
            # GSC-driven picks never disturb the fallback rotation's fairness.
            if not gsc_selection:
                try:
                    update_last_processed_product(sheet_name)
                except Exception as state_err:
                    print(f"⚠️ Could not update rotation pointer (non-fatal): {state_err}", flush=True)

            # Write product name for GitHub Actions to read. Use the resolved
            # product's urlPrefix (same source of truth as the post content
            # itself), not sheet_name - sheet_name is only the rotation tab
            # label and can mismatch the topic's actual product.
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            with open(os.path.join(base_dir, "product_name.txt"), "w") as f:
                f.write(product_info.get("urlPrefix", sheet_name))

            save_blog_metadata_to_sheet(
                brand=self.brand,
                url= f'https://blog.{self.brand}{blog_post_metadata["url"]}',
                title=blog_post_metadata['title'],
                author=blog_post_metadata['author'],
                gist_url=gist_url,
                published_date=blog_post_metadata['date'],
                product=sheet_name,
                layout=layout_choice.name
                )
            
            return {
                "folder_name": folder_name,
                "product": product_name,
                "platform": platform,
                "brand": self.brand,
                "layout": layout_choice.name,
                "SEO_Score": report["score"],
                "run_id": self.metrics.run_id,
                "duration_ms": self.metrics.run_duration_ms,
                "token_usage": self.metrics.token_usage["total_tokens"],
                "api_call_count": self.metrics.api_call_count,
                "status": "success"
            }

        except Exception as e:
            import traceback
            print(f"\n Blog generation failed!", flush=True)
            print(f"Error: {e}", flush=True)
            traceback.print_exc()
            
            # Record failure
            self.metrics.record_failure(str(e))
            self.metrics.end_job()
            
            # Print and send metrics even on failure
            self.metrics.print_summary()
            print(" Sending failure metrics...")
            # await self.metrics.send_metrics_to_team()
            # await self.metrics.send_metrics_to_prod()

            return {
                "status": "error",
                "message": str(e),
                "run_id": self.metrics.run_id,
                "token_usage": self.metrics.token_usage["total_tokens"],
                "api_call_count": self.metrics.api_call_count,
            }

    async def create_blog_from_manual_input(
        self,
        author: str,
        product: str,
        platform: str,
        topic: str,
        outline_text: str = "",
        keywords_text: str = "",
        merge_with_serp: bool = False,
        layout_override: str = "",
    ):
        """
        Generate a blog post from a user-supplied topic/outline/keywords
        instead of pulling from the approved-topics sheet. There is no sheet
        row for this run, so nothing gets marked as generated and the
        rotation pointer is untouched. This method never pushes anything to
        a downstream repo - the caller (workflow) is responsible for
        retrieving the generated folder, e.g. via an artifact upload.
        """
        set_tracing_disabled(disabled=True)

        try:
            product_info = get_productInfo(product, platform, self.products, self.brand)
        except ValueError as e:
            print(f"❌ Product info error: {e}. Aborting.", flush=True)
            return {"status": "error", "message": str(e)}

        isCloud = "cloud" in product_info["ProductName"].lower()
        post_topic = capitalize_file_formats_for_title(topic, FILE_FORMAT_MAPPINGS)
        product_name = product_info.get("ProductName")

        self.metrics.start_job(product=product_name, platform=platform, website=self.brand)

        try:
            context = prepare_context(product_info)

            print("📚 Connecting to fetch_category_related_articles MCP server")
            related_links = await fetch_category_related_articles(
                post_topic,
                product_name,
                product_info.get('BlogsURL'),
                3
            )
            scan_stats = related_links.get("scan_stats", {}) if isinstance(related_links, dict) else {}
            http_calls = scan_stats.get("tier1_scanned", 0) + scan_stats.get("tier2_scanned", 0)
            if http_calls:
                self.metrics.record_http_call(count=http_calls, caller="fetch_category_related_articles")

            # ── Keywords: user-supplied, optionally merged with SERP research ──
            user_keywords = [k.strip() for k in keywords_text.split(",") if k.strip()]
            if not user_keywords:
                user_keywords = [post_topic]

            primary = [user_keywords[0]]
            secondary = user_keywords[1:]

            if merge_with_serp:
                print("🔍 Merging with SERP-based keyword research...", flush=True)
                serp_keywords = await fetch_keywords_auto(post_topic, product_name, platform)
                for kw in serp_keywords:
                    if kw not in primary and kw not in secondary:
                        secondary.append(kw)

            f_keywords = normalize_case_preserve_formats_in_keywords(primary + secondary, FILE_FORMAT_MAPPINGS)
            blog_outline = [item.strip() for item in outline_text.split(",") if item.strip()]
            allowed_products = extract_product_names(self.products)

            print(f" Generating content now. ")
            tags = await generate_tags_with_llm(post_topic, f_keywords, blog_outline, self.metrics)
            print(f"tags are -- {tags}")

            # ── Layout: explicit override wins outright, same mechanism as ──
            # ── the sheet-driven flow; empty/"auto" falls through to the   ──
            # ── normal signal-based weighted selection.                    ──
            layout_choice = select_layout(
                topic=post_topic,
                angle="",
                persona="",
                is_cloud=isCloud,
                recent_layouts=[],
                override=layout_override,
            )
            print(f"📐 Layout: {layout_choice.name} (reason: {layout_choice.reason})", flush=True)
            print(f"📐 Skeleton: {' -> '.join(layout_choice.skeleton())}", flush=True)

            # ── Code snippet generation: same source-of-truth step and     ──
            # ── abort-on-total-failure contract as the automated flow.     ──
            print("💻 Generating source-of-truth code snippet...", flush=True)
            generated_code = await generate_code_snippet(
                topic=post_topic,
                primary_keyword=f_keywords[0],
                platform=platform,
                context=context,
                outline=blog_outline,
                is_cloud=isCloud,
                max_retries=3,
                metrics=self.metrics,
            )
            if not generated_code:
                message = "Code snippet generation failed after 3 attempts. Aborting blog generation."
                print(f"❌ {message}", flush=True)
                self.metrics.record_failure(message)
                self.metrics.end_job()
                return {
                    "status": "error",
                    "message": message,
                    "run_id": self.metrics.run_id,
                    "token_usage": self.metrics.token_usage["total_tokens"],
                    "api_call_count": self.metrics.api_call_count,
                }

            instructions = prompts.get_blog_writer_prompt(
                post_topic,
                f_keywords,
                blog_outline,
                related_links,
                context,
                author,
                "",
                "",
                [],
                [],
                "",
                tags,
                isCloud,
                allowed_products,
                layout_choice=layout_choice,
                generated_code=generated_code
            )

            result = await llm_service.run_agent(
                instructions=instructions,
                context=context,
                agent_name="blog-writer-agent",
                temperature=0.4,
                max_turns=10,
                max_tokens=16000
            )
            if not result or not result.final_output:
                print("⚠️ LLM returned empty output. Ending execution gracefully.")
                return {
                    "status": "skipped",
                    "message": "LLM returned empty output"
                }

            self.metrics.record_llm_usage(
                input_tokens=result.token_usage["input_tokens"],
                output_tokens=result.token_usage["output_tokens"],
                caller="blog-writer-agent"
            )

            fixed_content, was_fixed = await validate_and_fix_meta_description(result.final_output, metrics=self.metrics)
            if was_fixed:
                result.final_output = fixed_content

            result.final_output = clean_ai_generated_markdown(result.final_output)
            result.final_output = validate_markdown_links(result.final_output)
            print(f" Content Generated, Performing SEO Audit Now --", flush=True)

            targets = {
                "primary_keyword": f_keywords[0],
                "target_keyword_count": 5,
                "min_words": settings.NUMBER_OF_BLOG_WORDS
            }
            report = validate_seo_content(result.final_output, targets)
            print(f" Audit completed -- {report}", flush=True)

            blog_post_metadata = extract_blog_metadata(result.final_output)

            jistified = await gist_injector(result.final_output, post_topic, blog_post_metadata.get("summary", ""), f'https://blog.{self.brand}{blog_post_metadata.get("url", "")}')
            text_output = jistified.content[0].text
            data = json.loads(text_output)
            gist_url = data.get("gist_url", "")

            final_content = inject_file_format_links(result.final_output, FILE_FORMAT_MAPPINGS, BASE_URL)

            print(f" Generating markdown file")
            file_res = await generate_markdown_file(
                title=post_topic,
                content=final_content,
                brand=self.brand
            )

            filepath = file_res.get("output", {}).get("filepath")
            folder_name = file_res.get("output", {}).get("folder_name")
            full_path = file_res.get("output", {}).get("full_path")
            banner_location = f"../../content/blogPosts/{file_res['output']['brand_folder']}/{file_res['output']['folder_name']}/images/{slugify(post_topic)}.jpg"
            banner = await generate_blog_image(product_name, post_topic, "Left", banner_location)
            print(f"banner generated -- {banner}", flush=True)

            # ── No sheet row exists for this run: nothing to mark as       ──
            # ── generated, no rotation pointer to advance, no metadata     ──
            # ── sheet write. Product name is still written out (same as    ──
            # ── the automated flow) so a caller workflow can optionally    ──
            # ── commit/PR the result using the same downstream steps.      ──
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            with open(os.path.join(base_dir, "product_name.txt"), "w") as f:
                f.write(product_info.get("urlPrefix", product))

            self.metrics.record_success(f"Blog post created: {filepath}")
            self.metrics.end_job()

            print(f"\n✅ Blog post generation completed!")
            print(f"📄 File: {filepath}")
            print(f"⏱️  Duration: {self.metrics.run_duration_ms}ms\n")

            self.metrics.print_summary()
            print("📊 Sending metrics to Google Script... ")

            metrics_sent_for_team = await self.metrics.send_metrics_to_team()
            metrics_sent_for_pro = await self.metrics.send_metrics_to_prod()

            if metrics_sent_for_team and metrics_sent_for_pro:
                print(f"Metrics sent successfully\n {metrics_sent_for_pro}", flush=True)
            else:
                print("Failed to send metrics (check logs)\n")

            return {
                "folder_name": folder_name,
                "folder_path": full_path,
                "product": product_name,
                "platform": platform,
                "brand": self.brand,
                "layout": layout_choice.name,
                "SEO_Score": report["score"],
                "run_id": self.metrics.run_id,
                "duration_ms": self.metrics.run_duration_ms,
                "token_usage": self.metrics.token_usage["total_tokens"],
                "api_call_count": self.metrics.api_call_count,
                "status": "success"
            }

        except Exception as e:
            import traceback
            print(f"\n Blog generation failed!", flush=True)
            print(f"Error: {e}", flush=True)
            traceback.print_exc()

            self.metrics.record_failure(str(e))
            self.metrics.end_job()
            self.metrics.print_summary()

            return {
                "status": "error",
                "message": str(e),
                "run_id": self.metrics.run_id,
                "token_usage": self.metrics.token_usage["total_tokens"],
                "api_call_count": self.metrics.api_call_count,
            }