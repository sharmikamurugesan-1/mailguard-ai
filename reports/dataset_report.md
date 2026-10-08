# Dataset Discovery & Validation Report

## Overview
- **Dataset Name**: Enron Spam Dataset
- **Source URL**: [https://github.com/MWiechmann/enron_spam_data](https://github.com/MWiechmann/enron_spam_data)
- **License**: GPL-3.0 / Public Domain (CALO Enron Corpus)
- **Dataset Type**: `email` (real emails with separate subject and body)
- **Retrieved Date**: 2026-10-06
- **Combination Format**: `Subject: {clean_subject}\n\n{clean_body}`

## Cleaning Audit & Sample Counts
- **Initial Raw Rows**: 33,716
- **Both Null Dropped**: 51
- **Duplicates Removed**: 3,203
- **Cleaned Total Samples (`n_samples`)**: 30,462

## Class Distribution
- **Ham (legitimate)**: 15,910 (52.23%)
- **Spam**: 14,552 (47.77%)

## Text Characteristics
- **Average Character Length**: 1487.39 chars
- **Average Token Count**: 223.38 tokens

## Sample Records (First 5)
| Index | Label | Subject Snippet | Body Snippet |
|---|---|---|---|
| 0 | `ham` | christmas tree farm pictures |  |
| 1 | `ham` | vastar resources , inc . | gary , production from the high island larger block a - 1 # |
| 2 | `ham` | calpine daily gas nomination | - calpine daily gas nomination 1 . doc |
| 3 | `ham` | re : issue | fyi - see note below - already done . stella - - - - - - - - |
| 4 | `ham` | meter 7268 nov allocation | fyi . - - - - - - - - - - - - - - - - - - - - - - forwarded |


## Verification Status
- Validated column integrity: `['Subject', 'Message', 'Spam/Ham']` present.
- Label mapping confirmed: only `spam` and `ham` classes exist.
- De-duplication complete: exact duplicate texts removed to avoid leakage.
