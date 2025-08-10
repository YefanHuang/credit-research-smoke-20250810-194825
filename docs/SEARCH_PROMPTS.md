# Search Prompts Reference Guide

This document lists all search-related prompts in the codebase for easy maintenance and updates.

## Main Search Prompts

### 1. Unified Model Manager Search Prompt
- **File**: `oop/search_manager.py`
- **Method**: `_create_enhanced_prompt`
- **Purpose**: Main search prompt for credit rating research
- **Usage**: Used by all search operations through the unified model manager
- **Key Components**:
  - Credit rating focus
  - Geographic coverage
  - Authoritative sources
  - Content types
  - Output requirements

### 2. Workflow Search Templates
- **File**: `.github/workflows/unified_search.yml`
- **Parameter**: `search_query_template`
- **Default**: `official research articles about management governance of credit rating systems policies {topic} from national bureaus credit agencies S&P Global TransUnion Equifax authoritative institutions World Bank`
- **Usage**: Used as base template for workflow searches

### 3. Simple Research Workflow
- **File**: `.github/workflows/simple-research.yml`
- **Parameter**: `search_query_template`
- **Default**: Same as unified_search.yml
- **Usage**: Used for simpler, focused searches

## Supporting Search Components

### 1. Search Manager Keywords
- **File**: `oop/search_manager.py`
- **Variables**: 
  - `self.credit_keywords`
  - `self.authoritative_sources`
- **Purpose**: Define focused keywords and sources for credit rating research

### 2. Filter Prompts
- **File**: `api/app/routers/vector.py`
- **Method**: `filter_documents`
- **Purpose**: Filter and rank search results

## Legacy/Backup Prompts (Not Active)

### 1. Enhanced Search Strategies
- **File**: `examples/enhanced_search_strategies.py`
- **Status**: Example code, not actively used
- **Note**: Contains older prompt patterns for reference

### 2. Legacy Workflows
- **Directory**: `legacy_workflows_backup/`
- **Files**:
  - `unified-research-broken.yml`
  - `customizable-research.yml`
- **Status**: Archived, not in use

## How to Update Prompts

1. **Main Search Prompt**:
   - Edit `oop/search_manager.py`
   - Update `_create_enhanced_prompt` method
   - Ensure changes align with credit rating focus

2. **Keywords and Sources**:
   - Edit `credit_keywords` and `authoritative_sources` in `search_manager.py`
   - Focus on credit rating agencies, regulators, and methodologies

3. **Workflow Templates**:
   - Edit `search_query_template` in workflow files
   - Keep templates focused on credit rating research

## Notes

- All prompts should be in English
- Focus on credit rating industry
- Avoid unrelated topics (ESG, Market Motivation, etc.)
- Maintain geographic diversity in sources  
- Prioritize official and authoritative sources through prompt guidance
- Domain filtering removed - use prompt to guide AI toward authoritative sources