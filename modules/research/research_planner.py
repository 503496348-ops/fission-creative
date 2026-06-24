"""
Research Planner — topic decomposition and research question generation.
Inspired by GPT-Researcher's Plan-and-Solve approach.

Decomposes a broad topic into structured research questions,
assigns priority, and generates an execution plan.
"""

import json
import re
import logging
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    FACTUAL = "factual"        # What is X?
    ANALYTICAL = "analytical"  # Why does X happen?
    COMPARATIVE = "comparative"  # How does X compare to Y?
    EVALUATIVE = "evaluative"  # Is X effective?
    EXPLORATORY = "exploratory"  # What are the implications of X?


class Priority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class ResearchQuestion:
    """A single research question with metadata."""
    id: str
    question: str
    question_type: QuestionType
    priority: Priority
    sub_questions: list["ResearchQuestion"] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    answer: Optional[str] = None
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "question": self.question,
            "type": self.question_type.value,
            "priority": self.priority.value,
            "sub_questions": [sq.to_dict() for sq in self.sub_questions],
            "sources": self.sources,
            "answer": self.answer,
            "confidence": self.confidence,
        }


@dataclass
class ResearchPlan:
    """Structured research plan for a topic."""
    topic: str
    questions: list[ResearchQuestion]
    estimated_depth: int = 3  # max recursion depth
    search_queries: list[str] = field(default_factory=list)
    outline: list[str] = field(default_factory=list)

    def total_questions(self) -> int:
        count = len(self.questions)
        for q in self.questions:
            count += len(q.sub_questions)
        return count

    def critical_questions(self) -> list[ResearchQuestion]:
        return [q for q in self.questions if q.priority == Priority.CRITICAL]


