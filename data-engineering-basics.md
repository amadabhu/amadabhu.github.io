# The Basics of Data Engineering

### [Menu](./sitemap.md)

This is a high level primer, only designed to serve as brief introduction. All of the utilities in this section of my website will help build solutions for the answers to the above questions.

# [Toolbox](https://github.com/amadabhu/Snowflake-Lakehouse-Utilities/tree/main)

This toolbox repo can be used as reusable utility functions.

## Input
Inputs are your source information. This is what's sometimes referred to as "raw data". There's several approaches to the input side, a few examples are below:

- web scraping
- REST API
- TCP/IP connection
- direct file upload (.csv,.json.,.parquet etc)
- sensors 

## Process

This is the meat of the engineering where you need to answer several questions. Some examples are below. These are all context dependent and vary significantly. 

- What needs to happen to the data?
- What frequency does it need to be updated?
- What frequency does it need to be deleted?
- Which category of machine learning does the data fall into?
- Do we have enough data to do meaningful machine learning?
- Do we need to compress the data?
- Are we applying any filters to the data?
- Is there an existing index that we need to join the data into?


## Output

This is the final result, and it answers where the output of all the hardwork lives. This varies by use case, so there's a subset of examples below:

- database (RDS, Postgres, MySQL, etc)
- blob storage (s3, azure blob, google blob)
- local user machine
- data visualization
- website
- back to another REST API






