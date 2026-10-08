# Dataset Information

## Selected Dataset: Enron Spam Dataset (MWiechmann Preprocessed Corpus)

- **Source URL**: [https://github.com/MWiechmann/enron_spam_data](https://github.com/MWiechmann/enron_spam_data)
- **Direct Download**: `https://raw.githubusercontent.com/MWiechmann/enron_spam_data/master/enron_spam_data.zip`
- **Original Source**: CALO Project / Carnegie Mellon University Enron Email Corpus (FERC investigation public release)
- **License**: GPL-3.0 (curation scripts) / Public Domain (Enron corporate email corpus)
- **Dataset Type**: `email` (Real corporate emails with explicit Subject and Body lines)
- **Language**: English
- **Retrieved Date**: 2026-10-06

## Dataset Specifications

- **Total Records**: 33,716
- **Compressed Size**: ~15.6 MB (`enron_spam_data.zip`)
- **Uncompressed Size**: ~51.7 MB (`enron_spam_data.csv`)
- **Columns**:
  - `Message ID`: Integer identifier (0 - 33715)
  - `Subject`: Email subject line (string, nullable: 289 nulls)
  - `Message`: Email body content (string, nullable: 371 nulls)
  - `Spam/Ham`: Target classification label (`spam` or `ham`)
  - `Date`: Timestamp of email (YYYY-MM-DD)
- **Class Distribution**:
  - `spam`: 17,171 samples (50.93%)
  - `ham`: 16,545 samples (49.07%)

## Download & Setup Instructions

To obtain the dataset manually:
1. Download `enron_spam_data.zip` from `https://raw.githubusercontent.com/MWiechmann/enron_spam_data/master/enron_spam_data.zip`.
2. Extract the file into `data/raw/`.
3. Verify that `data/raw/enron_spam_data.csv` is present.
4. Run the training script:
   ```bash
   python -m src.train
   ```