class ResearchPlanner:
    """
    Generates structured research plans from topics.

    Uses heuristics and LLM integration to:
    1. Decompose topics into research questions
    2. Classify question types
    3. Prioritize questions
    4. Generate search queries
    5. Create document outlines
    """

    def __init__(self, llm_fn: Optional[callable] = None):
        self.llm_fn = llm_fn

    def plan(self, topic: str, depth: int = 3, num_questions: int = 5) -> ResearchPlan:
        """
        Generate a research plan for a topic.

        Args:
            topic: The research topic
            depth: Maximum sub-question depth
            num_questions: Number of top-level questions to generate

        Returns:
            ResearchPlan with questions, search queries, and outline
        """
        questions = self._generate_questions(topic, num_questions)
        search_queries = self._generate_search_queries(topic, questions)
        outline = self._generate_outline(topic, questions)

        return ResearchPlan(
            topic=topic,
            questions=questions,
            estimated_depth=depth,
            search_queries=search_queries,
            outline=outline,
        )

    def _generate_questions(self, topic: str, num: int) -> list[ResearchQuestion]:
        """Generate research questions for a topic."""
        if self.llm_fn:
            return self._generate_questions_llm(topic, num)
        return self._generate_questions_heuristic(topic, num)

    def _generate_questions_heuristic(self, topic: str, num: int) -> list[ResearchQuestion]:
        """Generate questions using heuristic templates."""
        templates = [
            (f"What is {topic} and why is it important?", QuestionType.FACTUAL, Priority.CRITICAL),
            (f"What are the key components or aspects of {topic}?", QuestionType.ANALYTICAL, Priority.HIGH),
            (f"How has {topic} evolved over time?", QuestionType.EXPLORATORY, Priority.MEDIUM),
            (f"What are the main challenges or criticisms of {topic}?", QuestionType.EVALUATIVE, Priority.HIGH),
            (f"How does {topic} compare to alternatives?", QuestionType.COMPARATIVE, Priority.MEDIUM),
            (f"What are the practical applications of {topic}?", QuestionType.FACTUAL, Priority.HIGH),
            (f"What does current research say about {topic}?", QuestionType.ANALYTICAL, Priority.CRITICAL),
            (f"What are the future trends for {topic}?", QuestionType.EXPLORATORY, Priority.LOW),
        ]

        questions = []
        for i, (q_text, q_type, priority) in enumerate(templates[:num]):
            sq = self._generate_sub_questions(topic, q_text, 2)
            questions.append(ResearchQuestion(
                id=f"q{i+1}",
                question=q_text,
                question_type=q_type,
                priority=priority,
                sub_questions=sq,
            ))
        return questions

    def _generate_questions_llm(self, topic: str, num: int) -> list[ResearchQuestion]:
        """Generate questions using LLM."""
        prompt = f"""Generate {num} research questions about: {topic}

Return a JSON array with objects:
{{"question": "...", "type": "factual|analytical|comparative|evaluative|exploratory", "priority": 1-4}}

Focus on questions that would produce a comprehensive, well-sourced research report."""

        try:
            response = self.llm_fn(prompt)
            raw = json.loads(response)
            questions = []
            for i, item in enumerate(raw):
                questions.append(ResearchQuestion(
                    id=f"q{i+1}",
                    question=item["question"],
                    question_type=QuestionType(item.get("type", "factual")),
                    priority=Priority(item.get("priority", 3)),
                ))
            return questions
        except Exception as e:
            logger.warning(f"LLM question generation failed: {e}, falling back to heuristic")
            return self._generate_questions_heuristic(topic, num)

    def _generate_sub_questions(self, topic: str, parent_q: str, count: int) -> list[ResearchQuestion]:
        """Generate sub-questions for deeper exploration."""
        templates = [
            (f"What specific evidence supports claims about {topic}?", QuestionType.FACTUAL),
            (f"What are the underlying mechanisms of {topic}?", QuestionType.ANALYTICAL),
            (f"What case studies exist for {topic}?", QuestionType.FACTUAL),
        ]
        return [
            ResearchQuestion(
                id=f"{parent_q[:10]}_sq{i+1}",
                question=q,
                question_type=qt,
                priority=Priority.MEDIUM,
            )
            for i, (q, qt) in enumerate(templates[:count])
        ]

    def _generate_search_queries(self, topic: str, questions: list[ResearchQuestion]) -> list[str]:
        """Generate optimized search queries from questions."""
        queries = [topic]  # broad query first

        for q in questions:
            # Extract key terms from question
            key_terms = self._extract_key_terms(q.question)
            if key_terms:
                queries.append(f"{topic} {key_terms}")

            # Type-specific queries
            if q.question_type == QuestionType.COMPARATIVE:
                queries.append(f"{topic} comparison analysis")
            elif q.question_type == QuestionType.EVALUATIVE:
                queries.append(f"{topic} pros cons review")
            elif q.question_type == QuestionType.EXPLORATORY:
                queries.append(f"{topic} trends future 2025 2026")

        return list(dict.fromkeys(queries))[:10]  # deduplicate, limit

    def _extract_key_terms(self, question: str) -> str:
        """Extract key terms from a question string."""
        # Remove question words
        stop_words = {"what", "how", "why", "when", "where", "who", "which", "is", "are", "the", "a", "an", "of", "to", "in", "for", "and", "or", "does", "do"}
        words = re.findall(r'\b\w+\b', question.lower())
        key = [w for w in words if w not in stop_words and len(w) > 2]
        return " ".join(key[:4])

    def _generate_outline(self, topic: str, questions: list[ResearchQuestion]) -> list[str]:
        """Generate document outline from questions."""
        outline = [f"# {topic}"]

        # Group by question type
        type_headers = {
            QuestionType.FACTUAL: "Background & Key Facts",
            QuestionType.ANALYTICAL: "Analysis & Mechanisms",
            QuestionType.COMPARATIVE: "Comparative Analysis",
            QuestionType.EVALUATIVE: "Evaluation & Critique",
            QuestionType.EXPLORATORY: "Future Directions",
        }

        seen_types = set()
        for q in questions:
            header = type_headers.get(q.question_type, "Additional Research")
            if q.question_type not in seen_types:
                outline.append(f"## {header}")
                seen_types.add(q.question_type)
            outline.append(f"- {q.question}")
            for sq in q.sub_questions:
                outline.append(f"  - {sq.question}")

        outline.append("## Conclusion")
        outline.append("## References")
        return outline
