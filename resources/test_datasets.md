# Test datasets

## Test text data

The test data added in this repo is part of the Kaggle dataset 
[CNN DailyMail News Text Summerization](https://www.kaggle.com/datasets/gowrishankarp/newspaper-text-summarization-cnn-dailymail?resource=download).

The numbers in the file names indicate a text ID, where the same numbers contain the same texts.
The following manipulations were done:

| File name                              | Manipulation                                                                                                                                                                    |
|----------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------| 
| 1_odt.txt                              | Full text, saved as odt, transformed to .txt                                                                                                                                    |
| 1_pdf.txt                              | Full text, saved as pdf, transformed to .txt                                                                                                                                    |
| 1_txt.txt                              | Full text, saved as .txt                                                                                                                                                        |
| 2_fulltext_odt.txt                     | Full text, saved as odt, transformed to .txt                                                                                                                                    |
| 2_partialtext_odt.txt                  | Part of the full text from 2_fulltext_odt.txt, saved as odt, transformed to .txt                                                                                                |
| 2_partialtext_pdf.txt                  | Part of the full text from 2_fulltext_odt.txt, saved as pdf, transformed to .txt                                                                                                |
| 3_fulltext_odt.txt                     | Full text, saved as odt, transformed to .txt                                                                                                                                    |
| 3_fulltext_changed_dots_odt.txt        | Full text from 3_fulltext_odt.txt, but all dots changed to any of the following: [!?,;/\s], <br/>saved as odt, transformed to .txt                                              |
| 4_fulltext_odt.txt                     | Full text, saved as odt, transformed to .txt                                                                                                                                    |
| 4_fulltext_within_other_texts_odt.txt  | Full text from 4_fulltext_odt.txt, but surrounded by two other bodies of texts, <br/>saved as odt, transformed to .txt                                                          |
| 5_fulltext_odt.txt                     | Full text, saved as odt, transformed to .txt                                                                                                                                    |
| 5_fulltext_different_format_odt.txt    | Full text from 5_fulltext_odt.txt, but with different formatting (i.e. more whitespaces and enters and an inserted list of bullet points <br/>saved as odt, transformed to .txt |
| 5_fulltext_different_format_pdf.txt    | Full text from 5_fulltext_odt.txt, but with different formatting (i.e. more whitespaces and enters and an inserted list of bullet points <br/>saved as pdf, transformed to .txt |
| 5_fulltext_odt_fake_ocr_errors.txt     | Full text from 5_fulltext_odt.txt, but with fake OCR errors (i.e. replacing l with 1, S with $, etc)                                                                            |


## News edit data

The news edits dataset is obtained from [this link](https://github.com/isi-nlp/NewsEdits) and belongs to the following
article: 
[NewsEdits: A News Article Revision Dataset and a Novel Document-Level Reasoning Challenge](https://aclanthology.org/2022.naacl-main.10) (Spangher et al., NAACL 2022)

This dataset gave us multiple versions of the same text with minor changes, which made it useful for near-duplicate
detection.

We used the following databases from the dataset and combined them using the script 
`resources/news_edits_data/create_news_edits.db`:  
ap.db, canadaland.db, fox.db, nationalpost.db, therebel.db, bbc.db, cbc.db, globemail.db, reuters.db, torontostar.db, 
calgaryherald.db, dailymail.dd, lapresse.db, telegraph.db, torontosun.db