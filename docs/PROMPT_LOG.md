# Prompt Log for Credit Monitor System

This document serves as a central log for all prompts used within the Credit Monitor system, specifically for interactions with Qwen and Perplexity models. All prompts are designed to be in English, with explicit instructions for English output to ensure consistency in research and analysis.

---

## 1. `oop/search_manager.py`

### Function: `_create_enhanced_prompt(self, topic: str)`

This prompt is used to generate an enhanced search query for the Perplexity model, focusing on comprehensive credit industry research.

```
Search for the latest credit industry research and analysis on "{topic}", with the following requirements:

📊 Content Type:
- Credit industry research reports and whitepapers
- Technology innovation and application case studies
- Regulatory policy interpretations and compliance guidance
- Market trends and data insights
- Empirical research and quantitative analysis

🏛️ Prioritize Authoritative Sources:
- Regulatory bodies: {', '.join(self.authoritative_sources[:4])}
- Academic institutions: {', '.join(self.authoritative_sources[4:8])}
- Consulting firms: {', '.join(self.authoritative_sources[8:13])}
- Technology companies: {', '.join(self.authoritative_sources[13:])}

🔍 Keyword Enhancement:
{f"Prioritize content containing the following relevant terms: {', '.join(relevant_keywords)}" if relevant_keywords else ""}

🎯 Key Focus:
- Data-driven analysis and empirical research
- Technical implementation details and architectural design
- Policy impact and industry development trends
- Risk management and model innovation
- Actionable recommendations and best practices

📋 Output Requirements:
- Provide detailed content summaries and key findings
- Include original source links and publication dates
- Evaluate content authority and credibility
- Highlight technological innovations and practical applications
- Ensure output is in English.
```

---

## 2. `examples/enhanced_search_strategies.py`

### Function: `create_domain_specific_prompt(self, topic: str, search_depth: str)`

This function creates a domain-specific search prompt with varying levels of detail based on `search_depth`. The combined prompt structure is shown below.

```
Search for the latest credit industry research and analysis on "{topic}", with the following requirements:

📊 Content Type and Quality Requirements:
- Industry news and policy interpretations
- Introduction to basic concepts and application cases
- Market dynamics and development trends
- In-depth research reports and whitepapers
- Technology innovation and application case studies
- Regulatory policy interpretations and compliance guidance
- Market trends and data insights
- Empirical research and quantitative analysis
- Academic papers and frontier research
- Technical architecture and algorithm innovation
- Regulatory framework and policy impact analysis
- Risk models and quantitative strategies
- Industry standards and best practices
- International comparison and trend prediction

🏛️ Prioritize Authoritative Sources (by weight):
- Regulatory bodies: {', '.join(self.authoritative_sources[:4])}
- Academic institutions: {', '.join(self.authoritative_sources[4:8])}
- Consulting firms: {', '.join(self.authoritative_sources[8:13])}
- Technology companies: {', '.join(self.authoritative_sources[13:])}

🔍 Keyword Enhanced Search:
Prioritize content containing the following relevant terms: {', '.join(relevant_keywords)}

🎯 Content Quality Standards:
- Data-driven analysis and empirical research
- Specific case studies and application scenarios
- Technical implementation details and architectural design
- Policy impact and industry development trends
- Risk management and model innovation
- Actionable recommendations and best practices

📋 Output Format Requirements:
- Provide detailed content summaries
- Highlight key findings and conclusions
- Include original source links and publication dates
- Evaluate content authority and credibility
- Ensure output is in English.
```

### Function: `create_multi_angle_search_strategy(self, topic: str)`

This function generates multiple prompts, each focusing on a different perspective of the search topic.

#### Prompt: Policy and Regulatory Perspective

```
Search for "{topic}" related content from a regulatory policy perspective:
- Latest regulatory policies and changes
- Compliance requirements and implementation guidelines
- Official documents and interpretations from regulatory bodies
- Industry standards and specifications
Focus on content published by authoritative institutions such as central banks and banking and insurance regulatory commissions.
Ensure output is in English.
```

#### Prompt: Technological Innovation Perspective

```
Search for "{topic}" related content from a technological innovation perspective:
- Latest technological advancements and breakthroughs
- Application cases of new technologies (e.g., AI, blockchain in credit)
- Technical architecture and algorithm design
- Data security and privacy protection technologies
Focus on content detailing technical implementation and practical applications.
Ensure output is in English.
```

#### Prompt: Market and Risk Management Perspective

