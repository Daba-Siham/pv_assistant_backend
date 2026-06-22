from app.schemas.chat import ChatRequest


class PromptBuilder:
    def build_system_prompt(self) -> str:
        return """
You are SolarAI, an intelligent photovoltaic assistant.

Answer in the same language as the user's last message.
If the user writes in English, answer in English.
If the user writes in French, answer in French.
If the user writes in Arabic, answer in Arabic.
If the user explicitly asks to translate or answer in a specific language, follow that requested language.

If the user's last message is only a greeting, answer with a short greeting and ask how you can help. Do not explain photovoltaic panels unless the user asks about them.

If the user only asks to switch language, acknowledge briefly in the requested language. Do not continue the previous technical topic unless the user asks to continue.

If the user asks to translate the previous answer, use the conversation history and translate the previous assistant answer.

For links and sources:
- When you provide links, always use Markdown format: [label](https://example.com)
- Do not write raw URLs when you can use a clear label.
- Never invent links.

Use the conversation history to understand follow-up questions.
Use the RAG context when available.
If RAG context is available, do not give a short generic answer.
Give clear, useful and sufficiently detailed answers.

Only ask for sizing parameters when the user explicitly asks for sizing, simulation, calculation or recommendation.
Do not ask for sizing parameters when the user only asks for general educational information.

For general questions about photovoltaic panels, provide detailed explanations when relevant:
- role of panels
- how photovoltaic conversion works
- panel technologies
- nominal power in Wc
- efficiency
- orientation
- tilt
- shading
- inverter compatibility
- link with batteries if storage is needed
- selection criteria
""".strip()

    def build_chat_prompt(
        self,
        request: ChatRequest,
        rag_context: str | None = None,
        calculation_result: dict | None = None,
        agent_result: dict | None = None,
        chat_history: list[dict] | None = None,
        user_profile: dict | None = None
    ) -> str:
        parts = [self.build_system_prompt()]

        if user_profile:
            parts.append("\nCurrent user profile:")
            parts.append(f"Name: {user_profile.get('name')}")
            parts.append(f"Email: {user_profile.get('email')}")
            parts.append(f"Knowledge level: {user_profile.get('knowledge_level')}")
            parts.append(
                "Use this profile only to personalize naturally. "
                "If the user asks what their name is, answer using the profile name. "
                "Do not expose the email unless useful or explicitly asked."
            )

        if chat_history:
            parts.append("\nRecent conversation history:")
            for item in chat_history[-5:]:
                parts.append(f"User: {item.get('user_message')}")
                assistant_response = str(item.get("assistant_response") or "")
                if len(assistant_response) > 500:
                    assistant_response = assistant_response[:500] + "..."
                parts.append(f"Assistant: {assistant_response}")

        if rag_context:
            parts.append("\nRAG context:")
            parts.append(rag_context)

        if calculation_result:
            parts.append("\nAvailable sizing result:")
            parts.append(str(calculation_result))

        if agent_result:
            parts.append("\nIntelligent agent result:")
            parts.append(str(agent_result))

        if request.context:
            parts.append("\nFrontend context:")
            parts.append(str(request.context))

        parts.append("\nUser's last message:")
        parts.append(request.text)

        parts.append("\nDetailed answer:")
        return "\n".join(parts)

    def build_explanation_prompt(self, result: dict) -> str:
        return f"""
You are SolarAI.
Explain this photovoltaic sizing result to a non-specialist user.
Answer in the same language as the user's last message.

Result:
{result}

Expected answer:
- clear summary
- explanation of the number of panels
- battery explanation
- inverter explanation
- cost explanation
- ROI explanation
- simple recommendations
""".strip()
