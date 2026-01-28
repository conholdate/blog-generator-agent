from agent_engine.content_gap_agent.cli import RunArgs, run_sync

if __name__ == "__main__":
    out = run_sync(
        RunArgs(
            blog="aspose",
            product="cells",
            platform="net",      # or None to run all platforms
            config_dir="./config",
            cache_dir="./repo_cache",
            output_dir="./output",
            flush=False,
        )
    )
    print(out)
