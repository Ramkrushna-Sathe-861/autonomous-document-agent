from app.workflow import AgentOrchestrator, build_graph


class FakeLLM:
    async def structured_complete(self, prompt: str, **kwargs):
        if "Create an execution plan" in prompt:
            return {
                "document_type": "project proposal",
                "document_title": "Sample Proposal",
                "assumptions": ["Assumption"],
                "total_steps": 2,
                "steps": [
                    {
                        "step_number": 1,
                        "action": "Overview",
                        "description": "Summarize the request.",
                        "dependencies": [],
                    },
                    {
                        "step_number": 2,
                        "action": "Delivery",
                        "description": "Describe delivery and success measures.",
                        "dependencies": [1],
                    },
                ],
                "estimated_sections": 2,
            }
        return {
            "status": "PASS",
            "issues": [],
            "suggestions": [],
            "confidence_score": 0.95,
        }

    async def complete(self, prompt: str, **kwargs):
        return "Sample content for this section."


def test_graph_builder_compiles() -> None:
    orchestrator = AgentOrchestrator(FakeLLM())
    graph = build_graph(orchestrator)
    assert graph is not None