```
Search for "{topic}" related content from a market and risk management perspective:
- Market trends and competitive landscape analysis
- Risk assessment models and strategies
- Impact of economic cycles on the credit industry
- Case studies of risk events and their handling
Focus on data-driven analysis and practical risk management solutions.
Ensure output is in English.
```

#### Prompt: International Comparison Perspective

```
Search for "{topic}" related content from an international comparison perspective:
- Cross-country credit market dynamics and differences
- International regulatory standards and best practices
- Global credit technology trends and adoption
- Analysis of major international credit institutions
Focus on comparative studies and global insights.
Ensure output is in English.
```

---

## 3. `tests/enhanced_api_architecture.py`

### Function: `create_time_filtered_query(self, topic: str, time_range: str)`

This prompt is used to create a time-filtered search query for the Perplexity model.

```
Search for the latest credit industry research articles on "{topic}", with the following requirements:

1. Content Type: Credit industry research reports, analysis articles, policy interpretations
2. Authoritative Sources: Content published by financial institutions, research institutes, regulatory bodies
3. Depth Requirement: In-depth content including data analysis, case studies, or policy interpretations
4. Exclude Content: News alerts, promotional articles, non-professional content

Please sort by relevance and authority, provide detailed content summaries and original source links.
Key Focus:
- Industry trend analysis
- Technological innovation applications
- Regulatory policy impact
- Market data insights
Ensure output is in English.
```

---

## 4. `oop/search_result_processor.py`

### Function: `intelligent_summarization(self, content: str, max_length: int = 300, topic: str = "")`

This prompt is used to summarize text content using the LLM (Qwen) model. The prompt ensures that the summary is precise and maintains key information, explicitly requesting English output.

```
Please summarize the following {topic_context} content into a precise summary of no more than {max_length} characters:

{clean_content}

Summary requirements:
1. Retain core data and key conclusions
2. Highlight credit industry characteristics and professional terminology
3. Maintain clear logical structure
4. Keep character count under {max_length}
5. Concise language but high information density

Please return the summary directly without additional explanation. Ensure output is in English.
```

---

## 5. GitHub Workflow Files

### `.github/workflows/unified-research.yml`

#### Function: `filter_prompt` in embedded Python script

This prompt is used for filtering and processing research content using the LLM (Qwen) model.

```
Please analyze the following credit industry research content and filter based on these criteria:

1. Content Quality:
   - Must contain substantive analysis or insights
   - Include data, statistics, or concrete examples
   - Professional and authoritative tone

2. Topic Relevance:
   - Focus on credit industry trends and developments
   - Cover technological innovation or regulatory changes
   - Address market dynamics or risk management

3. Information Value:
   - Provide actionable insights or recommendations
   - Include specific implementation details or case studies
   - Offer unique perspectives or expert analysis

4. Exclude:
   - Generic news or surface-level reporting
   - Marketing or promotional content
   - Outdated or irrelevant information

Please return a boolean (True/False) indicating if the content meets these criteria.
Ensure output is in English.
```

### `legacy_workflows_backup/customizable-research.yml`

#### Functions: `create_custom_search_prompt` and `generate_email_content`

The workflow contains customizable prompts for search and email content generation, with default keywords and templates in English.

```python
default_keywords = [
    "credit risk assessment",
    "credit scoring models",
    "regulatory compliance",
    "credit data analysis",
    "credit technology innovation"
]

email_template = """
Credit Industry Research Update

Key Findings:
{key_findings}

Market Trends:
{market_trends}

Technology Updates:
{tech_updates}

Regulatory Changes:
{regulatory_changes}

For detailed information, please refer to the attached report.
"""
```

### `legacy_workflows_backup/chromadb-hybrid-pipeline.yml` and `chromadb-hybrid-pipeline-v2.yml`

#### Function: `intelligent_segmentation`

This prompt is used for intelligent text segmentation in the ChromaDB training pipeline.

```
Please analyze and segment the following credit industry research content:

Requirements:
1. Maintain logical coherence within segments
2. Identify natural topic boundaries
3. Preserve key information and context
4. Ensure segments are self-contained
5. Keep segment length between 200-500 characters

Segmentation criteria:
- Topic transitions
- Argument structure
- Information density
- Contextual relationships

Please return segments as a list, with each segment preserving complete sentences.
Ensure output is in English.
```

### Additional Workflow Files

The following workflow files have been updated to use English for all descriptions, print statements, and mock data:

