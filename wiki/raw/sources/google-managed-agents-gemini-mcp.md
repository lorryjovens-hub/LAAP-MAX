---
title: "Expanding Managed Agents in Gemini API: Background Tasks, Remote MCP and More"
source_url: "https://blog.google/innovation-and-ai/technology/developers-tools/expanding-managed-agents-gemini-api/"
ingested: "2026-07-19"
source_type: blog
intel_score:
  quality: 7.5
  safety: 6.5
  innovation: 7.5
  efficiency: 7.0
  overall: 7.1
tags: [google-ai, agents, mcp, gemini-api, managed-agents]
---

# Expanding Managed Agents in Gemini API: Background Tasks, Remote MCP and More

**Source**: Google AI Blog
**Date**: 2026-07-07
**Author**: Philipp Schmid

## Summary

Google announced new capabilities for Managed Agents in Gemini API: background execution for async interactions, easy connection to remote MCP servers, custom function calling, and credential refresh across interactions.

### Key Features

1. **Background Execution**: Long-running tasks no longer require holding HTTP connections open
2. **Remote MCP Integration**: Easy connection to remote MCP (Model Context Protocol) servers
3. **Custom Function Calling**: Developers can define custom functions
4. **Credential Refresh**: Credential management across interactions

### Technical Details

Managed Agents in Gemini Interactions API allows calling a single endpoint, and Gemini handles reasoning, code execution, package installation, file management and web information inside an isolated cloud sandbox.

## LAAP Relevance

This is highly relevant to LAAP's architecture. Key parallels:
- **MCP Integration**: LAAP's CognitiveBus uses a similar protocol pattern. Google's MCP support validates our architectural direction.
- **Background Tasks**: LAAP's PSI scheduler already supports background execution; seeing Google adopt this confirms the pattern.
- **Managed Sandbox**: Similar to LAAP's isolated execution environments.

## Tags

- google-ai, agents, mcp, gemini-api, managed-agents, background-execution, sandbox
