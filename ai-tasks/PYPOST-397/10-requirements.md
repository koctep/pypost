# PYPOST-397: Close debt — QSyntaxHighlighter block-by-block performance

## Goals

JsonHighlighter runs `highlightBlock` per QTextDocument block. Assess whether this causes
unacceptable performance on large documents.

## Definition of Done

1. Block-by-block model confirmed acceptable for typical response/body sizes.
2. No change required; debt closed as accepted Qt pattern.

## Task Description

Accepted-debt closure. Standard QSyntaxHighlighter behavior; no perf issue observed.