- `test-connection.yml`
- `research-api.yml`
- `smart-chromadb-training.yml`
- `enhanced-research.yml`
- `simple-research-broken.yml`
- `self-hosted-api.yml`
- `ci.yml`

Key changes include:
- Translation of all hardcoded strings to English
- Adjustment of token estimation ratios for English text (from `// 3` to `// 4`)
- Addition of "Ensure output is in English" to all prompts
- Standardization of file names and documentation in English
```

## 6. `examples/perplexity_api_integration.py`

### System Prompt for Financial Research Assistant

This prompt defines the role and focus of the Perplexity API when conducting credit research.

```
You are a professional financial research assistant specializing in credit research and risk management. 
Provide accurate, up-to-date information about credit industry developments, regulatory changes, and technological innovations.
Focus on authoritative sources like central banks, financial institutions, and academic research.
```

### Search Query Prompt

This prompt is used to generate search queries for credit industry research.

```
Search for the latest credit industry research and analysis on "{topic}", with the following requirements:

📊 Content Type:
- Credit industry research reports and whitepapers
- Technology innovation and application case studies
- Regulatory policy interpretations and compliance guidance
- Market trends and data insights

🏛️ Prioritize Authoritative Sources:
- Central banks and regulatory bodies
- Major bank and financial institution research departments
- Leading credit companies
- Authoritative fintech research institutions

🎯 Key Focus:
- Data-driven analysis and empirical research
- Technical implementation details and architectural design
- Policy impact and industry development trends
- Risk management and model innovation

Please provide detailed content summaries, key findings, and original source links.
Ensure output is in English.
```

## 7. `oop/unified_chromadb_trainer.py`

### Intelligent Segmentation Prompt

This prompt is used for intelligent text segmentation in the ChromaDB training pipeline.

```
Please analyze and segment the following credit industry research content:

Requirements:
1. Maintain logical coherence within segments
2. Identify natural topic boundaries
3. Preserve key information and context
4. Ensure segments are self-contained
5. Keep segment length between 200-500 characters

Segmentation criteria:
- Topic transitions
- Argument structure
- Information density
- Contextual relationships

Please return segments as a list, with each segment preserving complete sentences.
Ensure output is in English.
```

## 8. Summary of Prompt Types and Locations

### Model Interaction Prompts
1. **Qwen LLM Prompts**
   - Summarization (`oop/search_result_processor.py`)
   - Filtering (`unified-research.yml`)
   - Segmentation (`unified_chromadb_trainer.py`)

2. **Perplexity Search Prompts**
   - Basic Search (`oop/search_manager.py`)
   - Enhanced Search (`examples/enhanced_search_strategies.py`)
   - Time-filtered Search (`tests/enhanced_api_architecture.py`)
   - API Integration (`examples/perplexity_api_integration.py`)

### Workflow Prompts
1. **GitHub Actions**
   - Research Workflows
   - Training Workflows
   - Testing Workflows

### Template Prompts
1. **Email Templates**
   - Research Updates
   - System Notifications

2. **Search Templates**
   - Basic Search
   - Domain-specific Search
   - Multi-angle Search

### Configuration Prompts
1. **Default Settings**
   - Keywords
   - Source Priorities
   - Quality Criteria

All prompts have been standardized to:
1. Use English exclusively
2. Include explicit instructions for English output
3. Maintain consistent formatting and structure
4. Focus on credit industry specifics
5. Prioritize authoritative sources
```

## 9. Search and Model Interaction Prompts

### A. Perplexity Search Prompts

#### 1. Basic Search (`scripts/search_perplexity.py`)
```
System: "You are a research assistant specialized in credit reporting and financial regulation. Please search for recent information about the given topic and return detailed results."

User: "Search for recent information about: {topic}. Please provide detailed content including source URLs and publication dates if available."
```

#### 2. Official API Example (`examples/perplexity_official_example.py`)
```
System: "You are a helpful assistant that provides accurate and up-to-date information about credit research and financial industry."

User: """
Search for the latest credit industry research on "{topic}", with the following requirements:

📊 Content Type:
- Credit industry research reports and whitepapers
- Technology innovation and case studies
- Regulatory policy analysis
- Market trends and data insights

🏛️ Prioritize Authoritative Sources:
- Central banks and regulatory bodies
- Major banks and financial institutions
- Leading credit reporting companies
- Authoritative research institutions

Please provide detailed summaries and original source links.
Ensure output is in English.
"""
```

