from agent_engine.blog_keyword_analyzer.tools.normalization import KeywordRefiner
from agent_engine.blog_keyword_analyzer.tools.topic_acceptance import finalize_topic_acceptance


def test_kra_title_case_preserves_omr_and_step_by_step() -> None:
    refiner = KeywordRefiner()

    assert (
        refiner.to_title_case("STEP-by-STEP Guide to Read Omr Sheet from PNG in .NET")
        == "Step-by-Step Guide to Read OMR Sheet from PNG in .NET"
    )
    assert (
        refiner.to_title_case("STEP-by-STEP Parse Omr Image from Memorystream in Java")
        == "Step-by-Step Parse OMR Image from MemoryStream in Java"
    )


def test_kra_acceptance_fixes_malformed_platform_developer_guide() -> None:
    result = finalize_topic_acceptance(
        title="Parse Omr Survey Results in .NET-a Developer Guide",
        primary_keyword="Parse Omr Survey Results in .NET",
        platform=".NET",
    )

    assert result.title == "Parse OMR Survey Results in .NET: A Developer Guide"


def test_kra_acceptance_adds_missing_omr_answer_sheet_format_preposition() -> None:
    result = finalize_topic_acceptance(
        title="How to Parse Omr Answer Sheet JPG in .NET",
        primary_keyword="Parse Omr Answer Sheet JPG in .NET",
        platform=".NET",
    )

    assert result.title == "How to Parse OMR Answer Sheet from JPG in .NET"
