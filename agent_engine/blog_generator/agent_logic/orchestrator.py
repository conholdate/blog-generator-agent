"""
Orchestrator with OpenAI Agents SDK + Runner + Metrics Tracking
"""
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel, set_tracing_disabled, ModelSettings
from config import settings
from tools.mcp_tools import generate_markdown_file, fetch_category_related_articles, gist_injector, generate_blog_image
from utils import prompts
from utils.seo_validator import validate_seo_content
from utils.file_format_mappings import FILE_FORMAT_MAPPINGS, BASE_URL
from utils.helpers import prepare_context, get_productInfo, get_topic_by_index, inject_file_format_links, slugify
from utils.metricsRecorder import MetricsRecorder
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

        self.client = AsyncOpenAI(
            base_url=settings.PROFESSIONALIZE_BASE_URL,
            api_key=settings.PROFESSIONALIZE_API_KEY
        )
        self.model = OpenAIChatCompletionsModel(
            model=settings.PROFESSIONALIZE_LLM_MODEL,
            openai_client=self.client
        )

        self.products = self.load_products()
        
        # Initialize metrics recorder with updated parameters
        self.metrics = MetricsRecorder(
            agent_name="Blog Post Generator",
            agent_owner=agent_owner,
            job_type="Blog Post Generation",
            run_env=run_env
        )
        
        print(f"🤖 Orchestrator initialized")
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
        topics_file: str, 
        author: str = ""
    ):
        """Let the agent autonomously create a blog with metrics tracking"""
        set_tracing_disabled(disabled=True)
        topics_raw_data = get_topic_by_index(topics_file)
        post_topic = topics_raw_data.pop("topic")
        product_name = topics_raw_data.pop("product")
        platform = topics_raw_data.pop("platform")
        
        # Get product info
        product_info = get_productInfo(product_name, platform, self.products)
        print(f"Product Infor --- {product_info}", flush=True)
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
    
            primary = topics_raw_data.get("keywords", {}).get("primary", [])
            secondary = topics_raw_data.get("keywords", {}).get("secondary", [])
            target_persona = topics_raw_data.get("target_persona", "")
            angle = topics_raw_data.get("angle", "")
            print(f"primary -- {primary}", flush=True)
            print(f"secondary -- {secondary}", flush=True)
            print(f"target persona -- {target_persona}", flush=True)
            print(f"angle -- {angle}", flush=True)

            f_keywords = primary + secondary
            print(f"f_keywords -- {f_keywords}")
  
            blog_outline = topics_raw_data.get("outline")
            # post_topic = sanitize_markdown_title(post_topic)
            
            print(f" Generating content now.")
       
            agent = Agent(
                name="blog-writer-agent",
                instructions=prompts.get_blog_writer_prompt(
                    post_topic,
                    f_keywords,
                    blog_outline,
                    related_links,
                    context,
                    author,
                    platform,
                    target_persona,
                    angle
                ),
                model=self.model,
                model_settings=ModelSettings(temperature=0.6)
            )

            result = await Runner.run(agent, context, max_turns=10)
            print(f" Content Generated, Performing SEO Audti Now --", flush=True)
            targets = {
                "primary_keyword": f_keywords[0],
                "target_keyword_count": 5,
                "min_words": settings.NUMBER_OF_BLOG_WORDS
            }
            report = validate_seo_content(result.final_output, targets)
            print(f" Audit completed -- {report}", flush=True)
             
            print(f" Injecting gists now -- ",flush=True)
            
            jistified = await gist_injector(result.final_output, post_topic)

            text_output = jistified.content[0].text
            data = json.loads(text_output)
            final_content = data["jistified_content"]
            final_content = inject_file_format_links(final_content, FILE_FORMAT_MAPPINGS, BASE_URL)
            print(f" Generating markdown file")
            file_res = await generate_markdown_file(
                title=post_topic,
                content=final_content,
                brand= self.brand
            )
         
            filepath = file_res.get("output", {}).get("filepath")
            folder_name = file_res.get("output", {}).get("folder_name")
            banner_location = f"../../content/blogPosts/{file_res['output']['brand_folder']}/{file_res['output']['folder_name']}/images/{slugify(post_topic)}.png"
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
            print("📊 Sending metrics to Google Script...")
            # metrics_sent_for_team = await self.metrics.send_metrics_to_team()
            # metrics_sent_for_pro = await self.metrics.send_metrics_to_prod()
            
            # if metrics_sent_for_team and metrics_sent_for_pro:
            #     print("Metrics sent successfully\n")
            # else:
            #     print("Failed to send metrics (check logs)\n")

            return {
                "folder_name": folder_name,
                "product": product_name,
                "platform": platform,
                "brand": self.brand,
                "SEO_Score": report["score"],
                "run_id": self.metrics.run_id,
                "duration_ms": self.metrics.run_duration_ms,
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
                "run_id": self.metrics.run_id
            }