#### 3. Enhanced Time-Filtered Search (`tests/enhanced_api_architecture.py`)
```
Search for the latest credit industry research articles on "{topic}", with the following requirements:

1. Content Type: Credit industry research reports, analysis articles, policy interpretations
2. Authoritative Sources: Content published by financial institutions, research institutes, regulatory bodies
3. Depth Requirement: In-depth content including data analysis, case studies, or policy interpretations
4. Exclude Content: News alerts, promotional articles, non-professional content

Please sort by relevance and authority, provide detailed content summaries and original source links.
Key Focus:
- Industry trend analysis
- Technological innovation applications
- Regulatory policy impact
- Market data insights
Ensure output is in English.
```

### B. Search Templates

#### 1. Basic Search Templates
```
Base template: "{topic} latest research credit reporting financial services"
Usage: Main Perplexity search query
Location: Workflows, API routes
```

#### 2. Domain-Specific Templates
```
Banking: "{institution} credit rating research"
Regulatory: "{organization} credit regulation development"
Technology: "credit {technology} implementation"
Market: "{market_segment} credit system construction"
```

#### 3. Result Display Templates
```
Title template: "Credit {category} - {topic}"
Content template: "Latest {analysis_type} on {topic}, including {aspects}."
```

### C. LLM Interaction Prompts

#### 1. Text Segmentation (`oop/unified_chromadb_trainer.py`)
```
Please intelligently segment the following text into semantically complete paragraphs, with each segment not exceeding {max_chunk_size} characters:

{text[:2000]}  # limit input length

Requirements:
1. Maintain semantic integrity and coherence
2. Keep each segment under {max_chunk_size} characters
3. Remove reference numbers at the end of sentences or paragraphs (e.g., remove "1" from "investors.1" or "2" from "risk.2")
4. Clean up text transitions (e.g., "investors.1In this paper" should become "investors. In this paper")
5. Return format: one segment per line, separated by "---"

Ensure output is in English.
```

#### 2. Content Summarization (`oop/search_result_processor.py`)
```
Please summarize the following {topic_context} content into a precise summary of no more than {max_length} characters:

{clean_content}

Summary requirements:
1. Retain core data and key conclusions
2. Highlight credit industry characteristics and professional terminology
3. Maintain clear logical structure
4. Keep character count under {max_length}
5. Concise language but high information density

Please return the summary directly without additional explanation. Ensure output is in English.
```

### D. Workflow Prompts

#### 1. ChromaDB Training Pipeline (`legacy_workflows_backup/chromadb-hybrid-pipeline.yml`)
```
Please intelligently segment the following text from the {domain} domain, with each segment not exceeding {max_chunk_size} characters:

{text[:2000]}...

Requirements:
1. Maintain semantic integrity and coherence
2. Keep each segment under {max_chunk_size} characters
3. Remove reference numbers at the end of sentences or paragraphs (e.g., remove "1" from "investors.1" or "2" from "risk.2")
4. Clean up text transitions (e.g., "investors.1In this paper" should become "investors. In this paper")
5. Return in JSON format: {"chunks": ["paragraph1", "paragraph2", ...]}

Ensure output is in English.
```

### E. Common Requirements Across All Prompts

1. Language Requirements:
   - All prompts are in English
   - Explicit instruction to ensure English output
   - Consistent professional terminology

2. Quality Standards:
   - Focus on authoritative sources
   - Maintain semantic integrity
   - Preserve technical accuracy
   - Remove reference numbers and clean transitions

3. Output Format:
   - Clear structure
   - Consistent formatting
   - Proper segmentation
   - JSON format where required

4. Content Focus:
   - Credit industry research
   - Financial regulations
   - Market analysis
   - Technical innovations

### F. API Router Prompts

#### 1. Document Filtering (`api/app/routers/vector.py`)
```
Please select the {selection_count} most relevant documents from the following list:

Selection criteria: {criteria}

Document list:
{documents_text}

Please return the selected document numbers (comma-separated), e.g.: 1,3,5
```

#### 2. Search Query Construction (`api/app/routers/search.py`)
```
System: "You are a helpful assistant that provides accurate and up-to-date information about credit research and financial industry."

Query: "credit research latest developments on {topic}"

Search Parameters:
- Domain filters: reuters.com, bloomberg.com, ft.com, wsj.com, economist.com, wikipedia.org
- Context size: medium
- Return related questions: true
```
```