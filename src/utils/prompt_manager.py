from dataclasses import dataclass
from typing import Dict, Any, Optional
import logging


@dataclass
class PromptTemplate:
    """Template for agent prompts."""
    name: str
    template: str
    variables: list[str]
    description: Optional[str] = None
    
    def format(self, **kwargs) -> str:
        """Format the template with provided variables."""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable: {e}")


class PromptManager:
    """Manages prompt templates for all agents."""
    
    def __init__(self):
        self.logger = logging.getLogger("prompt_manager")
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default prompt templates."""
        
        # Query Handler prompts
        self.register_template(PromptTemplate(
            name="query_classification",
            template="""You are a query classification agent. Analyze the user's request and determine:
1. Primary intent (research, blog, linkedin, image, strategy)
2. Topic/subject matter
3. Any specific requirements

User query: {query}
Previous context: {context}

Respond in JSON format:
{{
    "intent": "primary_intent",
    "topic": "extracted_topic",
    "requirements": ["requirement1", "requirement2"]
}}""",
            variables=["query", "context"],
            description="Classify user queries and extract intent"
        ))
        
        # Research Agent prompts
        self.register_template(PromptTemplate(
            name="research_synthesis",
            template="""You are a research agent. Synthesize the following search results into a comprehensive research report.

Topic: {topic}
Search Results:
{search_results}

Provide:
1. Key findings (3-5 main points)
2. Supporting evidence with sources
3. Relevant statistics and data
4. Credibility assessment of sources

Format as a structured research report.""",
            variables=["topic", "search_results"],
            description="Synthesize research from multiple sources"
        ))
        
        # Blog Writer prompts
        self.register_template(PromptTemplate(
            name="blog_outline",
            template="""Create an SEO-optimized blog outline for the following topic.

Topic: {topic}
Target Keywords: {keywords}
Research: {research}

Provide:
1. Compelling title (with keyword)
2. Meta description (150-160 chars)
3. Section headings (H2, H3)
4. Key points for each section
5. Internal linking suggestions""",
            variables=["topic", "keywords", "research"],
            description="Generate SEO blog outline"
        ))
        
        self.register_template(PromptTemplate(
            name="blog_content",
            template="""Write a comprehensive blog post based on this outline and research.

Outline:
{outline}

Research:
{research}

Requirements:
- Target length: {word_count} words
- Tone: {tone}
- Include {keywords} naturally
- Use engaging storytelling
- Add actionable takeaways

Write the complete blog post in Markdown format.""",
            variables=["outline", "research", "word_count", "tone", "keywords"],
            description="Generate full blog content"
        ))
        
        # LinkedIn Writer prompts
        self.register_template(PromptTemplate(
            name="linkedin_post",
            template="""Create an engaging LinkedIn post about the following topic.

Topic: {topic}
Key Points: {key_points}
Tone: {tone}

Requirements:
- Hook in first line
- Value-driven content
- Professional yet conversational
- Include 3-5 relevant hashtags
- Call-to-action at the end
- 150-300 words

Generate the LinkedIn post.""",
            variables=["topic", "key_points", "tone"],
            description="Generate LinkedIn post"
        ))
        
        # Image Generation prompts
        self.register_template(PromptTemplate(
            name="image_prompt_optimization",
            template="""Optimize this image description for DALL-E 3 generation.

Original description: {description}
Style preference: {style}
Context: {context}

Create an enhanced prompt that:
- Specifies artistic style clearly
- Includes composition details
- Mentions color palette
- Describes mood/atmosphere
- Is concise yet descriptive

Return the optimized prompt only.""",
            variables=["description", "style", "context"],
            description="Optimize DALL-E prompts"
        ))
        
        # Content Strategist prompts
        self.register_template(PromptTemplate(
            name="content_enhancement",
            template="""Review and enhance the following content for quality and impact.

Content Type: {content_type}
Original Content:
{content}

Brand Voice Guidelines: {brand_voice}

Provide:
1. Quality score (1-10)
2. Specific improvements
3. Enhanced version
4. SEO recommendations

Focus on clarity, engagement, and brand alignment.""",
            variables=["content_type", "content", "brand_voice"],
            description="Enhance content quality"
        ))
        
        self.logger.info(f"Loaded {len(self.templates)} default templates")
    
    def register_template(self, template: PromptTemplate) -> None:
        """Register a new prompt template."""
        self.templates[template.name] = template
        self.logger.debug(f"Registered template: {template.name}")
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Retrieve a prompt template by name."""
        return self.templates.get(name)
    
    def format_prompt(self, template_name: str, **kwargs) -> str:
        """Format a prompt template with variables."""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        
        return template.format(**kwargs)
    
    def list_templates(self) -> list[str]:
        """List all available template names."""
        return list(self.templates.keys())
