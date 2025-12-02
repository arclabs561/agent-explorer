# Weak Points Analysis: Multi-Scale Summarization & Viewing

## Current State

### What Exists

1. **Single Conversation Scales** (`scales` command)
   - Micro: per-turn heads (first 10 turns)
   - Meso: milestones (assistant imperative cues)
   - Macro: topic hint from earliest user message
   - Supports LLM-based summaries (micro/meso/macro)

2. **Recursive Summarization** (`streams-summarize-recursive`)
   - RAPTOR-like hierarchical summarization
   - Level 0: per-stream summaries
   - Levels 1+: recursive summaries of groups
   - Works on streams (user message transitions), not conversations

3. **Cluster Summarization** (`cluster-summarize`)
   - Summarizes cluster tree nodes
   - Provides titles, themes, risks, labels
   - Works on clustered corpus, not individual conversations

### What's Missing

1. **Unified Multi-Scale View**
   - No single command to view: message → conversation → corpus
   - Scales command only shows one conversation
   - No way to see "summary of summaries" across conversations

2. **Integration Gaps**
   - `scales` and `streams-summarize-recursive` are separate
   - No connection between conversation-level and corpus-level summaries
   - Recursive summarization only works on streams, not raw conversations

3. **Navigation Between Scales**
   - Can't easily drill down from corpus summary → conversation → message
   - Can't zoom out from message → conversation → corpus
   - No interactive exploration

4. **Corpus-Level Summarization**
   - No easy way to get "summary of all conversations"
   - No hierarchical view: corpus → conversations → turns
   - Missing RAPTOR-like structure for entire corpus

## Weak Points

### 1. Fragmented Scale Viewing

**Problem**: Users must run multiple separate commands to see different scales:
- `scales` for one conversation
- `streams-summarize-recursive` for streams (different data structure)
- `cluster-summarize` for clusters (requires clustering first)

**Impact**: Hard to understand relationships between scales. Can't see "how does this conversation fit into the corpus?"

### 2. No Recursive Summarization for Conversations

**Problem**: `streams-summarize-recursive` works on user message transitions (streams), not on conversation pairs/turns directly.

**Impact**: Can't apply RAPTOR-like summarization to raw conversations. Must convert to streams first, losing some structure.

### 3. Limited Corpus-Level Abstraction

**Problem**: No easy way to:
- Get a high-level summary of all conversations
- See how conversations relate to each other
- Navigate from corpus → conversation → turn

**Impact**: Hard to understand patterns across conversations. No "big picture" view.

### 4. No Unified Data Model

**Problem**: Different commands expect different data structures:
- `scales`: pairs from one conversation
- `streams-summarize-recursive`: streams JSON
- `cluster-summarize`: cluster tree JSON

**Impact**: Can't easily compose operations. Each scale requires different preprocessing.

## Recommendations

### 1. Unified Multi-Scale Command

Create a `view-scale` command that shows:
- **Level 0 (Message)**: Single turn/pair
- **Level 1 (Conversation)**: Summary of one conversation
- **Level 2 (Corpus)**: Summary of all conversations
- **Level 3+ (Recursive)**: Summary of summaries

### 2. Recursive Summarization for Conversations

Extend recursive summarization to work directly on:
- Conversation pairs (not just streams)
- Multiple conversations (corpus-level)
- Hierarchical structure: corpus → conversations → turns

### 3. Integrated Navigation

Enable drilling down/zooming out:
- Start at corpus level → select conversation → view turns
- Start at turn level → see conversation context → see corpus context

### 4. Unified Data Model

Create a consistent structure that supports:
- Single conversation (pairs)
- Multiple conversations (index JSONL)
- Hierarchical summaries (recursive structure)

## Implementation Priority

1. **High**: Unified multi-scale viewing command
2. **High**: Recursive summarization for conversations (not just streams)
3. **Medium**: Corpus-level summarization
4. **Medium**: Navigation between scales
5. **Low**: Interactive exploration (TUI)

